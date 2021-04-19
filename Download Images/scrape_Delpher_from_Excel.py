#Code shown here has been copied and adapted from https://www.thepythoncode.com/article/download-web-page-images-python

import requests
import os
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
import re
import pandas as pd
import csv

#In order to use this script, (1) make sure all of the above libraries are installed (as well as either xlrd or openxl which pandas depends on to read Excel files),
#(2) edit the seven variables below and (3) run the script!

path_to_excel_file = "../Lucas Testing/Excel/OCR List.xlsx"
image_download_path = "./Images/"
metadata_download_path = "./Metadata/"
row_number_start = 2
row_number_end = 102 #specific row numbers to enable Python not to download all 4000 links from the Excel file at once
download_full_images = True
download_cut_out_images = True

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

def get_links_from_excel(start, end):
    """
    Reads URL fields from the Excel file, starting at field 'start' and stopping right before the field with index 'end' is reached
    """
    df = pd.read_excel(path_to_excel_file)
    urls = df["URL"].tolist()[start:end]
    return {"%d" % (start + index):urls[index] for index in range(len(urls))}

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

def create_accompanying_csv(images_info):
    """
    Write metadata to a file
    """
    with open(metadata_download_path + "Excel_metadata.csv","w") as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(["Entry","Titel","Dag","DAG","Maand","MAAND","Jaar","URL_full","URL_cut_out","keywords"])
        for img_data in images_info.items():
            day, DAY, month, MONTH, year = split_date(img_data[1][4])
            csv_writer.writerow([str(int(img_data[0]) + 2),img_data[1][3],day,DAY,month,MONTH,year,img_data[1][1],img_data[1][0],img_data[1][2]])

def main():
    images_info = {}
    #Iterate over links collected from Christiaans Excel sheet
    for item in tqdm(get_links_from_excel(row_number_start - 2,row_number_end - 2).items(),"Collecting image urls and newspaper metadata"):
        # for each page link, collect the links to the full and cut out versions of the image shown on that page, as well as any corresponding metadata that can be detected
        info = get_image_and_metadata(item[1])
        if info:
            # add url and metadata info to the image info list
            images_info["%s" % (item[0])] = info
    for item in tqdm(images_info.items(),"Downloading images"):
        # for each image, download the versions that the user wants downloaded
        if download_cut_out_images:
            download(item[1][0], image_download_path, "entry_%d_cut_out.jpeg" % (int(item[0]) + 2))
        if download_full_images:
            download(item[1][1], image_download_path, "entry_%d_full.jpeg" % (int(item[0]) + 2))
    if images_info:
        # Write the collected metadata to a csv file
        create_accompanying_csv(images_info)
    print("Done!")

if __name__ == '__main__':
    main()