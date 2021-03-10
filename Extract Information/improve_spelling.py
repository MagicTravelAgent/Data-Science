from Levenshtein import distance as lev
import re

input_text = "Adreskantoor-Leeuwarden.  ordt gevraagd : Eene BOVEN-VOOR-  of ONDERKAMER, voor menschen zon: der Kinderen. Adres franco, onder letter G, aan J. BALT, Noorderweg , Leeuwarden.  TE HUUR:  Een rojjaal INTREK, op 12 Mei e. k. te aanvaarden, op een der beste stanmden en in het midden der stad gelegen; benevens een KELDER , dadelijk te aan vaarden.  Adres franco, onder letter Z, nan J. BALT, Noorderweg ‚ Leeuwarden.  BAKKERIJ GEVRAAGD.  Wordt gevraagd , uit de hand TE KOOP of TE BUUR: Eene BAKKERIJ, op 12 Mei e. k., op een dorp in Friesland. Adres franco, onder de letters K K, met opgaaf van prijs, aan J. BALT, Noorderweg , Leeuwarden.  9 ï P Dames! Opregt! Een JONG MENSCH, P. G., 26 jaren oud, van woed uiterlijk en eene fatsoenlijke en zelf- standige betrekking bekleedende, verlangt in kennis te komen met een fatsoenlijk , bij voor- keur gefortuneerd MEISJE , van ongeveer ge- lijken leeftijd ‚ om , na wederzijdsch goedvinden, een wettig huwelijk aan te gaan. Var geheimhouding kan men stellig verzekert zijn. Geteekende brieven, liefst met bijvoeging van Portret, worden franco ingewacht, onder de letters A Z, bij J. BALT, aan den Noorder- weg te Leeuwarden. Brieveu en Portret worden teruggezonden.  Keukenmeid.  Wordt tegen Mei gevraagd, op een groot Dorp: Eene flinke KEUKENMEID, liefst eene die gewoon is buiten te dienen. Het is een klein gezin, waar eene tweede Meid voor binnen is. Het loon naar bekwaamheid en deugden  Adres franco , onder letter O, bij J. BALT, Noerderweg , Leeuwarden.        ene fatsoenlijke BURGER DOCHTER, oud  Y 20 jaren, zoekt eene betrekking als BIN- NENMEID, of tot adsistentie in eene huishou- ding met of zonder Kinderen, kunnende goede getuigschriften overleggen. Brieven franco, onder de letters A K, aan J. BALT, Leeuwarden.  f 2000.  Bovengemelde som wordt, liefst dadelijk , voor 3 jaren gevraagd tegen goede rente en solide borgtocht. Franco brieven, onder letter P, aan J. BALT , Noorderweg, Leeuwarden.  Kleermakers,  die op billijke voorwaarden grondig onder- rigt verlangen Iín de SNEDE , adresseren zich, met franco brieven, onder het motto „beter Kunst dan Geld” , aan J. BALT, Noorderweg , Leeuwarden  ì llegistràtie.  Ten kantore van Registratie voor de Geregte- lijke Akten te Leeuwarden wordt verlangd een KLERK, die met de werkzaamheden niet ou- bekend is. Brieven franeo."

#Define a function that restores punctuation and capital usage after a word has been replaced by a word from the spelling list
def restore_caps_and_punctuation(new_word,original_word):
    if original_word.isupper():
        return new_word.upper()
    elif original_word[0].isupper():
        return new_word[0].upper() + new_word[1:]
    return new_word

#Define a function to calculate Levenshtein distances for a list of words and pick the word with the lowest Levenshtein distance
#Both of these functions will be used later in the script
def determine_most_similar_word(preprocessed_word,original_word):
    lev_dists = {}
    for word_from_list in wordlist.keys():
        lev_dists[word_from_list] = lev(word_from_list, preprocessed_word)
    min_dist = min(lev_dists.values())
    replacement_candidates = [word for word in lev_dists if lev_dists[word] == min_dist]
    word_to_replace = ""
    if len(replacement_candidates) < 2:
        word_to_replace = replacement_candidates[0]
    else:
        #If multiple replacement candidates are found, use word frequency information to find the most suitable replacement
        freq = -1
        for cand in replacement_candidates:
            if int(wordlist[cand]) > freq:
                freq = int(wordlist[cand])
                word_to_replace = cand

    #Any capitals and punctuation present in the original word should be added in the word to be replaced
    return restore_caps_and_punctuation(word_to_replace, original_word)


#Here is where Python actually starts executing stuff
#Read (1) a list of correctly spelled words and (2) a list of word frequencies (based on CGN, a Corpus of Spoken Dutch)
wordlist = {}
with open("wordlist.txt") as wordlist_file:
    for line in wordlist_file:
        wordlist[line.strip()] = 0
with open("word_frequencies.txt", encoding="ISO-8859-1") as freq_file:
    for line in freq_file:
        try:
            _, total, token = line.strip().split(maxsplit=2)
            wordlist[token] = total
        except ValueError:
            pass


#Compare words from the input_text to the word list and, if a word is not in the list, replace it by the closest word that is
#First off, combine words that have been cut off at the end of a line (indicated by a - sign)
input_text = re.sub("-( )+","",input_text)

#Split the text into parts, and keep only those parts that are not empty
words = input_text.split(" ")
words = [word for word in words if len(word) > 0]

#Iterate over the list of words
for index in range(len(words)):
    #Make lowercase and remove interpunction etc.
    word = re.sub("[^\w\d-]","",words[index].lower())

    #Don't bother with words consisting only of numbers
    if all(char in "012345789" for char in word):
        continue

    #Check if word is already spelled correctly
    if word not in wordlist.keys():
        #If the word contains "-", correct the individual parts
        #If the word does not contain "-", correct the entire word at once
        if "-" in word:
            compound_parts = re.split("-",word)
            for i in range(len(compound_parts)):
                if compound_parts[i] not in wordlist.keys():
                    compound_parts[i] = determine_most_similar_word(compound_parts[i],re.split("-",words[index])[i])
                else:
                    compound_parts[i] = restore_caps_and_punctuation(compound_parts[i],re.split("-",words[index])[i])
            words[index] = '-'.join(compound_parts)
        else:
            words[index] = determine_most_similar_word(word,words[index])


#Rebuild the list of word tokens back into a string
output_text = ""
for word in words:
    output_text += word + " "
print(output_text)