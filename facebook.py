#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import requests

from time import sleep, time
from pymongo import MongoClient
from datetime import datetime


class Facebook(object):
    """ """

    def __init__(self):
        super().__init__()

        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        urllib3.disable_warnings(UserWarning)

        self.host = 'localhost'
        self.port = 27017

    def get_all_feed(self, page_id, access_token, db_name, collection_name):
        """ """
        i = 0
        start = datetime.now()

        # 마지막 쿼리를 가져옴
        url = None
        # url, is_done = self.get_last_request(db_name=db_name, collection_name=collection_name)
        # if is_done is True:
        #     print('Skip {}'.format(collection_name), flush=True)
        #     return True

        # 마지막 쿼리부터 가져오거나 마지막 피드를 가져와서 시작
        print('{} {} {}'.format(collection_name, page_id, start), flush=True)
        if url is not None:
            statuses = self.request_feed(url=url)
            sleep(5)
        else:
            statuses, url = self.get_last_feed(page_id=page_id, access_token=access_token, limit=10)

        # next 가 없을때까지 반복
        while True:
            self.save_data(data_list=statuses['data'], db_name=db_name, collection_name=collection_name, url=url)

            i += 1
            if i % 10 == 0:
                print('{} {}'.format(i, datetime.now()))

            # if there is no next page, we're done.
            if 'paging' in statuses.keys() and 'next' in statuses['paging']:
                url = statuses['paging']['next']

                try:
                    url_info, query = self.parse_url_query(url=url)
                    print(datetime.now(), collection_name, i, query['after'][0:10], flush=True)
                except Exception as e:
                    print(datetime.now(), collection_name, i, url, e, flush=True)

                statuses = self.request_feed(url=url)
                sleep(10)
            else:
                break

        self.save_data(data_list=None, db_name=db_name, collection_name=collection_name, url=None)
        print('완료: {} {} {}'.format(collection_name, i, datetime.now() - start), flush=True)

        return True

    def get_last_request(self, db_name, collection_name):
        """ """
        from pymongo import DESCENDING

        result = None
        is_done = False

        connect = MongoClient('mongodb://{}:{}'.format(self.host, self.port))
        db = connect.get_database(db_name)

        collection = db.get_collection(name='history-{}'.format(collection_name))

        # 히스토리 저장
        try:
            cursor = collection.find(filter={}).sort('insert_date', DESCENDING).limit(1)
            for document in cursor:
                if 'url' in document:
                    result = document['url']

                if 'is_done' in document and document['is_done'] is True:
                    is_done = True

                break

            cursor.close()
        except Exception as e:
            print('save history error: ', e, flush=True)

        connect.close()
        return result, is_done

    def test_graph_api(self, page_id, access_token):
        """ """
        url = 'https://graph.facebook.com/v2.11/{page_id}/' \
              '?access_token={access_token}'.format(page_id=page_id, access_token=access_token)

        url = 'https://graph.facebook.com/v2.11/{page_id}/feed/' \
              '?access_token={access_token}'.format(page_id=page_id, access_token=access_token)

        # retrieve data
        data = self.request_feed(url)

        print(json.dumps(data, indent=4, sort_keys=True))

        return True

    def get_last_feed(self, page_id, access_token, limit):
        """ """

        fields = [
            'caption',
            'comments{comment_count,message,like_count,message_tags,likes,reactions,parent,created_time,'
            'id,from,comments{id,like_count,comment_count,likes,parent,created_time}}',
            'created_time',
            'description',
            'from',
            'id',
            'likes.summary(true)',
            'link',
            'message',
            'name',
            'shares',
            'type',
            'with_tags'
        ]
        # 'message_tag',

        query = {
            'page_id': page_id,
            'limit': limit,
            'access_token': access_token,
            'fields': ','.join(fields),
        }

        # construct the URL string
        url = 'https://graph.facebook.com/{page_id}/feed/?' \
              'fields={fields}&limit={limit}&access_token={access_token}'.format(**query)

        return self.request_feed(url), url

    def request_feed(self, url, max_try=5, request_state=False):
        """ """
        if request_state is True:
            try:
                url_info, query = self.parse_url_query(url=url)
                print(datetime.now(), url_info.path, flush=True)
                print(json.dumps(query, indent=4, sort_keys=True), flush=True)
            except Exception as e:
                print(datetime.now(), url, e, flush=True)

        while True:
            try:
                response = requests.get(url=url, timeout=60)
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
            except Exception as e:
                print('ERROR at request {}: {}'.format(url, datetime.now()), e, flush=True)

                sleep(25)

                max_try -= 1
                if max_try < 0:
                    return None

    @staticmethod
    def parse_url_query(url):
        """ """
        from urllib.parse import urlparse, parse_qs

        query = None
        url_info = None
        try:
            url_info = urlparse(url)
            query = parse_qs(url_info.query)
        except Exception as e:
            print('error at parse url query: ', e, flush=True)

        result = {}
        if query is not None:
            for k in query:
                result[k] = query[k][0]

        return url_info, result

    def save_data(self, data_list, db_name, collection_name, url):
        """ """
        from pymongo.errors import BulkWriteError

        insert_date = datetime.now()

        # 몽고 디비 핸들 오픈
        connect = MongoClient('mongodb://{}:{}'.format(self.host, self.port))
        db = connect.get_database(db_name)

        # id 변경
        if data_list is not None:
            documents = []
            for data in data_list:
                data['_id'] = data['id']

                # 디비 저장 시간 기록
                data['insert_date'] = insert_date
                documents.append(data)

            collection = db.get_collection(name=collection_name)
            # 데이터 저장
            try:
                collection.insert_many(documents)
            except BulkWriteError as e:
                print('ERROR: ', e, e.details, flush=True)
            except Exception as e:
                print('ERROR: ', e, flush=True)

        # 히스토리 저장
        try:
            history_collection = db.get_collection(name='history-{}'.format(collection_name))

            if url is None:
                history = {
                    'is_done': True,
                    'insert_date': insert_date
                }
            else:
                history = {
                    'is_done': False,
                    'url': url,
                    'insert_date': insert_date
                }

            history_collection.insert_one(history)
        except Exception as e:
            print('ERROR history: ', e, flush=True)

        connect.close()

        return True


