#!/bin/bash
TASK_NAME="TDT2"
DATA_DIR="data_test"
OUTPUT_EXPDIR="exp/TDT2_spk"
stage=3
train_set=train_spk
test_set=test_short_spk

set -euo pipefail

if [ $stage -le 0 ]; then 
    # text (train, test_short, test_long)
    python preprocess.py --output_dir $DATA_DIR --task_name $TASK_NAME --is_training true --is_short false --is_spoken false
    python preprocess.py --output_dir $DATA_DIR --task_name $TASK_NAME --is_training false --is_short true --is_spoken false
    python preprocess.py --output_dir $DATA_DIR --task_name $TASK_NAME --is_training false --is_short false --is_spoken false
    # spoken (train, test_short, test_long)
    python preprocess.py --output_dir $DATA_DIR --task_name $TASK_NAME --is_training true --is_short false --is_spoken true
    python preprocess.py --output_dir $DATA_DIR --task_name $TASK_NAME --is_training false --is_short true --is_spoken true
    python preprocess.py --output_dir $DATA_DIR --task_name $TASK_NAME --is_training false --is_short false --is_spoken true
fi

if [ $stage -le 1 ]; then
   # training + evaluate
    python3 run_classifier_TDT2.py --task_name $TASK_NAME --do_train --do_eval --do_lower_case \
                                   --data_dir $DATA_DIR/$TASK_NAME --bert_model bert-base-chinese \
                                   --max_seq_length 128 --train_batch_size 32 --learning_rate 2e-5 \
                                   --num_train_epochs 3.0 --output_dir $OUTPUT_EXPDIR \
                                   --set_trainset ${train_set}.csv --set_testset ${test_set}.all.csv
fi

#if [ $stage -le 2 ]; then
    # only do_eval
    #python3 run_classifier_TDT2.py --task_name $TASK_NAME --do_eval --do_lower_case \
    #                               --data_dir $DATA_DIR/$TASK_NAME --bert_model bert-base-chinese \
    #                               --max_seq_length 128 --train_batch_size 32 --learning_rate 2e-5 \
    #                               --num_train_epochs 3.0 --output_dir $OUTPUT_EXPDIR \
    #                               --set_trainset train.csv --set_testset test_short.all.csv
#fi

if [ $stage -le 3 ]; then
    # text (short query)
    python BERT_test.py --bert_results $OUTPUT_EXPDIR/${train_set}_${test_set}.txt --is_training false --is_short true --is_spoken true 
fi
