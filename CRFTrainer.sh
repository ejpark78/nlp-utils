#!/usr/bin/env bash


time ./CRFTrainer.py -train_set data/named_entity/baseball/train.00.json.bz2 -model_name model/baseball.00.model
time ./CRFTrainer.py -train_set data/named_entity/baseball/train.01.json.bz2 -model_name model/baseball.01.model

time ./CRFTrainer.py -train_set data/named_entity/baseball/train.json.bz2 -model_name model/baseball-baseline.model
