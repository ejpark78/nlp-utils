#!/usr/bin/env bash

# 원본 위치: https://ratsgo.github.io/embedding

COMMAND=$1
function gdrive_download () {
  CONFIRM=$(wget -c --no-check-certificate --no-netrc --quiet --save-cookies cookies.txt --keep-session-cookies --no-check-certificate "https://docs.google.com/uc?export=download&id=$1" -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')
  echo wget -c --no-check-certificate --load-cookies cookies.txt "https://docs.google.com/uc?export=download&confirm=$CONFIRM&id=$1" -O $2
  wget -c --no-check-certificate --no-netrc --load-cookies cookies.txt "https://docs.google.com/uc?export=download&confirm=$CONFIRM&id=$1" -O $2
  rm -rf cookies.txt
}

case $COMMAND in
    dump-raw-wiki)
        echo "download ko-wikipedia..."
        wget -c --no-check-certificate --no-netrc https://dumps.wikimedia.org/kowiki/latest/kowiki-latest-pages-articles.xml.bz2 -P data/raw
        mkdir -p data/processed
        ;;
    dump-raw-korquad)
        echo "download KorQuAD data..."
        wget -c --no-check-certificate --no-netrc https://korquad.github.io/dataset/KorQuAD_v1.0_train.json -P data/raw
        wget -c --no-check-certificate --no-netrc https://korquad.github.io/dataset/KorQuAD_v1.0_dev.json -P data/raw
        mkdir -p data/processed
        ;;
    dump-raw-nsmc)
        echo "download naver movie corpus..."
        wget -c --no-check-certificate --no-netrc https://github.com/e9t/nsmc/raw/master/ratings.txt -P data/raw
        wget -c --no-check-certificate --no-netrc https://github.com/e9t/nsmc/raw/master/ratings_train.txt -P data/raw
        wget -c --no-check-certificate --no-netrc https://github.com/e9t/nsmc/raw/master/ratings_test.txt -P data/raw
        mkdir -p data/processed
        ;;
    dump-blog)
        echo "download blog data.."
        mkdir -p data/processed
        gdrive_download 1Few7-Mh3JypQN3rjnuXD8yAXrkxUwmjS data/processed/processed_blog.txt
        ;;
    dump-raw)
        echo "make directories..."
        mkdir -p data
        mkdir -p data/processed
        mkdir data/tokenized
        echo "download similar sentence data..."
        wget -c --no-check-certificate --no-netrc https://github.com/songys/Question_pair/raw/master/kor_pair_train.csv -P data/raw
        wget -c --no-check-certificate --no-netrc https://github.com/songys/Question_pair/raw/master/kor_Pair_test.csv -P data/raw
        ;;
    dump-word-embeddings)
        echo "download word embeddings..."
        mkdir -p data/processed
        cd data
        gdrive_download 1FeGIbSz2E1A63JZP_XIxnGaSRt7AhXFf data/word-embeddings.zip
        unzip word-embeddings.zip
        # rm word-embeddings.zip
        ;;
    dump-sentence-embeddings)
        echo "download sentence embeddings..."
        mkdir -p data/processed
        cd data
        gdrive_download 1jL3Q5H1vwATewHrx0PJgJ8YoUCtEkaGW data/sentence-embeddings.zip
        unzip sentence-embeddings.zip
        # rm sentence-embeddings.zip
        ;;
    dump-tokenized)
        echo "download tokenized data..."
        mkdir -p data/processed
        cd data
        gdrive_download 1Ybp_DmzNEpsBrUKZ1-NoPDzCMO39f-fx data/tokenized.zip
        unzip tokenized.zip
        # rm tokenized.zip
        ;;
    dump-processed)
        echo "download processed data..."
        mkdir -p data
        cd data
        gdrive_download 1kUecR7xO7bsHFmUI6AExtY5u2XXlObOG data/processed.zip
        unzip processed.zip
        # rm processed.zip
        ;;
    process-wiki)
        echo "processing ko-wikipedia..."
        mkdir -p data/processed
        python preprocess/dump.py --preprocess_mode wiki \
            --input_path data/raw/kowiki-latest-pages-articles.xml.bz2 \
            --output_path data/processed/processed_wiki_ko.txt
        ;;
    process-nsmc)
        echo "processing naver movie corpus..."
        mkdir -p data/processed
        python preprocess/dump.py --preprocess_mode nsmc \
            --input_path data/raw/ratings.txt \
            --output_path data/processed/processed_ratings.txt \
            --with_label False
        python preprocess/dump.py --preprocess_mode nsmc \
            --input_path data/raw/ratings_train.txt \
            --output_path data/processed/processed_ratings_train.txt \
            --with_label True
        python preprocess/dump.py --preprocess_mode nsmc \
            --input_path data/raw/ratings_test.txt \
            --output_path data/processed/processed_ratings_test.txt \
            --with_label True
        ;;
    process-korquad)
        echo "processing KorQuAD corpus..."
        mkdir -p data/processed
        python preprocess/dump.py --preprocess_mode korquad \
            --input_path data/raw/KorQuAD_v1.0_train.json \
            --output_path data/processed/processed_korquad_train.txt
        python preprocess/dump.py --preprocess_mode korquad \
            --input_path data/raw/KorQuAD_v1.0_dev.json \
            --output_path data/processed/processed_korquad_dev.txt
        cat data/processed/processed_korquad_train.txt data/processed/processed_korquad_dev.txt > data/processed/processed_korquad.txt
        rm data/processed/processed_korquad_*.txt
        ;;
    mecab-tokenize)
        echo "mecab, tokenizing..."
        python preprocess/supervised_nlputils.py --tokenizer mecab \
            --input_path data/processed/processed_wiki_ko.txt \
            --output_path data/tokenized/wiki_ko_mecab.txt
        python preprocess/supervised_nlputils.py --tokenizer mecab \
            --input_path data/processed/processed_ratings.txt \
            --output_path data/tokenized/ratings_mecab.txt
        python preprocess/supervised_nlputils.py --tokenizer mecab \
            --input_path data/processed/processed_korquad.txt \
            --output_path data/tokenized/korquad_mecab.txt
        ;;
    process-jamo)
        echo "processing jamo sentences..."
        python preprocess/unsupervised_nlputils.py --preprocess_mode jamo \
            --input_path data/tokenized/corpus_mecab.txt \
            --output_path data/tokenized/corpus_mecab_jamo.txt
        ;;
    space-correct)
        echo "train & apply space correct..."
        python preprocess/unsupervised_nlputils.py --preprocess_mode train_space \
            --input_path data/processed/processed_ratings.txt \
            --model_path data/processed/space-correct.model
        python preprocess/unsupervised_nlputils.py --preprocess_mode apply_space_correct \
            --input_path data/processed/processed_ratings.txt \
            --model_path data/processed/space-correct.model \
            --output_path data/processed/corrected_ratings_corpus.txt \
            --with_label False
        python preprocess/unsupervised_nlputils.py --preprocess_mode apply_space_correct \
            --input_path data/processed/processed_ratings_train.txt \
            --model_path data/processed/space-correct.model \
            --output_path data/processed/corrected_ratings_train.txt \
            --with_label True
        python preprocess/unsupervised_nlputils.py --preprocess_mode apply_space_correct \
            --input_path data/processed/processed_ratings_test.txt \
            --model_path data/processed/space-correct.model \
            --output_path data/processed/corrected_ratings_test.txt \
            --with_label True
        ;;
    soy-tokenize)
        echo "soynlp, LTokenizing..."
        mkdir -p data/tokenized
        python preprocess/unsupervised_nlputils.py --preprocess_mode compute_soy_word_score \
            --input_path data/processed/corrected_ratings_corpus.txt \
            --model_path data/processed/soyword.model
        python preprocess/unsupervised_nlputils.py --preprocess_mode soy_tokenize \
            --input_path data/processed/corrected_ratings_corpus.txt \
            --model_path data/processed/soyword.model \
            --output_path data/tokenized/ratings_soynlp.txt
        ;;
    komoran-tokenize)
        echo "komoran, tokenizing..."
        mkdir -p data/tokenized
        python preprocess/supervised_nlputils.py --tokenizer komoran \
            --input_path data/processed/corrected_ratings_corpus.txt \
            --output_path data/tokenized/ratings_komoran.txt
        ;;
    okt-tokenize)
        echo "okt, tokenizing..."
        mkdir -p data/tokenized
        python preprocess/supervised_nlputils.py --tokenizer okt \
            --input_path data/processed/corrected_ratings_corpus.txt \
            --output_path data/tokenized/ratings_okt.txt
        ;;
    hannanum-tokenize)
        echo "hannanum, tokenizing..."
        mkdir -p data/tokenized
        python preprocess/supervised_nlputils.py --tokenizer hannanum \
            --input_path data/processed/corrected_ratings_corpus.txt \
            --output_path data/tokenized/ratings_hannanum.txt
        ;;
    khaiii-tokenize)
        echo "khaiii, tokenizing..."
        mkdir -p data/tokenized
        python preprocess/supervised_nlputils.py --tokenizer khaiii \
            --input_path data/processed/corrected_ratings_corpus.txt \
            --output_path data/tokenized/ratings_khaiii.txt
        ;;
    bert-tokenize)
        mkdir -p data/tokenized
        python preprocess/unsupervised_nlputils.py --preprocess_mode bert_tokenize \
            --vocab_path data/sentence-embeddings/bert/pretrain-ckpt/vocab.txt \
            --input_path data/processed/corrected_ratings_corpus.txt \
            --output_path data/tokenized/ratings_sentpiece.txt
        ;;
    mecab-user-dic)
        echo "insert mecab user dictionary..."
        cd /tmp/mecab-ko-dic-2.1.1-20180720
        cp -f preprocess/mecab-user-dic.csv /tmp/mecab-ko-dic-2.1.1-20180720/user-dic/nnp.csv
        ./tools/add-userdic.sh
        make install
        cd /notebooks/embedding
        ;;
    make-bert-vocab)
        echo "making BERT vocabulary..."
        mkdir -p data
        cd data
        gdrive_download 1kUecR7xO7bsHFmUI6AExtY5u2XXlObOG data/processed.zip
        unzip processed.zip
        rm processed.zip
        cd /notebooks/embedding
        python preprocess/unsupervised_nlputils.py --preprocess_mode make_bert_vocab \
            --input_path data/processed/processed_wiki_ko.txt \
            --vocab_path data/processed/bert.vocab
        mv sentpiece* data/processed
        ;;
esac
