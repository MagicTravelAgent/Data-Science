#Code shown here has been copied and adapted from https://www.thepythoncode.com/article/download-web-page-images-python

import requests
import os
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
import re
import pandas as pd
import csv

#If you want to use this script yourself, just edit these four variables and everything ought to work
#Oh maybe make sure all of the above libraries are installed, as well as either the xlrd or the openpyxl module (which pandas depends on to read Excel files)
path_to_excel_file = "/home/astraea/Files/Programmeren/Python/Projects/Educatie/Delpher/Local/output/data_files/SAMEN_David_en_Lennart_met_OCR_v2.xlsx"
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

def get_all_images(url):
    """
    Returns all image URLs on a single `url`
    """
    soup = bs(requests.get(url).content, "html.parser")
    urls = []
    paper_name = ""
    paper_date = ""

    #Collect metadata from page
    paper_names = [span.text.strip() for span in soup.find_all("span") if str(span.attrs.get("class")) != "None" and len(span.attrs.get("class")) > 0 and span.attrs.get("class")[0] == "object-view-top-block__heading-content"]
    if len(paper_names) > 0:
        paper_name = paper_names[0]
    paper_dates = [li.text.strip() for li in soup.find_all("li") if str(li.attrs.get("class")) != "None" and len(li.attrs.get("class")) > 2 and li.attrs.get("class")[2] == "object-view-top-block__metadata-subtitle--date"]
    if len(paper_dates) > 0:
        paper_date = paper_dates[0]

    #Collect images
    for img in tqdm(soup.find_all("img"), "Extracting images"):
        img_url = img.attrs.get("src")
        if not img_url:
            # if img does not contain src attribute, just skip
            continue
        # make the URL absolute by joining domain with the URL that is just extracted
        img_url = urljoin(url, img_url)
        #Collect metadata information from URL
        keywords = re.sub(r"^.*words=([^&]+)&.*$", r"\1", img_url)
        for pattern in [("%28", ""), ("%29", ""), ("%2A", "*")]:
            keywords = re.sub("%s" % pattern[0], "%s" % pattern[1], keywords)
        keywords = re.split("\+",keywords)
        #Remove highlights
        img_url_cut_out = re.sub("words=[^&]+&","",img_url)
        #Remove the 's', 'h', 'x' and 'y' attributes to obtain the full image instead of a cut out part
        img_url_full = re.sub("&[shxy]=[^&]+","",img_url_cut_out)
        # finally, if the url is valid
        if is_valid(img_url_cut_out) and is_valid(img_url_full):
                urls.append([img_url_cut_out, img_url_full, keywords, paper_name, paper_date])
    return urls

def download(url, pathname, filename):
    """
    Downloads a file given an URL and puts it in the folder `pathname`
    """
    # if path doesn't exist, make that path dir
    if not os.path.isdir(pathname):
        os.makedirs(pathname)
    # download the body of response by chunk, not immediately
    response = requests.get(url, stream=True)
    # get the total file size
    file_size = int(response.headers.get("Content-Length", 0))
    # get the file name
    #filename = os.path.join(pathname, url.split("/")[-1])
    filename = os.path.join(pathname, filename)
    # progress bar, changing the unit to bytes instead of iteration (default by tqdm)
    progress = tqdm(response.iter_content(1024), f"Downloading {filename}", total=file_size, unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f:
        for data in progress:
            # write data read to the file
            f.write(data)
            # update the progress bar manually
            progress.update(len(data))

def get_links_from_excel(start, end):
    #Read URL fields from Excel file, starting at field 'start' and stopping at field with index 'end'
    df = pd.read_excel(path_to_excel_file)
    urls = df["URL"].tolist()[start:end]
    return {"%d" % (start + index):urls[index] for index in range(len(urls))}

def remove_leading_zeroes(number):
    if len(number) > 1 and number[0] == "0":
        return number[1:]
    return number

def split_date(date_string):
    return (date_string[0:2],
            remove_leading_zeroes(date_string[0:2]),
            date_string[3:5],
            remove_leading_zeroes(date_string[3:5]),
            date_string[6:10])

def create_accompanying_csv(imgs):
    with open(metadata_download_path + "metadata.csv","w") as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(["Entry","Titel","Dag","DAG","Maand","MAAND","Jaar","URL_full","URL_cut_out","keywords"])
        for img_data in imgs.items():
            day, DAY, month, MONTH, year = split_date(img_data[1][4])
            csv_writer.writerow([str(int(img_data[0]) + 2),img_data[1][3],day,DAY,month,MONTH,year,img_data[1][1],img_data[1][0],img_data[1][2]])

def main(starting_row,ending_row,path):
    imgs = {}
    for item in get_links_from_excel(starting_row - 2,ending_row - 2).items():
        # get all images
        images = get_all_images(item[1])
        if len(images) > 0:
            #In our specific use case, there should be only one image per link
            imgs["%s" % (item[0])] = images[0]
    for item in imgs.items():
        # for each image, download it
        if download_cut_out_images:
            download(item[1][0], path, "entry_%d_cut_out.jpeg" % (int(item[0]) + 2))
        if download_full_images:
            download(item[1][1], path, "entry_%d_full.jpeg" % (int(item[0]) + 2))
        create_accompanying_csv(imgs)

main(row_number_start,row_number_end,image_download_path)