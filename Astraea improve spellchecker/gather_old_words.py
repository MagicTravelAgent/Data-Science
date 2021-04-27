# By creating a frequency list of words from the OCR files (before the spell checker has been run),
# we can find additional correctly spelled words that should be added to the wordlist used by the spell checker script

import glob
from collections import Counter

def collect_word_frequencies(filenames):
    words = []
    for filename in filenames:
        with open(filename) as input_file:
            for line in input_file:
                words += line.strip().lower().split()
    return Counter(words)

def read_wordlist():
    with open('../Tesseract/wordlist.txt') as wordlist_file:
        return [line.strip().lower() for line in wordlist_file]

def filter_already_known_words(c,wordlist):
    words = list(c.keys())
    for word in words:
        if word in wordlist:
            c.pop(word)
    return c

if __name__ == '__main__':
    filenames = glob.glob("../Tesseract/OCR2/entry_*_full.txt")
    c = filter_already_known_words(collect_word_frequencies(filenames),read_wordlist())
    with open("frequencies.txt","w") as output_file:
        for item in c.most_common():
            output_file.write("%s: %d\n" % (item[0], item[1]))