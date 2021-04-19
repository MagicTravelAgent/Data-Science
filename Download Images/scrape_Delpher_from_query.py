#Code shown here has been copied and adapted from https://www.thepythoncode.com/article/download-web-page-images-python

import requests
import os
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
import re
import csv
import math

#In order to use this script, make sure all of the above libraries are installed, edit the below variables to your liking and run the script

#Administrative variables
image_download_path = "./Images/"
metadata_download_path = "./Metadata/"

#Download preferences
download_full_images = True
download_cut_out_images = True

#Customize query
query = "hypothe*"

#Customize year of appearance
#If all_years is True, there will be no year filtering
#If all_years is False and specific_years is a list containing numbers, the results will be filtered for those specific years
#If all_years is False and specific_years is empty, the results will span the range of years between min_year and max_year
all_years = False
specific_years = [1870,1871]
min_year = 1870
max_year = 1871

#Customize date of adding the newspaper to the Delpher database
all_dates = False
min_date = "01-01-2016"
max_date = "31-12-2021"

#Customize article type
#Either set article_type_All to true, or indicate preferences for individual article types
article_type_All = False
article_type_Advertentie = True
article_type_Artikel = False
article_type_Familiebericht = False
article_type_Illustratie_met_onderschrift = False

#Customize distribution area
distribution_area_All = False
distribution_area_Landelijk = False
distribution_area_Indonesie = False
distribution_area_Antillen = False
distribution_area_Regionaal = True
distribution_area_Suriname = False
distribution_area_VS = False

#Customize names of desired papers
#Add the names of the papers you want to search for inside the list. If the list is empty, all papers will be included in the results
paper_titles = ["Rotterdamsch nieuwsblad", "Provinciale Overijsselsche en Zwolsche courant"]

#Customize place where the papers have been printed
paper_origins = ["Rotterdam","Zwolle"]

#Customize names of places who have donated their pages for the Delpher project
sources = ["Koninklijke Bibliotheek","Gemeentearchief Rotterdam","Historisch Centrum Overijssel"]

#Alright, you're good to go!

def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_image_and_metadata(url):
    """
    Returns the image URL on a Delpher result page and the associated metadata
    """
    soup = bs(requests.get(url).content, "html.parser")
    paper_name = ""
    paper_date = ""

    # Collect metadata from page
    paper_names = [span.text.strip() for span in soup.find_all("span") if str(span.attrs.get("class")) != "None" and len(span.attrs.get("class")) > 0 and span.attrs.get("class")[0] == "object-view-top-block__heading-content"]
    if len(paper_names) > 0:
        paper_name = paper_names[0]
    paper_dates = [li.text.strip() for li in soup.find_all("li") if str(li.attrs.get("class")) != "None" and len(li.attrs.get("class")) > 2 and li.attrs.get("class")[2] == "object-view-top-block__metadata-subtitle--date"]
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
        if is_valid(img_url_cut_out) and is_valid(img_url_full):
            return [img_url_cut_out, img_url_full, keywords, paper_name, paper_date]
    return []

def download(url, pathname, filename):
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

def create_query_URL():
    """
    Create a Delpher search URL based on the search a user wants to make
    """
    php_variables = []

    #Add query
    if query:
        php_variables.append("query=" + query)

    #Add year of appearance
    if not all_years:
        if not specific_years:
            #Create a list of specific years using the date range
            specific_years_list = [year + min_year for year in range(max_year - min_year + 1)]
        else:
            specific_years_list = specific_years
        for year in specific_years_list:
            php_variables.append("facets[periode][]=2|%de_eeuw|%d-%d|%d|" % (math.ceil(year / 100),int(year / 10) * 10,int(year / 10) * 10 + 9,year))

    #Add article type
    if not article_type_All:
        if article_type_Advertentie:
            php_variables.append("&facets[type][]=advertentie")
        if article_type_Artikel:
            php_variables.append("&facets[type][]=artikel")
        if article_type_Familiebericht:
            php_variables.append("&facets[type][]=familiebericht")
        if article_type_Illustratie_met_onderschrift:
            php_variables.append("&facets[type][]=illustratie+met+onderschrift")

    #Add distribution type
    if not distribution_area_All:
        if distribution_area_Antillen:
            php_variables.append("facets[spatial][]=Nederlandse+Antillen")
        if distribution_area_Indonesie:
            php_variables.append("facets[spatial][]=Nederlands-Indië+|+Indonesië")
        if distribution_area_Landelijk:
            php_variables.append("facets[spatial][]=Landelijk")
        if distribution_area_Regionaal:
            php_variables.append("facets[spatial][]=Regionaal|lokaal")
        if distribution_area_Suriname:
            php_variables.append("facets[spatial][]=Suriname")
        if distribution_area_VS:
            php_variables.append("facets[spatial][]=Verenigde+Staten")

    #Add titles of newspapers
    for paper_title in paper_titles:
        php_variables.append("facets[papertitle][]=" + re.sub("\s","+",paper_title))

    #Add place of printing
    for paper_origin in paper_origins:
        php_variables.append("facets[spatialCreation][]=" + re.sub("\s","+",paper_origin))

    #Add donation source
    for source in sources:
        php_variables.append("facets[sourceFacet][]=" + re.sub("\s","+",source))

    #Add date of addition of newspapers to the Delpher database
    if not all_dates:
        php_variables.append('cql[]=(DelpherPublicationDate+_gte_+"%s")&cql[]=(DelpherPublicationDate+_lte_+"%s")' % (min_date, max_date))

    #Create URL
    URL = "https://www.delpher.nl/nl/kranten/results?"
    for php_variable in php_variables:
        URL += php_variable + "&"
    URL = URL[:-1]
    URL += "&maxperpage=50&sortfield=date&coll=ddd"

    return URL

