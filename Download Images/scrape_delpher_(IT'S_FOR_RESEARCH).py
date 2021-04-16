#Code shown here has been copied and adapted from https://www.thepythoncode.com/article/download-web-page-images-python

import requests
import os
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse
import re
import pandas as pd

#If you want to use this script yourself, just edit these four variables and everything ought to work
#Oh maybe make sure all of the above libraries are installed, as well as either the xlrd or the openpyxl module (which pandas depends on to read Excel files)
path_to_excel_file = r"C:\Users\koenv\OneDrive\Documenten\data science\SAMEN David en Lennart met OCR v2.xlsx"
image_download_path = r"C:\bin\delpherdownloads"
row_number_start = 103
row_number_end = 104 #specific row numbers to enable Python not to download all 4000 links from the Excel file at once

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
    for img in tqdm(soup.find_all("img"), "Extracting images"):
        img_url = img.attrs.get("src")
        if not img_url:
            # if img does not contain src attribute, just skip
            continue
        # make the URL absolute by joining domain with the URL that is just extracted
        img_url = urljoin(url, img_url)
        #Remove the 's', 'h', 'x' and 'y' attributes to obtain the full image instead of a cut out part
        img_url = re.sub("&[shxy]=[^&]+","",img_url)
        print(img_url)
        # finally, if the url is valid
        if is_valid(img_url):
                urls.append(img_url)
    print(urls)
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
        download(item[1], path, "entry_%d.jpg" % (int(item[0]) + 2))

main(row_number_start,row_number_end,image_download_path)