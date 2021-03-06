from Levenshtein import distance as lev
import re
import os
import time
import automata


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
def determine_most_similar_word_old(preprocessed_word, original_word):
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


def determine_most_similar_word_new(preprocessed_word, original_word):
    # Use a script found online to find all words with a Levenshtein distance of 2 or less
    m = automata.Matcher(raw_words)
    replacement_candidates = list(automata.find_all_matches(preprocessed_word, 2, m))

    #No additional steps required for short lists
    if len(replacement_candidates) == 0:
        return original_word
    if len(replacement_candidates) == 1:
        return restore_caps_and_punctuation(replacement_candidates[0],original_word)

    #For longer lists, use frequency information to find the most suitable replacement
    #However, the list contains words with a Levenshtein distance of 1 as well as 2, so take the distance into account as well
    word_to_replace = ""
    freq = -1
    lev_repl = 10
    for cand in replacement_candidates:
        lev_cand = lev(cand, preprocessed_word)

        if lev_cand < lev_repl:
            freq = int(wordlist[cand]) if cand in wordlist else 0
            word_to_replace = cand
            lev_repl = lev_cand
        elif lev_cand == lev_repl and cand in wordlist and int(wordlist[cand]) > freq:
            freq = int(wordlist[cand])
            word_to_replace = cand
            lev_repl = lev_cand
    return restore_caps_and_punctuation(word_to_replace, original_word)


# Read (1) a list of correctly spelled modern words, (2) a list of correctly spelled old words,
# and (3) a list of word frequencies (based on CGN, a Corpus of Spoken Dutch)
with open('wordlist.txt') as wordlist_file:
    wordlist = {line.strip().lower():0 for line in wordlist_file}
with open('wordlist_old.txt') as wordlist_file:
    wordlist_old = [line.strip().lower() for line in wordlist_file]
with open("word_frequencies.txt", encoding="ISO-8859-1") as freq_file:
    for line in freq_file:
        try:
            _, total, token = line.strip().split(maxsplit=2)
            wordlist[token.lower()] = total
        except ValueError:
            pass
    wordlist.pop("token")
raw_words = sorted(list(wordlist.keys()) + wordlist_old)


# Compare words from the input_text to the word list and, if a word is not in the list, replace it by the closest word that is
def improve_spelling(input_text, similarity_func=determine_most_similar_word_new):
    # Split the text into parts and keep track of where the newlines are
    lines = list(input_text.partition("\n"))
    while lines[-2] != "":
        lines += lines.pop(-1).partition("\n")
    words = []
    for line in lines:
        words += line.split(" ")
    words = [word for word in words if word]

    # Iterate over the list of words
    for index in range(len(words)):
        # Skip newlines
        if words[index] == "\n":
            continue

        # Check if the word is in the list of old/new correctly spelled words (before pre-processing)
        # This will be done once before and once after pre-processing, because of issues with punctuation marks etc.
        if words[index].lower() in wordlist or words[index].lower() in wordlist_old:
            continue

        # Skip acronyms (because not all of them are included in our wordlist)
        # We consider a word an acronym if it ends in "." and the word that follows it does not start with a capital letter
        if words[index].endswith(".") and index + 1 < len(words) and words[index + 1][0].islower():
            continue

        # Make lowercase and remove interpunction etc.
        word = re.sub("[^\w\d-]", "", words[index].lower())

        # Skip words consisting only of numbers
        if all(char in "0123456789/" for char in word):
            continue

        # Turn unicode ĳ into ij so the spell checker does not get confused
        word = re.sub("ĳ","ij",word)

        # Now that pre-processing is done, check again if the word is in the list of old/new correctly spelled words
        if words[index] in wordlist or words[index] in wordlist_old:
            continue

        # It's not in the lists? Time for a correction
        # If the word contains "-", correct the individual parts
        # If the word does not contain "-", correct the entire word at once
        if "-" in word[1:-1]:
            compound_parts = re.split("-", word)
            for i in range(len(compound_parts)):
                if compound_parts[i] not in wordlist.keys():
                    compound_parts[i] = similarity_func(compound_parts[i],re.split("-", words[index])[i])
                else:
                    compound_parts[i] = restore_caps_and_punctuation(compound_parts[i],
                                                                        re.split("-", words[index])[i])
            words[index] = '-'.join(compound_parts)
        else:
            words[index] = similarity_func(word, words[index])

    # Rebuild the list of word tokens back into a string
    output_text = ""
    for word in words:
        if word == "\n":
            output_text += "\n"
        else:
            output_text += word + " "
    return output_text

def _hours(seconds):
    return int(seconds / 60 / 60)

def _minutes(seconds):
    return int((seconds / 60) % 60)

def _seconds(seconds):
    return int(seconds % 60)


def _test_script(filename):
    starttime = time.time()
    with open(filename) as input_file:
        text = input_file.read()
    text_improved = improve_spelling(text,determine_most_similar_word_old)
    time_elapsed = time.time() - starttime
    print("Took %d:%d:%d to correct the text using the old method, ending up with this corrected text:\n%s" % (_hours(time_elapsed),_minutes(time_elapsed),_seconds(time_elapsed),text_improved))

    starttime = time.time()
    text_improved = improve_spelling(text, determine_most_similar_word_new)
    time_elapsed = time.time() - starttime
    print("Took %d:%d:%d to correct the text using the new method, ending up with this corrected text:\n%s" % (_hours(time_elapsed), _minutes(time_elapsed), _seconds(time_elapsed), text_improved))

if __name__ == '__main__':
    _test_script("./OCR2/entry_3_full.txt")
#Old method took 1 minute and 50 seconds to read entry_3_full.txt on Astraeas pc
#New method took 0 minutes and 18 seconds to read entry_3_full.txt on Astraeas pc