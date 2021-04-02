from Levenshtein import distance as lev
import re
import os

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


# Define a function that restores punctuation and capital usage after a word has been replaced by a word from the spelling list
def restore_caps_and_punctuation(new_word, original_word):
    try:
        if original_word.isupper():
            return new_word.upper()
        elif original_word[0].isupper():
            return new_word[0].upper() + new_word[1:]
        return new_word
    except IndexError as ex:
        print(ex)
        return ""


# Define a function to calculate Levenshtein distances for a list of words and pick the word with the lowest Levenshtein distance
# Both of these functions will be used later in the script
def determine_most_similar_word(preprocessed_word, original_word):
    lev_dists = {}
    for word_from_list in wordlist.keys():
        lev_dists[word_from_list] = lev(word_from_list, preprocessed_word)
    min_dist = min(lev_dists.values())
    replacement_candidates = [word for word in lev_dists if lev_dists[word] == min_dist]
    word_to_replace = ""
    if len(replacement_candidates) < 2:
        word_to_replace = replacement_candidates[0]
    else:
        # If multiple replacement candidates are found, use word frequency information to find the most suitable replacement
        freq = -1
        for cand in replacement_candidates:
            if int(wordlist[cand]) > freq:
                freq = int(wordlist[cand])
            word_to_replace = cand

    # Any capitals and punctuation present in the original word should be added in the word to be replaced
    return restore_caps_and_punctuation(word_to_replace, original_word)


# Read (1) a list of correctly spelled words and (2) a list of word frequencies (based on CGN, a Corpus of Spoken Dutch)
wordlist = {}
with open(os.path.join(THIS_FOLDER, 'wordlist.txt')) as wordlist_file:
    for line in wordlist_file:
        wordlist[line.strip()] = 0
with open(os.path.join(THIS_FOLDER, "word_frequencies.txt"), encoding="ISO-8859-1") as freq_file:
    for line in freq_file:
        try:
            _, total, token = line.strip().split(maxsplit=2)
            wordlist[token] = total
        except ValueError:
            pass


# Compare words from the input_text to the word list and, if a word is not in the list, replace it by the closest word that is
def improve_spelling(input_text):
    # First off, combine words that have been cut off at the end of a line (indicated by a - sign)
    input_text = re.sub("-( )+", "", input_text)

    # Split the text into parts, and keep only those parts that are not empty
    words = input_text.split(" ")
    words = [word for word in words if len(word) > 0]

    # Iterate over the list of words
    for index in range(len(words)):
        # Make lowercase and remove interpunction etc.
        word = re.sub("[^\w\d-]", "", words[index].lower())

        # Don't bother with words consisting only of numbers
        if all(char in "012345789" for char in word):
            continue

        # Check if word is already spelled correctly
        if word not in wordlist.keys():
            # If the word contains "-", correct the individual parts
            # If the word does not contain "-", correct the entire word at once
            if "-" in word[1:-1]:
                compound_parts = re.split("-", word)
                for i in range(len(compound_parts)):
                    if compound_parts[i] not in wordlist.keys():
                        compound_parts[i] = determine_most_similar_word(compound_parts[i],
                                                                        re.split("-", words[index])[i])
                    else:
                        compound_parts[i] = restore_caps_and_punctuation(compound_parts[i],
                                                                         re.split("-", words[index])[i])
                words[index] = '-'.join(compound_parts)
            else:
                words[index] = determine_most_similar_word(word, words[index])

    # Rebuild the list of word tokens back into a string
    output_text = ""
    for word in words:
        output_text += word + " "
    return output_text
