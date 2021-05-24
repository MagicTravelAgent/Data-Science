# -*- coding: utf-8 -*-
# imports
try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract as pt
import re
import glob
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
import csv
import math
from Levenshtein import distance as lev
import os
import automata
import numpy as np
import pandas as pd
import time
import io


# class for extractor
class Extractor:

    # class constructor
    def __init__(self):
        # file location definitions
        # Image download path
        self.image_download_path = "Images/"

        # Metadata download path
        self.metadata_download_path = "Metadata/"

        # OCR output path
        self.text_directory = "OCR/"

        # Advert output defined
        self.advert_directory = "Adverts/"

        # Final output csv directory location defined
        self.final_directory = "OCR/"

        # Download preferences
        self.download_full_images = False
        self.download_cut_out_images = True

        # Customize query
        self.query = "hypothe*"
        self.q_clean = ""

        # Customize year of appearance If all_years is True, there will be no year filtering If all_years is False
        # and specific_years is a list containing numbers, the results will be filtered for those specific years If
        # all_years is False and specific_years is empty, the results will span the range of years between min_year
        # and max_year
        self.all_years = False
        self.specific_years = [1870, 1871]
        self.min_year = 1870
        self.max_year = 1871

        # Customize date of adding the newspaper to the Delpher database
        self.all_dates = False
        self.min_date = "01-01-2016"
        self.max_date = "31-12-2021"

        # Customize article type
        # Either set article_type_All to true, or indicate preferences for individual article types
        self.article_type_All = False
        self.article_type_Advertentie = True
        self.article_type_Artikel = False
        self.article_type_Familiebericht = False
        self.article_type_Illustratie_met_onderschrift = False

        # Customize distribution area
        self.distribution_area_All = False
        self.distribution_area_Landelijk = False
        self.distribution_area_Indonesie = False
        self.distribution_area_Antillen = False
        self.distribution_area_Regionaal = True
        self.distribution_area_Suriname = False
        self.distribution_area_VS = False

        # Customize names of desired papers
        # Add the names of the papers you want to search for inside the list. If the list is empty, all papers will be included in the results
        self.paper_titles = ["Rotterdamsch nieuwsblad", "Provinciale Overijsselsche en Zwolsche courant"]

        # Customize place where the papers have been printed. If the list is empty, all papers will be included in the results
        self.paper_origins = ["Rotterdam", "Zwolle"]

        # Customize names of places who have donated their pages for the Delpher project. If the list is empty, all papers will be included in the results
        self.sources = ["Koninklijke Bibliotheek", "Gemeentearchief Rotterdam", "Historisch Centrum Overijssel"]

        # Read:
        # (1) a list of correctly spelled modern words
        # (2) a list of correctly spelled old words
        # (3) a list of word frequencies (based on CGN, a Corpus of Spoken Dutch)
        with open('Wordslist/wordlist.txt') as wordlist_file:
            self.wordlist = {line.strip().lower(): 0 for line in wordlist_file}
        with open('Wordslist/wordlist_old.txt') as wordlist_file:
            self.wordlist_old = [line.strip().lower() for line in wordlist_file]
        with open("Wordslist/word_frequencies.txt", encoding="ISO-8859-1") as freq_file:
            for line in freq_file:
                try:
                    _, total, token = line.strip().split(maxsplit=2)
                    self.wordlist[token.lower()] = total
                except ValueError:
                    pass
            self.wordlist.pop("token")
        self.raw_words = sorted(list(self.wordlist.keys()) + self.wordlist_old)

        # Creating the directories should they not exist already:
        dir_list = [self.image_download_path, self.metadata_download_path, self.text_directory, self.advert_directory]
        [self.make_dir(x) for x in dir_list]

        # Alright, you're good to go!

    def make_dir(self, dir):
        if not os.path.exists(dir):
            os.makedirs(dir)

    def is_valid(self, url):
        """
        Checks whether `url` is a valid URL.
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def get_image_and_metadata(self, url):
        """
        Returns the image URL on a Delpher result page and the associated metadata
        """
        soup = bs(requests.get(url).content, "html.parser")
        paper_name = ""
        paper_date = ""

        # Collect metadata from page
        paper_names = [span.text.strip() for span in soup.find_all("span") if
                       str(span.attrs.get("class")) != "None" and len(span.attrs.get("class")) > 0 and
                       span.attrs.get("class")[0] == "object-view-top-block__heading-content"]
        if len(paper_names) > 0:
            paper_name = paper_names[0]
        paper_dates = [li.text.strip() for li in soup.find_all("li") if
                       str(li.attrs.get("class")) != "None" and len(li.attrs.get("class")) > 2 and
                       li.attrs.get("class")[2] == "object-view-top-block__metadata-subtitle--date"]
        if len(paper_dates) > 0:
            paper_date = paper_dates[0]

        # Find newspaper image
        for img in soup.find_all("img"):
            img_url = img.attrs.get("src")
            if not img_url:
                # if img does not contain src attribute, it cannot be the image we are looking for
                continue
            # make the URL absolute by joining domain with the URL that is just extracted
            img_url = urljoin(url, img_url)
            # Collect metadata information from URL
            keywords = re.sub(r"^.*words=([^&]+)&.*$", r"\1", img_url)
            for pattern in [("%28", ""), ("%29", ""), ("%2A", "*")]:
                keywords = re.sub("%s" % pattern[0], "%s" % pattern[1], keywords)
            keywords = re.split("\+", keywords)
            # Remove highlights
            img_url_cut_out = re.sub("words=[^&]+&", "", img_url)
            # Remove the 's', 'h', 'w', 'x' and 'y' attributes to obtain the full image instead of a cut out part
            img_url_full = re.sub("&[shxyw]=[^&]+", "", img_url_cut_out)
            # finally, if the urls are valid
            if self.is_valid(img_url_cut_out) and self.is_valid(img_url_full):
                return [img_url_cut_out, img_url_full, keywords, paper_name, paper_date]
        return []

    def download(self, url, pathname, filename):
        """
        Downloads a file given an URL and puts it in the folder `pathname` under the name of 'filename'
        """
        # if path doesn't exist, make that path dir
        if not os.path.isdir(pathname):
            os.makedirs(pathname)
        # download the body of response by chunk, not immediately
        response = requests.get(url, stream=True)
        # get the file name
        filename = os.path.join(pathname, filename)
        # write data read to the file
        with open(filename, "wb") as f:
            for data in response.iter_content(1024):
                f.write(data)

    def create_query_URL(self):
        """
        Create a Delpher search URL based on the search a user wants to make
        """
        php_variables = []

        # Add query
        if self.query:
            php_variables.append("query=" + self.query)

        # Add year of appearance
        if not self.all_years:
            if not self.specific_years:
                # Create a list of specific years using the date range
                specific_years_list = [year + self.min_year for year in range(self.max_year - self.min_year + 1)]
            else:
                specific_years_list = self.specific_years
            for year in specific_years_list:
                php_variables.append("facets[periode][]=2|%de_eeuw|%d-%d|%d|" % (
                    math.ceil(year / 100), int(year / 10) * 10, int(year / 10) * 10 + 9, year))

        # Add article type
        if not self.article_type_All:
            if self.article_type_Advertentie:
                php_variables.append("&facets[type][]=advertentie")
            if self.article_type_Artikel:
                php_variables.append("&facets[type][]=artikel")
            if self.article_type_Familiebericht:
                php_variables.append("&facets[type][]=familiebericht")
            if self.article_type_Illustratie_met_onderschrift:
                php_variables.append("&facets[type][]=illustratie+met+onderschrift")

        # Add distribution type
        if not self.distribution_area_All:
            if self.distribution_area_Antillen:
                php_variables.append("facets[spatial][]=Nederlandse+Antillen")
            if self.distribution_area_Indonesie:
                php_variables.append("facets[spatial][]=Nederlands-Indië+|+Indonesië")
            if self.distribution_area_Landelijk:
                php_variables.append("facets[spatial][]=Landelijk")
            if self.distribution_area_Regionaal:
                php_variables.append("facets[spatial][]=Regionaal|lokaal")
            if self.distribution_area_Suriname:
                php_variables.append("facets[spatial][]=Suriname")
            if self.distribution_area_VS:
                php_variables.append("facets[spatial][]=Verenigde+Staten")

        # Add titles of newspapers
        for paper_title in self.paper_titles:
            php_variables.append("facets[papertitle][]=" + re.sub("\s", "+", paper_title))

        # Add place of printing
        for paper_origin in self.paper_origins:
            php_variables.append("facets[spatialCreation][]=" + re.sub("\s", "+", paper_origin))

        # Add donation source
        for source in self.sources:
            php_variables.append("facets[sourceFacet][]=" + re.sub("\s", "+", source))

        # Add date of addition of newspapers to the Delpher database
        if not self.all_dates:
            php_variables.append(
                'cql[]=(DelpherPublicationDate+_gte_+"%s")&cql[]=(DelpherPublicationDate+_lte_+"%s")' % (
                    self.min_date, self.max_date))

        # Create URL
        URL = "https://www.delpher.nl/nl/kranten/results?"
        for php_variable in php_variables:
            URL += php_variable + "&"
        URL = URL[:-1]
        URL += "&maxperpage=50&sortfield=date&coll=ddd"

        return URL

    def get_links_from_query(self):
        """
        Traverse through the pages listing the results found by Delpher, and collect the links to pages with individual results
        """

        # Create search URL
        url = self.create_query_URL()
        # Process URL
        soup = bs(requests.get(url).content, "html.parser")
        # Figure out the number of result pages by checking the total number of results and dividing it by 50
        possible_numbers_of_results = [span.text for span in soup.find_all("span") if
                                       str(span.attrs.get("id")) != "None" and span.attrs.get(
                                           "id") == "js-searchtip__numberOfResults"]
        if len(possible_numbers_of_results) < 1:
            return []
        num_results = int(possible_numbers_of_results[0])
        num_pages = math.ceil(num_results / 50)

        # For each page with 50 (or less) results, collect the links to each individual result and put them into an array
        results_links = []
        for page_number in tqdm(range(num_pages), "Gathering results"):
            # Load new page
            soup = bs(requests.get(url + "&page=%d" % (page_number + 1)).content, "html.parser")
            # Find links
            for link in soup.find_all("a"):
                result_url = link.attrs.get("href")
                # Is this a link to a result page?
                if not result_url or not result_url.startswith("/nl/kranten/view"):
                    continue
                # Make the url absolute
                result_url = urljoin(url, result_url)
                # finally, if the url is valid, it can be added to the array
                if self.is_valid(result_url) and result_url not in results_links:
                    results_links.append(result_url)
        return results_links

    def remove_leading_zeroes(self, number):
        """
        Removes leading zeroes from month and day numbers ("04" -> "4", "12" -> "12")
        """
        if len(number) > 1 and number[0] == "0":
            return number[1:]
        return number

    def split_date(self, date_string):
        """
        Split Delpher's full date strings into separate pieces of date-related information
        """
        return (date_string[0:2],
                self.remove_leading_zeroes(date_string[0:2]),
                date_string[3:5],
                self.remove_leading_zeroes(date_string[3:5]),
                date_string[6:10])

    def create_accompanying_csv(self, imgs, query_clean):
        """
        Write metadata to a file
        """
        with open(self.metadata_download_path + "%s_metadata.csv" % query_clean, "w") as output_file:
            csv_writer = csv.writer(output_file)
            csv_writer.writerow(
                ["Result ID", "Titel", "Dag", "DAG", "Maand", "MAAND", "Jaar", "URL full", "URL cut out", "keywords"])
            for img_data in imgs.items():
                day, DAY, month, MONTH, year = self.split_date(img_data[1][4])
                csv_writer.writerow(
                    [img_data[0], img_data[1][3], day, DAY, month, MONTH, year, img_data[1][1], img_data[1][0],
                     img_data[1][2]])

    def run_query_to_image(self):
        images_info = {}
        # Create a custom query and gather the links associated with the results
        links = self.get_links_from_query()
        if not links:
            print("Could not find any results :( Did you make a spelling error somewhere?")
            return
        # Let's not assume that the user is okay with downloading 4.000.000 images
        max_number = input(
            "Found %d articles that matched your search query! How many do you want to download? (Please type in your answer below and press Enter)\n" % len(
                links))
        if int(max_number) < len(links):
            links = links[:int(max_number)]
        for index in tqdm(range(len(links)), "Collecting image urls and newspaper metadata"):
            # for each page link, collect the links to the full and cut out versions of the image shown on that page, as well as any corresponding metadata that can be detected
            info = self.get_image_and_metadata(links[index])
            if info:
                # add url and metadata info to the image info list
                images_info["%d" % (index + 1)] = info
        # create a version of the query without wildcards, because Windows does not like filenames with those characters in it
        query_clean = re.sub("[.*]", "", self.query)
        self.q_clean = query_clean
        for item in tqdm(images_info.items(), "Downloading images"):
            # for each image, download the versions that the user wants downloaded
            if self.download_cut_out_images:
                self.download(item[1][0], self.image_download_path,
                              "%s_result_%s_cut_out.jpeg" % (query_clean, item[0]))
            if self.download_full_images:
                self.download(item[1][1], self.image_download_path, "%s_result_%s_full.jpeg" % (query_clean, item[0]))
        if links:
            # Write the collected metadata to a csv file
            self.create_accompanying_csv(images_info, query_clean)
        print("Images Downloaded!")

    # method for image to text
    def ocr_images(self):

        # Going through each of the images in the download folder
        for image_filename in glob.glob(self.image_download_path + "\*.jpeg"):
            print("Transcribing image:", image_filename)
            try:
                # ocr the file using tesseract
                text = pt.image_to_string(Image.open(image_filename), lang='nld')

                # creating the file destination
                f_dest = image_filename.replace(self.image_download_path[:-1], self.text_directory[:-1])
                f_dest = f_dest.replace(".jpeg", ".txt")

                # with the created destination write the text using utf-8 in case of special characters
                with open(f_dest, "w", encoding="utf-8") as f:
                    f.write(text)
                    f.close()

            # should there be a problem with the image relay this to the user
            except Exception as ex:
                print("Image OCR failed on", image_filename)
                print(ex)

    # function to extract the advert from the text
    def extract_advert(self):

        output_file = open(self.advert_directory + "img_ocr.csv", "w")
        csv_writer = csv.writer(output_file)

        csv_writer.writerow(
            ["ID_CVB2", "ID_CVB", "IDv2", "ID", "Titel", "Dag", "DAG", "Maand", "MAAND", "Jaar", "Type", "Type_Detail",
             "Soort Transactie", "Vraag/Aanbod", "Detail", "Contact", "Beroep", "Locatie_Contact", "Handelt namens",
             "Advertentie_Opmerking", "Bedragen", "Bedrag_range_minimum", "Bedrag_range_maximum", "Reden", "Onderpand",
             "Locatie_Onderpand", "Loan-to-value", "Tegenpartij_Voorkeur", "Aflossing", "Rente", "Moment",
             "Hypotheek_Opmerking", "URL", "tblResultaatMetadatakey", "OCR"])

        # taking all of the filenames from downloaded images and putting them into a list
        filenames = glob.glob(self.text_directory + "\*.txt")
        filenames.sort()
        for filename in filenames:
            print("Opening %s..." % (filename))
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read()
                f.close()

            # splitting the text of the advert by newline + space as tesseract seems to seperate paragraphs lie this
            text = text.split("\n ")

            # the regular expression used to find the advert
            # TODO look at using the same regular expression used in the queries
            reg = ".*ypothe+.*"
            # reg = "^.*(" \
            #       "(?= 1e )(?= hypothe)|" \
            #       "(?= 1ste )(?= hypothe)|" \
            #       "(?= a[^ ]*ngebo[^ ]*den )(?= onderpa)|" \
            #       "(?= b[^ ]*sch[^ ]*kba[^ ]*r )(?= tegen )(?= rente)|" \
            #       "(?= bil[^ ]*k)(?= rente)|" \
            #       "(?= Bouwfonds)|" \
            #       "(?= eerste)(?= hypothe)|" \
            #       "(?= Eerste)(?= schepenke)|" \
            #       "(?= genoeg )(?= overwa[^ ]*rde)|" \
            #       "(?= gevr[^ ]*g)(?= onderpa)|" \
            #       "(?= gevr[^ ]*g)(?= tegen )(?= rente)|" \
            #       "(?= gez[^ ]*ht )(?= tegen )(?= rente)|" \
            #       "(?= gezocht )(?= onderpa)|" \
            #       "(?= grond[^ ]*red[^ ]*t)|" \
            #       "(?= hyp. )(?= verban)|" \
            #       "(?= hypoth)(?= b[^ ]*sch[^ ]*kba[^ ]*r )|" \
            #       "(?= hypothe[^ ]*b)|" \
            #       "(?= Hypothe[^ ]*r )(?= verban)|" \
            #       "(?= Ie )(?= hypothe)|" \
            #       "(?= Iste )(?= hypothe)|" \
            #       "(?= le )(?= hypothe)|" \
            #       "(?= leen )(?= onderpa)|" \
            #       "(?= leen )(?= tegen )(?= rente)|" \
            #       "(?= lste )(?= hypothe)|" \
            #       "(?= mak[^ ]*el[^ ]*r )(?= hypoth)|" \
            #       "(?= notaris )(?= hypothe)|" \
            #       "(?= onderpa)(?= aanwe[^ ]*ig )|" \
            #       "(?= onderpa)(?= overwa[^ ]*rde)|" \
            #       "(?= Pandbrie)|" \
            #       "(?= ru[^ ]*me)(?= overwa[^ ]*rde)|" \
            #       "(?= secuur )(?= onderpa)|" \
            #       "(?= soli[^ ]*d)(?= onderpa)|" \
            #       "(?= vold[^ ]*nde)(?= overwa[^ ]*rde)" \
            #       ").*$"

            match = ""
            for i in text:
                # x = re.search(reg, i.replace("\n", " "))
                x = re.search(reg, i, re.IGNORECASE)
                if x:
                    match += i
            if match == "":
                print("match empty, improving spelling for better match?")
                for i in text:
                    i = self.improve_spelling(i)
                    # x = re.search(reg, i.replace("\n", " "))
                    x = re.search(reg, i, re.IGNORECASE)
                    if x:
                        print("match found in improved spelling")
                        match += i
            else:
                print("match not empty")
                match = self.improve_spelling(match)

            # writing the match into the csv for the adverts
            csv_writer.writerow(
                ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
                 "", "",
                 "", "", "", "", "", "", match])

            with open(filename.replace(self.text_directory[:-1], self.advert_directory[:-1]), "w",
                      encoding="utf-8") as f:
                f.write(match)
                f.close()

        output_file.close()

    # Define a function that restores punctuation and capital usage after a word has been replaced by a word from the spelling list
    def restore_caps_and_punctuation(self, new_word, original_word):
        try:
            if original_word.isupper():
                return new_word.upper()
            elif original_word[0].isupper():
                return new_word[0].upper() + new_word[1:]
            return new_word
        except IndexError as ex:
            print(ex)
            return ""

    # finding the word that the miss-spelled word most probably is
    def determine_most_similar_word(self, preprocessed_word, original_word):
        # Use a script found online to find all words with a Levenshtein distance of 2 or less
        m = automata.Matcher(self.raw_words)
        replacement_candidates = list(automata.find_all_matches(preprocessed_word, 2, m))

        # No additional steps required for short lists
        if len(replacement_candidates) == 0:
            return original_word
        if len(replacement_candidates) == 1:
            return self.restore_caps_and_punctuation(replacement_candidates[0], original_word)

        # For longer lists, use frequency information to find the most suitable replacement
        # However, the list contains words with a Levenshtein distance of 1 as well as 2, so take the distance into account as well
        word_to_replace = ""
        freq = -1
        lev_repl = 10
        for cand in replacement_candidates:
            lev_cand = lev(cand, preprocessed_word)

            if lev_cand < lev_repl:
                freq = int(self.wordlist[cand]) if cand in self.wordlist else 0
                word_to_replace = cand
                lev_repl = lev_cand
            elif lev_cand == lev_repl and cand in self.wordlist and int(self.wordlist[cand]) > freq:
                freq = int(self.wordlist[cand])
                word_to_replace = cand
                lev_repl = lev_cand
        return self.restore_caps_and_punctuation(word_to_replace, original_word)

    # Compare words from the input_text to the word list and, if a word is not in the list, replace it by the closest word that is
    def improve_spelling(self, input_text):
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
            if words[index].lower() in self.wordlist or words[index].lower() in self.wordlist_old:
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
            word = re.sub("ĳ", "ij", word)

            # Now that pre-processing is done, check again if the word is in the list of old/new correctly spelled words
            if words[index] in self.wordlist or words[index] in self.wordlist_old:
                continue

            # It's not in the lists? Time for a correction
            # If the word contains "-", correct the individual parts
            # If the word does not contain "-", correct the entire word at once
            if "-" in word[1:-1]:
                compound_parts = re.split("-", word)
                for i in range(len(compound_parts)):
                    if compound_parts[i] not in self.wordlist.keys():
                        compound_parts[i] = self.determine_most_similar_word(compound_parts[i],
                                                                             re.split("-", words[index])[i])
                    else:
                        compound_parts[i] = self.restore_caps_and_punctuation(compound_parts[i],
                                                                              re.split("-", words[index])[i])
                words[index] = '-'.join(compound_parts)
            else:
                words[index] = self.determine_most_similar_word(word, words[index])

        # Rebuild the list of word tokens back into a string
        output_text = ""
        for word in words:
            if word == "\n":
                output_text += "\n"
            else:
                output_text += word + " "
        return output_text

    # function to add information to the csv
    def add_information(self, row, rowindex, information):
        if information != "":
            information = information.strip()
            if row[rowindex] == "":
                row[rowindex] = information
            else:
                if information not in row[rowindex].split("; "):
                    row[rowindex] += "; " + information

    # method for advert to information
    def extract_information(self):
        # open the input csv and output csv
        with open(self.advert_directory + "img_ocr.csv") as input_file:
            with open(self.final_directory + "img_ocr_data.csv", "w", encoding="utf-8") as output_file:
                csv_reader = csv.reader(input_file)
                csv_writer = csv.writer(output_file)

                # check the ocr from each row for indications of certain information
                for row in csv_reader:
                    if len(row) > 34:
                        if row[34] != "OCR":
                            ocr = row[34]
                            ocr_lower = ocr.lower()

                            # Search for indications of type (column K/L)
                            if re.search("bank", ocr_lower, re.IGNORECASE):
                                self.add_information(row, 10, "Instelling")
                                self.add_information(row, 11,
                                                     re.sub(r"^.*?([\w]*bank).*$", r"\1", ocr, flags=re.IGNORECASE))
                            elif re.search("verko[o]?p", ocr_lower, re.IGNORECASE):
                                self.add_information(row, 10, "Verkoop en Hypotheek")
                                self.add_information(row, 12, "hypotheek")
                                self.add_information(row, 13, "aanbod")
                            else:
                                self.add_information(row, 10, "False Positive")

                            # Indications of transaction type (column M)
                            if re.search("hypothe(ek|cair)", ocr_lower, re.IGNORECASE):
                                self.add_information(row, 12, "hypotheek")
                            if re.search("pandbrie", ocr_lower, re.IGNORECASE):
                                self.add_information(row, 12, "pandbrief")
                            if re.search("obligati", ocr_lower, re.IGNORECASE):
                                self.add_information(row, 12, "Obligaties")
                            if re.search("gevraagd", ocr_lower, re.IGNORECASE):
                                self.add_information(row, 12, "Lening")
                                self.add_information(row, 13, "vraag")

                            # Indications of supply/demand (column N)
                            if re.search("gee(ft|ven) uit|verstrek", ocr_lower, re.IGNORECASE):
                                self.add_information(row, 13, "aanbod")

                            # Indications of details (column O)
                            # for some reason these often seem to contain the word "kan"
                            # also this doesn't seem to be working yet
                            if re.search("^(\. )?([A-Z][^.]* kan [^.]*\.)( [A-Z].*)?$", ocr, re.IGNORECASE):
                                self.add_information(row, 14,
                                                     re.sub(r"^(\. )?([A-Z][^.]* kan [^.]*\.)( [A-Z].*)?$", r"\1", ocr))

                            # Indications of contact person (column P, Q and R)
                            for name_indicator in ["Mr\.", "den Heer", "[Ff]ranco[^.]*aan"]:
                                # search for the name indicators, and grab the 10 words that follow it
                                name_areas = re.findall(
                                    "( %s ([A-Z][^ .,]*[ .,]+)([^ .,]+[ .,]+){0,9})" % name_indicator, ocr)
                                for name_area in name_areas:
                                    # print("23: " + name_area[0])

                                    # 'te' antecedes a place. If you detect 'te', that's definitely not part of a contact person's name.
                                    if re.search(" %s .* te " % name_indicator, name_area[0], re.IGNORECASE):
                                        # Check for commas, which also signify the end of a name
                                        if re.search(" %s .*, .* te " % name_indicator, name_area[0], re.IGNORECASE):
                                            self.add_information(row, 15,
                                                                 re.sub(r"^.* %s (.*),.* te .*$" % name_indicator,
                                                                        r"\1",
                                                                        name_area[0]))
                                            # the word after the comma might be a contact person's profession
                                            self.add_information(row, 16,
                                                                 re.sub(r"^.* %s .*,(.*) te .*$" % name_indicator,
                                                                        r"\1",
                                                                        name_area[0]))
                                        else:
                                            self.add_information(row, 15,
                                                                 re.sub(r"^.* %s (.*) te .*$" % name_indicator, r"\1",
                                                                        name_area[0]))
                                        # The piece of information following just after 'te' will be considered the contact person's location
                                        # add_information(row, 17, re.sub(r"^.* te (([A-Z][A-Za-z-]*)( [A-Z][).*?$", r"\1",name_area[0])[:-1])
                                        self.add_information(row, 17, re.sub(
                                            r"^.* te (([A-Z][A-Za-z-]* )*([A-Z][A-Za-z-]*[.,])?).*?$", r"\1",
                                            name_area[0])[:-1])
                                        # print(row[17])
                                    else:
                                        # Check for commas
                                        if re.search(" %s .*," % name_indicator, name_area[0], re.IGNORECASE):
                                            self.add_information(row, 15,
                                                                 re.sub(r"^.* %s (.*?),.*$" % name_indicator, r"\1",
                                                                        name_area[0]))
                                            # without 'te', the piece of information behind the comma is more likely to be a person's location than their profession
                                            self.add_information(row, 17, re.sub(
                                                r"^.* %s .*?, (?![A-Z]\.)(([A-Z][A-Za-z-]*[ ,]+)*([A-Z][A-Za-z-]*\.)?).*?$" % name_indicator,
                                                r"\1", name_area[0])[:-1])
                                            # print(row[17])
                                        else:
                                            self.add_information(row, 15, re.sub(
                                                r"^.* %s (([A-Z][^A-Z]* |van |de([nrs])? )*).*$" % name_indicator,
                                                r"\1", name_area[0]))

                            # Indications of numbers (columns U [amounts of money], AC [repayment period] AD [interest] and AE [moment])
                            numbers = re.findall("(([^ ]+ +){0,2}[^ ]*([0-9][0-9,. /]*)?[0-9][¼½¾]?%? ([^ ]+ ){0,2})",
                                                 ocr)
                            for number in numbers:
                                # Is it interest?
                                if re.search("[Pp]ct.|[Ii]nterest|%", number[0], re.IGNORECASE):
                                    self.add_information(row, 29, re.sub(
                                        r"^.*? (((f|ƒ|fr\.|frs\.) )?[0-9]+[¼½¾]?(%| pct.)?( 'sjaars)?)([ .,]+[^ .,]*)*?$",
                                        r"\1", number[0]))
                                elif re.search(
                                        "[0-9] (januarij?|februarij?|maart|april|mei|juni|juli|augustus|september|o[ck]tober|november|december)[ ,.]",
                                        number[0], flags=re.IGNORECASE):
                                    self.add_information(row, 30,
                                                         re.sub(r"^(.+[^0-9])?([0123]?[0-9] [^ ,.]+)[ ,.].*$", r"\2",
                                                                number[0]))
                                elif re.search("in [12][0-9]{3}", number[0], re.IGNORECASE):
                                    self.add_information(row, 30, re.sub(r"^.*in ([12][0-9]{3}).*$", r"\1", number[0]))
                                elif re.search("^([^ ]* )*?(nam\. |avonds te |)[0-9]{1,2} uur[ .,]", number[0],
                                               re.IGNORECASE):
                                    self.add_information(row, 30,
                                                         re.sub(r"^([^ ]* )*?((nam\. )?[0-9]{1,2} uur)[ .,].*$", r"\2",
                                                                number[0]))
                                # Is it a (repayment) period?
                                elif re.search("(?<!oud) [0-9]+ (jaar|jaren|maanden)(?! oud)", number[0],
                                               re.IGNORECASE):
                                    self.add_information(row, 28,
                                                         re.sub(r"^.*[^0-9]([0-9]+ (jaar|jaren|maanden)).*$", r"\1",
                                                                number[0]))
                                # Is it an amount of money?
                                elif re.search(" (f|ƒ|fr.) ([0-9][0-9,./ ]*)?[0-9][ ,.]", number[0], re.IGNORECASE):
                                    self.add_information(row, 20,
                                                         re.sub(r"^.* ((f|ƒ|fr) ([0-9][0-9,./ ]*)?[0-9])[ ,.].*$",
                                                                r"\1",
                                                                number[0]))
                                elif re.search(" ([0-9][0-9,./ ]*)?[0-9] frs.[ ,.]", number[0], re.IGNORECASE):
                                    self.add_information(row, 20,
                                                         re.sub(r"^.* (([0-9][0-9,./ ]*)?[0-9] frs.)[ ,.].*$", r"\1",
                                                                number[0]))
                        csv_writer.writerow(row)

    # method to merge all output files by combining meta data csv with the output csv
    def merge(self):
        # since the metadata ids are in order we need to try and get the order of the files since this order is how they are
        # set into the output csv. We will simply take the filenames the same way we do from the info extractor
        filenames = glob.glob(self.text_directory + "\*.txt")
        filenames.sort()
        order = np.array([[int(s) for s in file.split("_") if s.isdigit()]for file in filenames])

        # now we have the order that the items are in the info extract we can attach the meta data to it
        # to do this we will read both the csv files into dataframes and then merge them
        meta_file = pd.read_csv(self.metadata_download_path + "%s_metadata.csv" % self.q_clean, encoding="utf-8")
        info_file = pd.read_csv(self.final_directory + "img_ocr_data.csv", encoding="utf-8")
        info_file["ID"] = order

        # editing the columns so that they can be merged with no conflicts
        meta_file = meta_file.rename(columns = {"Result ID": "ID"})
        info_file = info_file.drop(['Titel', 'Dag', 'DAG', 'Maand', 'MAAND', 'Jaar'], axis = 1)
        merged = meta_file.merge(info_file, on="ID")

        #writing the final csv
        merged.to_csv("extraction.csv", encoding="utf-8")


    # method to run all
    def run(self):
        # run query to image:
        self.run_query_to_image()

        # run image to text
        self.ocr_images()

        # run the extraction of the advert
        self.extract_advert()

        # run the information extraction
        self.extract_information()

        # merge all output files into one csv
        self.merge()

        print("Extraction complete :)")


# create the extractor class
# to run the extractor you need to call the run function
# all of the variables set in the constructor will be used so if you want to change the functionality edit those at the top
ext = Extractor()
ext.run()