def main():
    app_id = "142140609745132"
    app_secret = "345abf6695e519ab147bee0d10d7aebb"  # DO NOT SHARE WITH ANYONE!

    access_token = '{}|{}'.format(app_id, app_secret)

    util = Facebook()

    # 그룹
    groups = [
        ('TensorFlowKR', '255834461424286')
    ]

    # 야구
    kbo_teams = [
        # 야구단
        ('BearSpotv', 'Bearspotv'),
        ('KBO', 'kbo1982'),
        ('LG 트윈스', 'LGTWINSSEOUL'),
        ('NC 다이노스 서포터', 'NcdinosSupporter'),
        ('NC 다이노스', 'ncdinos'),
        ('SK 와이번스', 'SKwyverns'),
        ('고양 다이노스', 'goyangdinos'),
        ('넥센히어로즈', 'heroesbaseballclub'),
        ('다이노스 여자야구단', 'wdinos'),
        ('두산베어스', '1982doosanbears'),
        ('랠리 다이노스', 'ncrallydinos'),
        ('롯데자이언츠', 'lottegiantsbusan'),
        ('롯데자이언츠 응원단(Lotte Giants)', 'entertrue'),
        ('삼성라이온즈', 'snssamsunglions'),
        ('수원-kt wiz', 'ktwiz'),
        ('한화이글스', 'hanwhaeagles.news'),

        # 야구 기타
        ('뚝심마니Baseball', 'dooksimbaseball'),
        ('마니아리포트', 'maniareport'),
        ('스카이스포츠 - skySports', 'skysports01'),
        ('스포츠 마니아 일루모여', 'sportssmile'),
        ('야구랑 선수랑', 'lovebaseballwithplayers'),
        ('야구없인 못살아', 'lifeneedsbaseball'),
        ('야구친구', 'yaguchingu'),
        ('창원마산야구장', 'changwonbaseballpark'),
        ('Baseball V', 'baseballv')
    ]

    # 대나무숲
    bamboo = [
        ('DGIST 대나무숲', 'dgbamboo'),
        ('GGHS 대나무숲', 'gghsbamboocom'),
        ('GIST 대나무숲', 'GISTIT.ac.kr'),
        ('IVF 대나무숲', 'bambooivf'),
        ('UST 대나무숲', 'ustbamboo'),
        ('가정고 대나무숲', 'incheon101010'),
        ('가천대학교 대나무숲', 'gcubamboo'),
        ('가톨릭대학교 대나무숲', 'CUKbby'),
        ('간호학과-간호사 대나무숲', 'activenursing'),
        ('강남대학교 대나무숲', 'knubambooforest'),
        ('건국대학교 대나무숲', 'konkukbamboo'),
        ('경기대학교 대나무숲', 'kyonggibamboo'),
        ('경북대학교 대나무숲', 'KNUbamboo'),
        ('경일대학교 대나무숲', 'KIUBABOO'),
        ('경희대학교 대나무숲', 'kyungheebamboo'),
        ('계명대학교 대나무숲', 'bamboo1kmu'),
        ('고려대학교 대나무숲', 'koreabamboo'),
        ('공주대학교 대나무숲', 'KNUGrove'),
        ('광양제철고 대나무숲', 'daesoopjigi'),
        ('광운대학교 대나무숲', 'kwubamboo'),
        ('구로고등학교 대나무숲', 'gurohighschooI'),
        ('국립 경상대학교 대나무숲', 'gnubamboo1'),
        # ('금성고 대나무숲', '금성고-대나무숲-679900038835070'),
        # ('금오공대 대나무숲', '금오공대-대나무숲-1944383369118783'),
        # ('금천고 대나무숲', '금천고-대나무숲-291971084345664'),
        ('김천대학교 대나무숲', 'Gimcheonuniversity'),
        ('나사렛대학교 대나무숲', '60DeLike'),
        ('남서울대학교 대나무숲', 'nsunivbamboo'),
        ('단국대학교 대나무숲', 'dkubamboo'),
        ('대구교대 대나무숲', 'bamb00dnue'),
        ('대전대학교 대나무숲', 'DJUTHINK'),
        ('대전동신과학고등학교 대나무숲', 'DDSHbamboo'),
        ('대한민국 고1 대나무숲', 'GO1Bamboo'),
        ('덕성여대 대나무숲', 'dssaytomeanything'),
        ('동국대학교 대나무숲', 'donggukbamboo'),
        ('동아방송예술대학교 대나무숲', 'dongdeasup'),
        # ('마산대학교 대나무숲', '마산대학교-대나무숲-453027114840846'),
        ('명지대학교 대나무숲 LTE', 'bamboomju'),
        ('명지대학교 대나무숲', 'mjubamboo'),
        # ('무주중학교 대나무숲', '무주중학교-대나무숲-374495616341957'),
        ('민사고 대나무숲', 'kmlabamboo'),
        ('부경대학교 대나무숲', 'PKNUBamboo'),
        ('사회복지 대나무숲', 'swdaenamu'),
        # ('삼육보건대학교 대나무숲', '삼육보건대학교-대나무숲-695834760463025'),
        ('상산고 대나무숲', 'sangsanbamboo'),
        ('상지대학교 대나무숲', 'sangjiuniversitynew'),
        ('서강대학교 대나무숲', 'sogangbamboo'),
        ('서경대학교 대나무숲', 'SeoKyeongUnivBamboo'),
        ('서울과학기술대학교 대나무숲', 'seoultechbamboo'),
        ('서울국제고 대나무숲', 'sghsbamboo'),
        ('서울대학교 대나무숲', 'SNUBamboo'),
        # ('서울대학교 자연과학대학 대나무숲', '서울대학교-자연과학대학-대나무숲-1624865904412987'),
        ('서울시립대학교 대나무숲', 'uosbamboo'),
        ('서울여대 대나무숲', 'swubamboo'),
        ('서울예술대학교 대나무숲', 'yesulbamboo'),
        ('성결대학교 대나무숲', 'SKUBAMBOO'),
        ('성균관대학교 대나무숲', 'SKKUBamboo'),
        ('성신여자대학교 대나무숲', 'SungshinBamboo'),
        ('세명대학교 대나무숲', 'SMUBamboo2016'),
        ('세종대학교 대나무숲', 'sejongbamboo'),
        # ('속초고등학교 대나무숲', '속초고등학교-대나무숲-180032975886297'),
        # ('수원여자대학교 대나무숲', '수원여자대학교-대나무숲-919669591402989'),
        ('숙명여대 대나무숲', 'bamboosmwu'),
        ('순천대학교 대나무숲', 'SCNUbamboo'),
        ('순천향대 대나무숲', 'schubamboo'),
        ('숭실대학교 대나무숲', 'sstt2015'),
        # ('신장고등학교 대나무숲', '신장고등학교-대나무숲-1427049140882982'),
        ('아주대학교 대나무숲', 'ajoubamboo'),
        ('안동대학교 대나무숲', 'ANUbamboo'),
        ('안양대학교 대나무숲', 'anyangbamboo'),
        ('안화고등학교 대나무숲', 'anhwahighschool'),
        ('연세대학교 대나무숲', 'yonseibamboo'),
        ('영남대학교 대나무숲', 'yubamboo.net'),
        ('울산과학고 대나무숲', 'ushsbamboo'),
        ('유니스트 대나무숲', 'unibamboooo0'),
        ('을지대학교 대나무숲', 'euljibamboo'),
        ('인천대학교 대나무숲', 'incheonbamboo'),
        ('인하대학교 대나무숲', 'inhabamboo'),
        ('전국교대생 대나무숲', 'eedubamboo'),
        ('전남대학교 대나무숲', 'MaeGuemI'),
        ('전대숲-전국대학생 통합 대나무숲', 'svbamboo'),
        # ('전주교대 대나무숲', '전주교대-대나무숲-1325126304217667'),
        ('중앙대학교 대나무숲', 'caubamboo'),
        ('중앙대학교 야생의 대나무숲', 'cauwildbamboo'),
        # ('지족고 대나무숲', '지족고-대나무숲-1737895163092670'),
        ('천안고등학교 대나무숲', 'chsshare'),
        ('청운대학교 인천캠퍼스 대나무숲', 'IncCWUbamboo'),
        # ('청주교육대학교 대나무숲 시즌2', '청주교육대학교-대나무숲-시즌2-1704678496497163'),
        ('총신대학교 대나무숲', 'chongshinBamboo'),
        # ('추계예술대학교 대나무숲', '추계예술대학교-대나무숲-1477527812555609'),
        ('충남대학교 대나무숲', 'ChungNamNationalBamboo'),
        ('포항공대 대나무숲', 'postechbamboo'),
        # ('한강미디어고등학교 대나무숲', '한강미디어고등학교-대나무숲-1450635828311879'),
        ('한경대학교 대나무숲', 'hknu162'),
        ('한국 미디어 대나무숲', 'KoreaMediaBamboo'),
        # ('한국교원대학교 대나무숲', '한국교원대학교-대나무숲-2058147414411332'),
        ('한국교통대학교 대나무숲', 'KnutBambooForest'),
        ('한국디지털미디어고등학교 대나무숲', 'dimigoBamboo'),
        ('한국외국어대학교 글로벌캠퍼스 대나무숲', 'globalbamboo'),
        ('한국외국어대학교 대나무숲', 'hufsbamboo'),
        ('한국장학재단 연합생활관 대나무숲', 'kosafdormitory'),
        ('한국항공대학교 대나무숲', 'KauBamboo1'),
        ('한국해양대학교 대나무숲', 'KMOUbamboo'),
        ('한동대학교 대나무숲', 'handongbamboo'),
        ('한민고등학교 대나무숲', 'HanminBamboo'),
        ('한밭대학교 대나무숲', 'HNUbamboo'),
        ('한세대학교 대나무숲', 'hanseibamboo'),
        ('한양대에리카 대나무숲', 'ericadruwa'),
        ('한양대학교 대나무숲', 'hyubamboo'),
        ('협성대학교 대나무숲', 'hyupsungbamboo'),
        ('호원대학교 대나무숲', 'howonuniversional'),
        ('홍익대학교 대나무숲', 'hongikbamboo')
    ]

    news = [
        # 언론사
        ('JTBC 뉴스', 'jtbcnews'),
        ('JTBC 이규연의 스포트라이트', 'jtbcspotlight'),
        ('KBS 스포츠', 'kbssports'),
        ('KBS뉴스', 'kbsnews'),
        ('MBC News', 'MBCnews'),
        ('MBC 스포츠플러스', 'mbcsportsplus'),
        ('SBS Onair Sports', 'sbsallsports'),
        ('SBS Plus', 'sbsplus'),
        ('SBS Sports', 'sbssportsnow'),
        ('SBS 뉴스', 'SBS8news'),
        ('SBS 라디오', 'sbsradioOfficial'),
        ('SBS', 'sbsnow'),
        ('SBSCNBC', 'SBSCNBC'),
        ('tvN(티비엔)', 'cjtvngo'),
        # ('손석희', '손석희-208694602527341'),
        ('손석희와 함께하는 사람들', 'togetherson'),
        ('엠빅뉴스', 'mbicnews'),
        ('채널A', 'tv.chA'),
        ('채널A 뉴스', 'channelanews'),
        ('채널A 라이프', 'tvcha.life'),

        # 통신사
        ('뉴시스', 'newsis.news'),
        # ('연합뉴스 그래픽뉴스팀', '연합뉴스-그래픽뉴스팀-762362527154939'),
        ('연합뉴스 미디어랩', 'ymedialabs'),
        ('연합뉴스', 'yonhap'),
        ('뉴스1', 'news1kr'),
        ('NSP통신', 'nspna'),

        # 인터넷 신문
        ('오마이뉴스', 'OhmyNewsKorea'),
        ('프레시안', 'pressian.news'),
        ('뉴데일리', 'newdailybiz'),
        ('데일리안 스포츠', 'dailiansports'),
        ('데일리안뉴스', 'dailiannews1'),
        ('미디어오늘', 'mediatodaynews'),
        ('미디어오늘내일', 'mediatonul2'),
        ('코리아옵저버', 'koreaobserver'),
        ('딴지일보', 'ddanziilbo'),

        # 전국지신문
        ('테크 조선', 'techchosun'),
        ('경향비즈', 'biznlife'),
        ('경향신문', 'kyunghyangshinmun'),
        ('국민일보', 'kukmindaily'),
        ('뉴욕타임즈', 'nytimes'),
        ('데이터랩 - Datalab', 'DataroomKBS'),
        ('동아비즈니스리뷰', 'dbrinsight'),
        ('동아일보', 'dongamedia'),
        ('동아일보논설위원실', 'dongaoped'),
        ('매거진 D', 'magazinedonga'),
        ('문화일보', 'munhwailbo'),
        ('서울신문 TV&EN', 'seoultv'),
        ('서울신문', 'TheSeoulShinmun'),
        ('세계일보', 'segyetimes'),
        ('영화-좋아', 'movielikekorea'),
        # ('조선경제아이', '조선경제아이-370027806348731'),
        ('조선일보', 'chosun'),
        ('조이뉴스24 - JoyNews24', 'JoyNews.TV'),
        ('주간경향', 'wkyunghyang'),
        ('주간조선', 'weeklychosun'),
        ('한겨레 사회부', 'hanisocialnews'),
        ('한겨레', 'hankyoreh'),
        ('한겨레21', 'hankyoreh21'),
        ('한겨레스페셜', 'hanispecialpage'),
        ('한국일보', 'hkilbo'),
        ('환경일보', 'www.hkbs.co.kr'),

        # 경제신문
        ('매일경제 Biz Times', 'weeklymkmba'),
        # ('매일경제', 'maekyungsns'),
        ('서울경제 썸', 'sedailythumb'),
        ('서울경제신문', 'seouleconomydaily'),
        ('한국경제신문 사설·칼럼', 'hankyung.editorial'),
        ('한국경제신문', 'hankyungmedia'),
        ('헤럴드경제', 'TheHeraldBusiness'),

        # 스포츠신문
        ('스포츠서울', 'sportsseoul1'),
        ('일간스포츠 야구뉴스', 'is.baseballnews'),
        ('일간스포츠', 'isplus1'),
        ('스포츠조선', 'sportschosun'),
        ('스포츠경향', 'sportkh'),
        ('스포츠한국', 'sportshankooki'),
        ('스포츠동아', 'sportsdonga'),
        ('스포츠월드', 'sportsworldsns'),

        # IT신문
        ('디지털타임스', 'Digitaltimesnews'),
        ('전자신문', 'etnews.kr'),
        ('전자신문엔터테인먼트', 'ETenterN'),

        # 잡지
        ('시사인', 'sisain'),
        ('레이디경향', 'ladykyunghyang'),
        ('IT동아-게임동아', 'itdonga'),
        ('IT조선 컨퍼런스', 'itchosuncon'),
        ('우먼 동아일보', 'thewomandonga'),
        ('과학동아', 'sciencedonga'),
        ('시사저널', 'sisajournal'),
        ('마이크로소프트웨어', 'dailymaso'),

        # 기타
        ('스포티비 뉴스', 'spotvnews'),
        ('스포티비', 'spotv'),
        ('그놈의디지털', 'whatisdigital'),
        ('뉴스퀘어 - Newsquare', 'newsquare.kr'),
        ('뉴스타운', 'newstown1'),
        ('뉴스타운', '뉴스타운-286039791506536'),
        ('디스패치', 'koreadispatch'),
        ('디지털 저널리즘 혁신', 'Journalismpage'),
        ('신촌타임즈', 'theshinchontimes2015'),
        ('아시아투데이', 'Asiatoday.online'),
        ('아이뉴스24 - INews24', 'inews24'),
        ('애플경제', 'applennews7'),
        ('에스비즈뉴스', 'sbiznewskr'),
        ('월요신문', 'wolyonews'),
        ('이슈갤러리', 'issuegall'),
        ('이슈컷', 'issuecut'),
        ('이슈픽 Issue Pic', 'issuepic1'),
        ('재경일보', 'jknewscorp'),
        ('아띠참신문', 'attichamnews'),
        ('팟캐스트 디스팩트', 'disfact'),
        ('프레스센터', 'press7651'),
        ('한국스포츠경제 비즈앤피플', 'biznpeople'),
        ('위키트리', 'wikitree.page'),
        ('넥스트데일리', 'nextdailykr'),
        ('메디게이트뉴스', 'medigatenews'),
        ('미디어썰', 'mediassul'),
        ('미디어펜', 'mediapen'),
        ('민중의소리', 'newsvop'),
        ('비디오머그 - VIDEO MUG', 'videomug'),
        ('비즈니스워치', 'businesswatch'),
        ('스브스뉴스', 'subusunews'),
        ('시사위크', 'sisaweek'),

    ]

    etc = [
        # 게임사
        ('엔씨소프트', 'ncsoft'),

        # IT
        ('코딩한잔', 'acupofcode'),
        ('코딩이 알고싶다', 'iwannaknowcoding'),

        # 출판사
        ('리더스북', 'leadersbook'),

        # 기타
        ('서울경기케이블tv', 'dlivech1'),
        ('어반어스', 'urbanearth.face'),
        ('엠톡', 'mtalkmagazine'),
        ('열린사람들', 'peopleopener'),
        ('영화공장', 'moviecapture'),
        ('오래된 문장의 위로', 'humanplus100'),
        ('웅진북클럽', 'woongjinthinkbig'),
        ('피키무비', 'pikimovie'),
        ('피키캐스트', 'allnewpiki'),
        ('한국기자협회', 'journalistskorea')
    ]

    page_list = kbo_teams + news + etc + bamboo
    db_name = 'facebook'

    for page in page_list:
        collection_name, page_id = page

        util.get_all_feed(page_id=page_id, access_token=access_token,
                          db_name=db_name, collection_name=collection_name)

    return True


if __name__ == "__main__":
    main()