def get_links_from_query():
    """
    Traverse through the pages listing the results found by Delpher, and collect the links to pages with individual results
    """

    #Create search URL
    url = create_query_URL()
    #Process URL
    soup = bs(requests.get(url).content, "html.parser")
    #Figure out the number of result pages by checking the total number of results and dividing it by 50
    possible_numbers_of_results = [span.text for span in soup.find_all("span") if str(span.attrs.get("id")) != "None" and span.attrs.get("id") == "js-searchtip__numberOfResults"]
    if len(possible_numbers_of_results) < 1:
        return []
    num_results = int(possible_numbers_of_results[0])
    num_pages = math.ceil(num_results / 50)

    #For each page with 50 (or less) results, collect the links to each individual result and put them into an array
    results_links = []
    for page_number in tqdm(range(num_pages), "Gathering results"):
        #Load new page
        soup = bs(requests.get(url + "&page=%d" % (page_number + 1)).content, "html.parser")
        #Find links
        for link in soup.find_all("a"):
            result_url = link.attrs.get("href")
            #Is this a link to a result page?
            if not result_url or not result_url.startswith("/nl/kranten/view"):
                continue
            #Make the url absolute
            result_url = urljoin(url,result_url)
            #finally, if the url is valid, it can be added to the array
            if is_valid(result_url) and result_url not in results_links:
                results_links.append(result_url)
    return results_links

def remove_leading_zeroes(number):
    """
    Removes leading zeroes from month and day numbers ("04" -> "4", "12" -> "12")
    """
    if len(number) > 1 and number[0] == "0":
        return number[1:]
    return number

def split_date(date_string):
    """
    Split Delpher's full date strings into separate pieces of date-related information
    """
    return (date_string[0:2],
            remove_leading_zeroes(date_string[0:2]),
            date_string[3:5],
            remove_leading_zeroes(date_string[3:5]),
            date_string[6:10])

def create_accompanying_csv(imgs):
    """
    Write metadata to a file
    """
    with open(metadata_download_path + "%s_metadata.csv" % query,"w") as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(["Result ID","Titel","Dag","DAG","Maand","MAAND","Jaar","URL full","URL cut out","keywords"])
        for img_data in imgs.items():
            day, DAY, month, MONTH, year = split_date(img_data[1][4])
            csv_writer.writerow([img_data[0],img_data[1][3],day,DAY,month,MONTH,year,img_data[1][1],img_data[1][0],img_data[1][2]])

def main():
    images_info = {}
    #Create a custom query and gather the links associated with the results
    links = get_links_from_query()
    if not links:
        print("Could not find any results :( Did you make a spelling error somewhere?")
        return
    #Let's not assume that the user is okay with downloading 4.000.000 images
    max_number = input("Found %d articles that matched your search query! How many do you want to download? (Please type in your answer below and press Enter)\n" % len(links))
    if int(max_number) < len(links):
        links = links[:int(max_number)]
    for index in tqdm(range(len(links)),"Collecting image urls and newspaper metadata"):
        # for each page link, collect the links to the full and cut out versions of the image shown on that page, as well as any corresponding metadata that can be detected
        info = get_image_and_metadata(links[index])
        if info:
            #add url and metadata info to the image info list
            images_info["%d" % (index + 1)] = info
    for item in tqdm(images_info.items(),"Downloading images"):
        # for each image, download the versions that the user wants downloaded
        if download_cut_out_images:
            download(item[1][0], image_download_path, "%s_result_%s_cut_out.jpeg" % (query, item[0]))
        if download_full_images:
            download(item[1][1], image_download_path, "%s_result_%s_full.jpeg" % (query, item[0]))
    if links:
        # Write the collected metadata to a csv file
        create_accompanying_csv(images_info)
    print("Done!")

if __name__ == '__main__':
    main()
