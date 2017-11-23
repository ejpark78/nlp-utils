#!/usr/bin/python3
# -*- coding: utf-8 -*-

# from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import pymongo

from os import getcwd
from time import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

# sys.path.append('{}'.format(getcwd()))
# sys.path.append('{}/nlp_util'.format(getcwd()))


class NCNlpUtil:
    def __init__(self):
        self.pos_tagger = None
        self.ne_tagger = None
        self.sp_project_ne_tagger = None

        self.count = None
        self.start_time = None

        self.domain = None

        self.multi_domain_ner = {}

    def open_multi_domain_ner(self, config='sp_config.ini'):
        """
        개체명 인식기 핸들 오픈
        
        # domain( "B"=야구 "E"=경제 "T"=야구 용어 )
        """
        from NCSPProject import NCSPProject

        domain_list = {
            'B': 'baseball',
            'E': 'economy',
            'T': 'baseball terms'
        }

        for d in domain_list:
            self.multi_domain_ner[domain_list[d]] = NCSPProject()
            self.multi_domain_ner[domain_list[d]].open(config, d)

        return

    def open_sp_project_ner(self, config='sp_config.ini', domain='B'):
        """
        개체명 인식기 핸들 오픈

        # domain( "B"=야구 "E"=경제 "T"=야구 용어 )
        """
        from NCSPProject import NCSPProject

        self.sp_project_ne_tagger = NCSPProject()
        self.sp_project_ne_tagger.open(config, domain)

        return

    def open_ner(self, model_file='dictionary/ner.josa.model'):
        """
        학습 기반 개체명 인식기 핸들 오픈
        """
        from NCNamedEntityTagger import NCNamedEntityTagger

        self.ne_tagger = NCNamedEntityTagger()
        self.ne_tagger.open(model_file)

        return

    def open_pos_tagger(self, dictionary_path='dictionary/rsc'):
        """
        형태소 분석기 핸들 오픈
        """
        from NCKmat import NCKmat

        if self.pos_tagger is None:
            self.pos_tagger = NCKmat()

            self.pos_tagger.verbose = True
            self.pos_tagger.open(dictionary_path)

        return self.pos_tagger

    def split_document(self, document):
        """
        문서를 입력받아 문장 분리후 문단 단위로 반환
        """
        sentence_count = 0

        split_result = []
        for paragraph in document.split('\n'):
            sentence_list = self.split_sentence(paragraph)

            if len(sentence_list) > 0:
                sentence_count += len(sentence_list)
                split_result.append(sentence_list)

        return split_result, sentence_count

    @staticmethod
    def get_qoute_count(sentence):
        """
        qoute 개수 반환            
        """
        count = 0
        position = sentence.find('"')
        while position >= 0:
            count += 1
            sentence = sentence[position+1:]
            position = sentence.find('"')

        return count

    def split_sentence(self, paragraph):
        """
        문장 분리
        """
        paragraph = paragraph.strip()

        paragraph = re.sub(r'\r', '', paragraph, flags=re.MULTILINE)

        paragraph = re.sub(r'\n+', '\n', paragraph, flags=re.MULTILINE)

        paragraph = re.sub(r'[↓↑←→]', '', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'[．]', '.', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'[“”]', '"', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'[‘’]', '\'', paragraph, flags=re.MULTILINE)

        paragraph = re.sub(r'(https?://.*?)(\s|\n)', '\n\g<1>\n', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'([.?!]+)', '\g<1>\n', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'(\[]+)', '\n\g<1>', paragraph, flags=re.MULTILINE)

        # attach text
        paragraph = re.sub(r'(\d+\.)\n+(\s*\d+\.)\n+(\s*\d+\.)', '\g<1>\g<2>\g<3>', paragraph, flags=re.MULTILINE)

        # 소숫점 처리
        paragraph = re.sub(r'(\d+\.)\n+(\d+)', '\g<1>\g<2>', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'(\(.+?)\n+(.+?\))', '\g<1>\g<2>', paragraph, flags=re.MULTILINE)

        paragraph = re.sub(r'([0-9a-zA-Z]\.)\n+([0-9a-zA-Z])', '\g<1>\g<2>', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'([.?!\]])\n+([\'\"])([,])', '\g<1>\g<2>\g<3>', paragraph, flags=re.MULTILINE)
        paragraph = re.sub(r'([.?!\]])\n+([\'\"])', '\g<1>\g<2>\n', paragraph, flags=re.MULTILINE)

        paragraph = re.sub(r'\n+([?.!]}\)])', '\g<1>', paragraph, flags=re.MULTILINE)

        # 숫자 복원
        paragraph = re.sub(r'(/[0-9.]+/)', r'\g<1>\n', paragraph, flags=re.MULTILINE)

        paragraph = paragraph.strip()

        sentence_list = []

        # 인용구 복원
        for single_sentence in paragraph.split('\n'):
            single_sentence = single_sentence.strip()
            if single_sentence == '':
                continue

            # 첫번째 문장
            if len(sentence_list) == 0:
                sentence_list.append(single_sentence)
                continue

            # 이전 문장의 qoute 개수
            count = self.get_qoute_count(sentence_list[len(sentence_list) - 1])
            if count % 2 == 1:
                # 홀수라면 합침
                sentence_list[len(sentence_list) - 1] += ' ' + single_sentence
            else:
                # 짝수거나 0 이라면 추가
                sentence_list.append(single_sentence)

        result = []
        for single_sentence in sentence_list:
            single_sentence = self.remove_stop_phrase(single_sentence)
            single_sentence = single_sentence.strip()

            if single_sentence != '':
                result.append(single_sentence)

        return result

    def remove_stop_phrase(self, sentence):
        """
        문장에서 필오 없는 구문을 제거
        """

        sentence, _ = self.remove_header(sentence)
        sentence, _ = self.remove_tail(sentence)

        if len(sentence) < 60:
            if sentence.find('기자') >= 0 or sentence.find('@') >= 0:
                return ''

        return sentence

    @staticmethod
    def remove_header(content_text):
        """
        본문에서 머릿말 분리

        머릿말 패턴:
            (서울=연합뉴스) 임헌정 기자 = 삼성 라이온즈 선수들이 20일 서울 잠실야구장에서 열린 2016
            [마이데일리 = 대전 유진형 기자] 한화 권혁이 20일 오후 대전광역시 한화생명 이글스파크에
            [OSEN=부산, 이동해 기자] 20일 부산광역시 사직야구장에서 '2016 타이어뱅크 KBO 리그'
            【서울=뉴시스】 장세영 기자 =  20일 오후 서울 구로구 경인로 고척 스카이돔구
        """
        content = content_text.strip()

        if content == '':
            return '', ''

        content = re.sub(r'^(【.+?】.*?=?)', r'\g<1>__SPLIT__', content, count=1)

        if content.find('__SPLIT__') >= 0:
            token = content.split('__SPLIT__')
            content = ''.join(token[1:])

        content = re.sub(r'^((대구|부산|사직|잠실|목동)?.{0,20}기자.{0,10}[=|\]])',
                         r'\g<1>__SPLIT__', content, count=1)
        
        #if content.find('__SPLIT__') <= 0:
        #    content = re.sub(r'^(\([^)]+?\).{0,10}(기자)=?)', r'\g<1>__SPLIT__', content, count=1)

        if content.find('__SPLIT__') <= 0:
            content = re.sub(r'^(\([^)]+?\).*?=?)', r'\g<1>__SPLIT__', content, count=1)

        if content.find('__SPLIT__') <= 0:
            content = re.sub(r'^(\[[^]]+?\].*?=?)', r'\g<1>__SPLIT__', content, count=1)

        if content.find('__SPLIT__') == 0:
            content = content.replace('__SPLIT__', '')

        if content.find('__SPLIT__') < 0:
            return content, ''

        token = content.split('__SPLIT__')
        head_line = token[0].strip()

        header = ''
        if head_line != '' and len(head_line) < 100:
            header = head_line
            content = '\n'.join(token[1:])

        content = content.replace('__SPLIT__', '')

        return content.strip(), header

    @staticmethod
    def remove_tail(content_text):
        """
        본문에서 꼬리말 분리

        꼬리말 패턴:
            "writer": "1회초 무사에서 두산 선발투수 보우덴이 힘차게 공을 던지고 있다. /sunday@osen.co.kr"
            "writer": "[OSEN=고척, 고유라 기자] 넥센 히어로즈가 공격 중심의 선발 라인업을 발표했다.

            되겠다\"고 소감을 전했다.\n\n잠실=함태수 기자 hamts7@sportschosun.com\n\n
            을 받게 됐다.\n\n최형창 기자 calling@segye.com\n\n사진/연합뉴스",

            되도록 하겠다\"고 말했다.(사진=발디리스/삼성 라이온즈 제공)",
            반드시 이길 수 있도록 더 노력하겠다\"라고 말했다.  \n\n[차우찬. 사진 = 마이데일리 사진 DB]",

            6회말 2사 만루 때 삼진아웃을 당하며 안타까와하고 있다.  (조남수 기자/news@isportskorea.com)",
            달아나야 한다\"고 말했다. 대전=박재호 기자 jhpark@sportschosun.com
            피오리아(미국 애리조나주)=글, 박선양 특파원 sun@ 사진, 손용호 기자 spjj@poctannews.com

            대구=정재근 기자
            대구=정재근 기자
            목동=정재근 기자 cjg@sportschosun.com/2012.04.18/
            부산 | 이주상기자.rainbow@sportsseoul.com
            부산 | 이주상기자.rainbow@sportsseoul.com
            부산 | 이주상기자.rainbow@sportsseoul.com
            부산=김경민 기자 kyungmin@sportschosun.com
            부산=류동혁 기자 sfryu@sportschosun.com
            사직 | 이주상기자.rainbow@sportsseoul.com
            사직 | 이주상기자.rainbow@sportsseoul.com
            잠실=조병관 기자 rainmaker@sportschosun.com

        TODO:
            꼬리말의 패턴으로 전처리
            http://sports.news.nate.com/view/20050303n02582?mid=s0101
        """
        content = content_text.strip()

        content = re.sub(r'\(([^)]{0,50})\)$', r'__SPLIT__\g<1>', content, count=1)

        if content.find('__SPLIT__') >= 0:
            token = content.split('__SPLIT__')
            content = ''.join(token[0:-1])
    
        content = re.sub(r'((대구|부산|사직|잠실|목동)?.{0,10}기자.{0,10}[=|].{0,50})$',
                         r'__SPLIT__\g<1>', content, flags=re.MULTILINE, count=1)

        if content.find('__SPLIT__') <= 0:
            content = re.sub(r'(/?[^\n]{0,10}기자[^\n]{0,10})$', r'__SPLIT__\g<1>', content, count=1)

        if content.find('__SPLIT__') <= 0:
            content = re.sub(r'\n([^@]{0,20}@[^@]{0,50})$', r'__SPLIT__\g<1>', content, count=1)

        if content.find('__SPLIT__') <= 0:
            content = re.sub(r'(/[^@]{0,20}@.{0,50})$', r'__SPLIT__\g<1>', content, count=1)

        if content.find('__SPLIT__') <= 0:
            content = re.sub(r'(\([^)]{0,50}\))$', r'__SPLIT__\g<1>', content, count=1)

        if content.find('__SPLIT__') <= 0:
            content = re.sub(r'(\([^)]*사진[^)]{0,50}\))$', r'__SPLIT__', content, count=1)

        if content.find('__SPLIT__') <= 0:
            content = re.sub(r'(\[[^]]*사진[^)]{0,50}\])$', r'__SPLIT__', content, count=1)

        if content.find('__SPLIT__') <= 0:
            content = re.sub(r'([^ ]+?=.+?기자.{0,50})$', r'__SPLIT__\g<1>', content, count=1)

        if content.find('__SPLIT__') <= 0:
            content = re.sub(r'(\n.+?=글.{0,50})$', r'__SPLIT__\g<1>', content, count=1)

        if content.find('__SPLIT__') == 0:
            content = content.replace('__SPLIT__', '')

        if content.find('__SPLIT__') < 0:
            return content, ''
        
        token = content.split('__SPLIT__')
        last_line = token[-1].strip()

        tail = ''
        if last_line != '' and len(last_line) < 50:
            tail = last_line
            content = '\n'.join(token[0:-1])

        content = content.replace('__SPLIT__', '')

        # remove date
        content = re.sub(r'\d{4}\.\d{1,2}\.\d{1,2}\.?$', r'\n', content, flags=re.MULTILINE)

        return content, tail

    def run_pos_tagger_qouted_sentence(self, qoute_sentence, sentence, max_sentence=2048):
        """
        인용구가 있는 문장 형태소 분석
        """
        # 인용문장 바꿔치기
        frame = re.sub(r'"([^"]+)"', r'"QOUTE"', sentence)

        if frame == sentence:
            return None

        # 인용 문장 형태소 분석
        qoute_pos_tagged_list = []
        for sub_sentence in qoute_sentence.groups():
            sentence_list = self.split_sentence(sub_sentence)

            buf = []
            for single_sentence in sentence_list:
                result = ''
                if len(single_sentence) < max_sentence:
                    result = self.pos_tagger.translate_utf8(single_sentence).strip()

                buf.append(result)

            qoute_pos_tagged_list.append(' '.join(buf))

        # 문장 프레임 형태소 분석
        frame_result = self.pos_tagger.translate_utf8(frame).strip()
        token_frame = frame_result.split(' ')

        # 결과 병합
        j = 0
        for i, token in enumerate(token_frame):
            if token.find('QOUTE/SL') < 0:
                continue

            if len(qoute_pos_tagged_list) <= j:
                return None

            token_frame[i] = token_frame[i].replace('QOUTE/SL', qoute_pos_tagged_list[j])
            j += 1

        return ' '.join(token_frame)

    def run_pos_tagger_sentence(self, sentence, max_sentence=2048):
        """
        한문장 형태소 분석 결과 반환
        """
        if self.pos_tagger is None:
            return ''

        try:
            sentence_euckr = sentence.encode('euc-kr', errors='ignore')
            sentence_input = sentence_euckr.decode('euc-kr')
        except Exception:
            return '', sentence

        # 인용구 처리
        # 두산 송일수 감독은 "두 팀 다 총력전을 펼친 힘든 경기였다. 에이스 역할을 해준 니퍼트와 중심타선의 집중력으로 이길 수 있었다"면서
        #  "첫 경기 승리의 흐름 이어가도록 최선을 다하겠다"라고 말했다.

        qoute = re.search(r'"([^"]+)"', sentence_input)
        if qoute:
            try:
                result = self.run_pos_tagger_qouted_sentence(qoute, sentence_input, max_sentence)
                if result is not None:
                    return result, sentence_input
            except Exception:
                return '', sentence_input

        if len(sentence_input) > max_sentence:
            return '', sentence_input

        try:
            result = self.pos_tagger.translate_utf8(sentence_input).strip()
        except Exception:
            result = ''

        return result, sentence_input

    def run_pos_tagger(self, paragraphs):
        """
        형태소 분석

        피안타를 사용자 사전에 등록: 기존) 9피안타 = 9/SN+피안/NNG+하/XSV+다
        """
        if self.pos_tagger is None:
            return None

        result = []
        pos_tagged_tree_result = []
        for sentence_list in paragraphs:
            sentence_buf = []
            pos_tagged_tree_buf = []
            for sentence in sentence_list:
                if len(sentence) > 500:
                    sentence_buf.append('')
                    pos_tagged_tree_buf.append('')
                    continue

                try:
                    pos_tagged, sentence = self.run_pos_tagger_sentence(sentence)
                    sentence_buf.append(pos_tagged)

                    pos_tagged_tree = self.convert_pos_form_to_treebank(sentence, pos_tagged)
                    pos_tagged_tree_buf.append(pos_tagged_tree)
                except Exception:
                    sentence_buf.append('')
                    pos_tagged_tree_buf.append('')

            result.append(sentence_buf)
            pos_tagged_tree_result.append(pos_tagged_tree_buf)

        return result, pos_tagged_tree_result

    @staticmethod
    def run_engllish_pos_tagger_sentence(sentence):
        """
        한문장 영어 형태소 분석 결과 반환
        """
        import nltk

        from nltk.tag import pos_tag_sents
        from nltk.tokenize import word_tokenize

        nltk.data.path.append('{}/dictionary/nltk_data'.format(getcwd()))

        tagged_sent = []
        for tag in pos_tag_sents([word_tokenize(sentence)])[0]:
            tagged_sent.append("%s/%s" % (tag[0], tag[1]))

        pos_tagged = ' '.join(tagged_sent)

        return pos_tagged, sentence

    @staticmethod
    def merge_paragraph(paragraph):
        result = []
        for sentence_list in paragraph:
            for sentence in sentence_list:
                result.append(sentence)

        return result

    @staticmethod
    def convert_pos_form_to_treebank(sentence, pos_tagged):
        """
        광주/NNP 삼성/NNP 라이온즈/NNP+와/JKB KIA/SL 타이거즈/NNG+의/JKG 경기/NNG+는/JX 많/VA+은/ETM 비/NNG+로/JKB 취소/NNG+되/XSV+었/EP+다/EM+./SF
        """
        token_sent = sentence.split(' ')
        token_pos = pos_tagged.split(' ')

        if len(token_sent) != len(token_pos):
            return ''

        tree = ''
        for i, pos_tagged in enumerate(token_pos):
            leaf_node = ''
            pos_tagged = re.sub(r'(/[A-Z]{2,3})\+', '\g<1> ', pos_tagged)
            for pos in pos_tagged.split(' '):
                token = pos.rsplit('/', maxsplit=1)

                if len(token) != 2:
                    print(token_sent[i], pos, token, flush=True)
                    break

                if '(' == token[0]:
                    token[0] = '-LRB-'
                elif ')' == token[0]:
                    token[0] = '-RRB-'

                leaf_node += '({} {})'.format(token[0], token[1])

            tree += '({} {})'.format(token_sent[i], leaf_node)

        return '(S {})'.format(tree)

    def run_multi_domain_ner_sentence(
            self, sentence, pos_tagged, domain_list=['baseball terms', 'baseball', 'economy']):
        """
        사전기반 개체명 인식기 실행
        """
        result = {}
        try:
            for domain in domain_list:
                if domain not in self.multi_domain_ner:
                    continue

                ne_tagged = self.multi_domain_ner[domain].translate(sentence, pos_tagged).strip()
                result[domain] = ne_tagged
        except Exception as err:
            result = ''

        return result

    def run_sp_project_named_entity_sentence(self, sentence, pos_tagged):
        """
        사전기반 개체명 인식기 실행
        """
        if self.sp_project_ne_tagger is None:
            return ''

        try:
            result = self.sp_project_ne_tagger.translate(sentence, pos_tagged)
            if result is not None:
                return result.strip()
        except Exception:
            pass

        return ''

    def run_sp_project_named_entity(self, paragraphs, pos_tagged):
        """
        사전기반 개체명 인식기 실행
        """
        if self.sp_project_ne_tagger is None:
            return None

        result = []
        for i in range(len(paragraphs)):
            sentence_buf = []
            for j in range(len(paragraphs[i])):
                named_entity = self.run_sp_project_named_entity_sentence(paragraphs[i][j], pos_tagged[i][j])
                sentence_buf.append(named_entity)

            result.append(sentence_buf)

        return result

    def run_named_entity_sentence(self, sentence):
        """
        학습 기반 개체명 인식기 실행
        """
        return self.ne_tagger.tag(sentence).strip()

    def run_named_entity(self, paragraphs, ne_info=None):
        """
        개체명 인식기 실행
        """
        if self.ne_tagger is None:
            return None

        result = []
        for sentence_list in paragraphs:
            sentence_buf = []
            for sentence in sentence_list:
                named_entity = self.run_named_entity_sentence(sentence, ne_info)
                sentence_buf.append(named_entity)

            result.append(sentence_buf)

        return result

    @staticmethod
    def trans_form(pos_tagged):
        """
        형태소 분석 형식을 리스트 형식으로 변환

        한편/NNG 이날/NNG 광주/NNP+에서/JKB 열리/VV+ㄹ/ETM 예정/NNG+이/VCP+었/EP+던/ETM
        [(한편, NNG), (이날, NNG) ... ]
        """
        result = []

        raw_input = pos_tagged

        pos_tagged = re.sub(r'(/[A-Z]{2,3})\+', '\g<1> ', pos_tagged)
        for token in pos_tagged.split(' '):
            if token == '':
                continue

            try:
                word, pos = token.rsplit('/', maxsplit=1)
                result.append((word, pos))
            except Exception:
                print(['error', raw_input, pos_tagged], flush=True)

        return result

    def get_chunk(self, paragraphs):
        """
        청킹

        찬스서/NNG => 찬스에서  찬스/NNG 에서/
        9/SN 피안/NNG 하/XSV   =>    9피안타   9/SN 피안타/NNG

        황재균(29)이 롯데 자이언츠 토종 선수 역대 최초로 '20(홈런)-20(도루) 클럽'에 가입했다.
        """
        import nltk

        def tree_to_string(tree, bracket='()', quotes=False):
            """
            treebank 에서 괄호문 처리 및 Tree.fromstring 형식 일치를 위함
                leaf 노드의 형식 변경 (NP 황재균/NNP) => (NP (NNP 황재균))
            """
            from nltk.tree import Tree

            if isinstance(tree.label(), str):
                s = '%s%s' % (bracket[0], tree.label())
            else:
                s = '%s%s' % (bracket[0], repr(tree.label()))

            for child in tree:
                if isinstance(child, Tree):
                    s += '  ' + tree_to_string(child, bracket, quotes)
                elif isinstance(child, tuple):
                    word, pos = child
                    if bracket[0] == word:
                        word = '-LRB-'
                    elif bracket[1] == word:
                        word = '-RRB-'

                    s += '\n  ' + " ({} {})".format(pos, word)
                elif isinstance(child, str) and not quotes:
                    s += '\n  ' + '%s' % child
                else:
                    s += '\n  ' + ' ' + tree.unicode_repr(child)

            return s + bracket[1]

        grammar = r"""
        VP:
            {<NNG>+<XSV>}
            {<NNG>+<JKS><VV>}         # 가/JKS 되/VV   실금/NNG 이/JKS 가/VV
            {<VV><EM><VX>}      # 갈/VV 아/EM 치우/VX

        NP:
            {<NNG><SN><NNB><SN><NNB>}  # 오후/NNG 2/SN 시/NNB 30/SN 분/NNB
            {<SN><NNB><SN><NNB>}  # 2/SN 시/NNB 30/SN 분/NNB

            {<SN><SP><SN><NNG>*}  # 0/SN ./SP 5/SN
            {<SN><SO><SN><NNG>*}  # 5/SN -/SO 1/SN

            {<SL>*<NNP|NNG>+<SO><SL>*<NNP|NNG>+}  # 넥센/NNP -/SO LG/SL 전/NNG

            {<SN><SP><SN><NNG|NNP>+} # 2/SN ,/SP 3/SN 루/NNG

            {<NNG>*<SN><SW>} # 키/NNG 195/SN ㎝/SW    몸무게/NNG 113/SN ㎏/SW

            {<SN><NNG|NNP>+<SO><SN><NNG|NNP>+} # 20/SN 홈런/NNG -/SO 20/SN 도루/NNG 기록/NNG

            # {<NNP><JX><SN><NNB>} # 오/NNP 는/JX 30/SN 일/NNB  # 다이노스/NNP 는/JX 30일/NNB

            {<SN><NR>} # 7/SN 구/NR

            {<NNG>+<SN>} # 하위/NNG 톱/NNG 5/SN

        NP:
            {<SL|SN>+<NNB|NNG|NNP>+}

            {<SN>+}

            {<NNG>*<SN>+<NNG>+}

            {<SL|NNG|NNP><SO>+<SL|NNG|NNP>+}

            {<MM>+<NNG>+}

            {<NNP|NNG>+<XSN>}

            {<NNP|NNG>+}

            {<NNB><NNG>}
        """

        parser = nltk.RegexpParser(grammar)

        result = []
        for pos_tagged_list in paragraphs:
            chunks_buf = []
            for pos_tagged in pos_tagged_list:
                words = self.trans_form(pos_tagged)

                chunks = parser.parse(words)
                chunks = tree_to_string(chunks)

                chunks_buf.append(chunks)

            result.append(chunks_buf)

        return result

    @staticmethod
    def get_topics(texts):
        """
        토픽 추출
        """

        def get_top_words(result, model, feature_names, n_top_words, separator):
            for topic_idx, topic in enumerate(model.components_):
                sub_topics = []
                for i in topic.argsort()[:-n_top_words - 1:-1]:
                    feature_names[i] = feature_names[i].replace(separator, ' ')
                    feature_names[i] = feature_names[i].strip()

                    sub_topics.append(feature_names[i])

                    if feature_names[i] not in result:
                        result[feature_names[i]] = 0

                    result[feature_names[i]] += 1

                print('{}: {}'.format(topic_idx, ','.join(sub_topics)), flush=True)

        from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
        from sklearn.decomposition import NMF, LatentDirichletAllocation

        separator = '_'

        n_topics = 20
        n_word = 5
        result_topics = {}

        try:
            # NMF
            # tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, lowercase=False)
            # tfidf = tfidf_vectorizer.fit_transform(texts)
            # nmf = NMF(n_components=n_topics, random_state=1, alpha=.1, l1_ratio=.5).fit(tfidf)
            # tfidf_feature_names = tfidf_vectorizer.get_feature_names()
            #
            # get_top_words(result_topics, nmf, tfidf_feature_names, n_word, separator)

            # LDA
            tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2, lowercase=False)
            tf = tf_vectorizer.fit_transform(texts)

            lda = LatentDirichletAllocation(n_topics=n_topics, max_iter=5,
                                            learning_method='online', learning_offset=50.,
                                            random_state=0)
            lda.fit(tf)

            tf_feature_names = tf_vectorizer.get_feature_names()
            get_top_words(result_topics, lda, tf_feature_names, n_word, separator)
        except Exception:
            pass

        return list(result_topics.keys())

    @staticmethod
    def print(data, pretty=True):
        import json

        def json_serial(obj):
            """
            날자 형식을 문자로 바꾸는 함수
            """
            from datetime import datetime

            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')

            if isinstance(obj, pymongo.database.Database):
                return ''

            raise TypeError('Type not serializable')


        if isinstance(data, str) is True:
            print(data, flush=True)
        else:
            if pretty is True:
                print(json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False, default=json_serial), flush=True)
            else:
                print(json.dumps(data, sort_keys=True, ensure_ascii=False, default=json_serial), flush=True)

        return

    def sec2time(self, sec, n_msec=0):
        """
        초를 시간 문자열로 변환후 반환
        """
        if hasattr(sec, '__len__'):
            return [self.sec2time(s) for s in sec]

        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        if n_msec > 0:
            pattern = '%%02d:%%02d:%%0%d.%df' % (n_msec + 3, n_msec)
        else:
            pattern = r'%02d:%02d:%02d'

        if d == 0:
            return pattern % (h, m, s)

        return ('%d days, ' + pattern) % (d, h, m, s)

    @staticmethod
    def get_runtime(start_time=None, end_time=None):
        """
        시작 시간과 끝 시간으로 실행 시간 계산해서 반환
        """

        if start_time is None:
            return 0

        if end_time is None:
            end_time = time()

        return end_time - start_time

    def print_runtime(self, count=None, total=-1, start_time=None, interval=10):
        """
        프로그램 실행 시간 및 남은 시간 표시
        """
        # 시작시간 설정
        if start_time is None:
            if self.start_time is None:
                self.start_time = time()

            start_time = self.start_time

        if count is None or count == 0:
            if self.count is None:
                self.count = 1

            self.count += 1
            count = self.count

        # 인터벌 설정
        if interval > 0:
            if count % interval != 0:
                return

        # 시간 계산
        run_time = time() - start_time
        time_per_unit = run_time / count

        if total > 0:
            from datetime import datetime, timedelta

            remaining_time = (total - count) * time_per_unit
            finish_date = datetime.now() + timedelta(seconds=remaining_time)

            message = {
                'current': count,
                'total': total,
                'rate': count / total * 100,
                'time_per_unit': time_per_unit,
                'run_time': self.sec2time(run_time),
                'remain_time': self.sec2time(remaining_time),
                'finish_time': finish_date.strftime('%Y-%m-%d %H:%M:%S')
            }

            print('END: {finish_time:s}, '
                  'RUN: {run_time:s}/{remain_time:s}, '
                  'PER: {time_per_unit:3.2f} sec, '
                  '{rate:03.2f}%/{current:,}/{total:,}'.format(**message), file=sys.stderr, flush=True)
        else:
            print('documents: {:,}, time per unit: {:3.2f}, run time: {:s}'.format(
                count, time_per_unit, self.sec2time(run_time)), file=sys.stderr, flush=True)

        return

    @staticmethod
    def parse_date_string(date_string, is_end_date=False):
        """
        문자열 날짜 형식을 date 형으로 반환
        2016-01, 2016-01-01
        """
        token = date_string.split('-')

        result = datetime.today()
        if len(token) == 2:
            result = datetime.strptime(date_string, '%Y-%m')

            if is_end_date is True:
                result += relativedelta(months=+1)
        elif len(token) == 3:
            result = datetime.strptime(date_string, '%Y-%m-%d')

            if is_end_date is True:
                result += relativedelta(days=+1)

        if is_end_date is True:
            result += relativedelta(microseconds=-1)

        return result

    def parse_date_rage(self, date_range):
        """
        날짜 범위를 파싱해서 시작날짜와 종료날짜를 구분해서 반환

        2016-08 => 2016-08-01~2016-08-31
        2016-08~2016-09 => 2016-08-01~2016-09-30

        date += datetime.timedelta(days=1)
        """
        from dateutil.relativedelta import relativedelta

        # split from to
        token = date_range.split('~')

        str_from = token[0]
        token_from = str_from.split('-')

        if len(token) == 1:
            date = self.parse_date_string(str_from)

            start_date = date
            if len(token_from) == 2:
                end_date = date + relativedelta(months=+1)
            else:
                end_date = date + relativedelta(days=+1)

            return start_date, end_date
        elif len(token) == 2:
            str_to = token[1]

            start_date = self.parse_date_string(str_from)
            end_date = self.parse_date_string(str_to, is_end_date=True)

            return start_date, end_date

        return None, None

    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        from datetime import datetime

        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')

        raise TypeError("Type not serializable")

    @staticmethod
    def parse_argument():
        """
        파라메터 옵션 정의
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='')

        arg_parser.add_argument('-pos_tagger', help='pos_tagger', action='store_true', default=False)

        arg_parser.add_argument('-crf_ner', help='ner', action='store_true', default=False)
        arg_parser.add_argument('-ner', help='dictionary based ner', action='store_true', default=False)

        return arg_parser.parse_args()


if __name__ == "__main__":
    util = NCNlpUtil()

    args = util.parse_argument()

    if args.crf_ner is True:
        util.open_ner(model_file='dictionary/ner.josa.model')

    if args.ner is True or args.pos_tagger is True:
        util.open_pos_tagger(dictionary_path='dictionary/rsc')

        if args.ner is True:
            # util.open_sp_project_ner(config='sp_config.ini', domain='B')
            util.open_multi_domain_ner(config='sp_config.ini')

    for sentence in sys.stdin:
        sentence = sentence.strip()

        if args.crf_ner is True:
            named_entity = util.run_named_entity_sentence(sentence)
            print(named_entity, flush=True)

        if args.pos_tagger is True:
            pos_tagged, _ = util.run_pos_tagger_sentence(sentence)
            print(pos_tagged, flush=True)

        if args.ner is True:
            pos_tagged, _ = util.run_pos_tagger_sentence(sentence)

            named_entity = util.run_multi_domain_ner_sentence(sentence, pos_tagged)
            print(named_entity, flush=True)
