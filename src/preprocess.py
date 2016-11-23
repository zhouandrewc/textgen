#
# Pre-process text into usable datasets
#
#

import io
import nltk
from os import listdir
from os.path import isfile, join


def pre_process(string):
    """
    Perform all pre-processing steps on input string
    :param string: input
    :return: pre-processed list of tokens for training
    """

    return string

raw_training_path = 'training/'
raw_train_data = [f for f in listdir(raw_training_path) if isfile(join(raw_training_path, f))]

output = 'train.txt'

with io.open(output, 'w', encoding='utf-8') as output_file:
    for raw_file in raw_train_data:
        with io.open(join(raw_file, raw_training_path), 'r', encoding='utf-8') as input_file:
            # Pre-process each input file and write to output file
            output_file.write(pre_process(input_file.read()))
