#
# NIST Test for NLG text evaluation
#
# Implementation based on:
# Papineni, K., Roukos, S., Ward, T. and Zhu, W.J., 2002, July. BLEU: a method for automatic evaluation of machine
# translation. In Proceedings of the 40th annual meeting on association for computational linguistics (pp. 311-318).
# Association for Computational Linguistics.
#
# Strong correlation with human expert evaluation for natural language generation (NLG) shown by
# Belz, A. and Reiter, E., 2006, April. Comparing Automatic and Human Evaluation of NLG Systems. In EACL.
#

import io
import numpy as np
import math
from fractions import Fraction
from collections import Counter
from nltk.util import ngrams

# Dictionary to memoize/cache information value of various n-grams
info_value = {}

# List of words in reference document
reference_data = None


def pre_process(str_text):
    """
    Perform all pre-processing steps on input string
    :param str_text: input
    :return: pre-processed list of tokens for training
    """

    str_text = str(str_text)

    # Uncomment to remove punctuation from all texts
    # import string
    # replace_punctuation = string.maketrans(string.punctuation, ' '*len(string.punctuation))
    # str_text = str_text.translate(replace_punctuation)

    str_text = str_text.lower().replace('\n', ' ').replace('\r', ' ')
    return ' '.join(str_text.split())


def get_information_value(words):
    """
    Calculate information value from reference document
    Let words = [w_1, w_2, ..., w_n], n-gram,
    k_1 = Number of occurrences of (n-1)-gram [w_1, w_2, ..., w_{n-1}] in text
    k_2 = Number of occurrences of n-gram [w_1, w_2, ..., w_n] in text
    then Info(words) = log_2 (k_1 / k_2)
    :param words: list of words (n-gram)
    :return: Information value of words
    """

    if reference_data is None:
        raise ValueError("No reference data found")

    words_k1 = ' '.join(words)
    words_k2 = ' '.join(words[:-1])
    try:
        return info_value[words_k1]
    except KeyError:
        pass

    k1 = 0.1 + reference_data.count(words_k1)
    k2 = 0.1 + reference_data.count(words_k2)
    info_count = np.log2(k1 / k2)

    info_value[words_k1] = info_count
    return info_count


def modified_bleu(references, hypothesis, weights=(0.25, 0.25, 0.25, 0.25)):
    """
    Calculate a single corpus-level BLEU score (aka. system-level BLEU) for all
    the hypotheses and their respective references.
    Instead of averaging the sentence level BLEU scores (i.e. marco-average
    precision), the original BLEU metric (Papineni et al. 2002) accounts for
    the micro-average precision (i.e. summing the numerators and denominators
    for each hypothesis-reference(s) pairs before the division).
    :param references: a corpus of lists of reference sentences, w.r.t. hypotheses
    :param hypothesis: a single hypothesis sentence split list for evaluation
    :param weights: weighting scheme (n values, 4 by default) corresponding to 1-grams to n-grams
    :return: modified BLEU score value, accounting for over-fitting
    """

    # Counter instance for numerators (Number of n-gram matches vs n-gram n value as key)
    p_numerators = Counter()
    # Counter instance for denominator (Number of n-gram in references vs n-gram n value as key)
    p_denominators = Counter()

    # For each order of ngram, calculate the numerator and
    # denominator for the corpus-level modified precision.
    for i, _ in enumerate(weights, start=1):
        p_i = modified_precision(references, hypothesis, i)
        p_numerators[i] += p_i.numerator
        p_denominators[i] += p_i.denominator

    # No brevity penalty is applied - different lengths of hypothesis and reference strings are irrelevant
    # in the case of evaluating text generation results
    # Collects the various precision values for the different ngram orders
    p_n = [Fraction(p_numerators[i], p_denominators[i]) for i, _ in enumerate(weights, start=1)]

    # Check if no matching 1-grams found, implying no matching n-grams found
    if p_numerators[1] == 0:
        return 0

    # Do not perform smoothing as per typical BLEU functions, values remain in the form of fractions.Fraction
    s = (w * math.log(p_i) for i, (w, p_i) in enumerate(zip(weights, p_n)) if p_i.numerator != 0)
    return math.exp(math.fsum(s))


def modified_precision(references, hypothesis, n):
    """
    Modified precision calculation implemented with minor modifications to baseline implementation in NLTK toolkit BLEU

    Calculate modified ngram precision.
    The normal precision method may lead to some wrong translations with
    high-precision, e.g., the translation, in which a word of reference
    repeats several times, has very high precision.
    This function only returns the Fraction object that contains the numerator
    and denominator necessary to calculate the corpus-level precision.
    To calculate the modified precision for a single pair of hypothesis and
    references, cast the Fraction object into a float.
    :param references: list of reference texts (originals and human written)
    :param hypothesis: hypothesis text split list (generated by LSTM-RNN system)
    :param n: n-gram order (value of n in n-gram)
    :return: BLEU's modified precision for n-gram.
    """
    # Extracts all ngrams in hypothesis
    # Set an empty Counter if hypothesis is empty.
    counts = Counter(ngrams(hypothesis, n)) if len(hypothesis) >= n else Counter()
    # Extract a union of references' counts.
    # max_counts = reduce(or_, [Counter(ngrams(ref, n)) for ref in references])
    max_counts = {}
    for reference in references:
        reference_counts = Counter(ngrams(reference, n)) if len(reference) >= n else Counter()
        for ngram in counts:
            max_counts[ngram] = max(max_counts.get(ngram, 0),
                                    reference_counts[ngram])

    # Assigns the intersection between hypothesis and references' counts.
    clipped_counts = {ngram: min(count, max_counts[ngram])
                      for ngram, count in counts.items()}

    numerator = sum(clipped_counts.values())
    # Ensures that denominator is minimum 1 to avoid ZeroDivisionError.
    # Usually this happens when the ngram order is > len(reference).
    denominator = max(1, sum(counts.values()))

    return Fraction(numerator, denominator)


def evaluate_nlg(evaluation_file, reference_file='training/1.txt', N=5, beta=0):
    """
    Compute evaluation score based of NIST evaluation metrics for machine translation
    Brevity factor = e^{beta * log ^ 2(min(1, L_sys / L_ref)}
    N-gram score = sum (n = 1 to N) {sum (all n-grams [w_1 .. w_n]) Info([w_1 .. w_n]] / sum (all n-grams [w_1 .. w_n])}
    Score = N-gram score * brevity factor
    :param evaluation_file: Text for evaluation
    :param reference_file: File with human generated reference text
    :param N: Maximum n-gram size, by default 5
    :param beta: Brevity penalty factor, by default 0
    :return: Evaluated score for file
    """

    global reference_data

    with io.open(evaluation_file, 'r', encoding='utf-8') as evaluation:
        evaluation_data = evaluation.read().encode('ascii', errors='ignore')
        evaluation_data = pre_process(evaluation_data).split()

    with io.open(reference_file, 'r', encoding='utf-8') as reference:
        reference_data = reference.read().encode('ascii', errors='ignore')
        reference_data = pre_process(reference_data)

    n = 1000
    reference_data = [reference_data[i:i + n].split() for i in range(0, len(reference_data), n)]

    return modified_bleu(reference_data, evaluation_data)


if __name__ == '__main__':
    modified_bleu_score = evaluate_nlg(evaluation_file='result.txt', reference_file='training/4-mod.txt')
    print "Against test set: ", modified_bleu_score
