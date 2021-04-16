try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract as pt
import re
import io
import glob
import csv
import improve_spelling as imp
import os

cwd = os.getcwd()  # Get the current working directory (cwd)
files = os.listdir(cwd)  # Get all the files in that directory
print("Files in %r: %s" % (cwd, files))

#--------------------------------------------------------------------- simple OCR for scraped and manual download

text = pt.image_to_string(Image.open('scraped.jpeg'))
with open("simple_scraped.txt", "w", encoding="utf-8") as f:
    f.write(text)
    f.close()

text = pt.image_to_string(Image.open('manual.jpg'))
with open("simple_manual.txt", "w", encoding="utf-8") as f:
    f.write(text)
    f.close()

#--------------------------------------------------------------------- OCR for scraped and manual with dutch post from tesseract

text = pt.image_to_string(Image.open('scraped.jpeg'), lang='nld')
with open("dutch_post_scraped.txt", "w", encoding="utf-8") as f:
    f.write(text)
    f.close()

text = pt.image_to_string(Image.open('manual.jpg'), lang='nld')
with open("dutch_post_manual.txt", "w", encoding="utf-8") as f:
    f.write(text)
    f.close()

#--------------------------------------------------------------------- using the speller improver for simple scraped and manual

with open("simple_scraped.txt", "r", encoding="utf-8") as f:
    text = f.read()
    f.close()
    i = imp.improve_spelling(text)
with open("simple_scraped_checked.txt", "w", encoding="utf-8") as f:
    f.write(i)
    f.close()

with open("simple_manual.txt", "r", encoding="utf-8") as f:
    text = f.read()
    f.close()
    i = imp.improve_spelling(text)
with open("simple_manual_checked.txt", "w", encoding="utf-8") as f:
    f.write(i)
    f.close()

# --------------------------------------------------------------------- using the speller improver for simple and manual post dutch

with open("dutch_post_scraped.txt", "r", encoding="utf-8") as f:
    text = f.read()
    f.close()
    i = imp.improve_spelling(text)
with open("dutch_post_scraped_checked.txt", "w", encoding="utf-8") as f:
    f.write(i)
    f.close()

with open("simple_manual.txt", "r", encoding="utf-8") as f:
    text = f.read()
    f.close()
    i = imp.improve_spelling(text)
with open("dutch_post_manual_checked.txt", "w", encoding="utf-8") as f:
    f.write(i)
    f.close()