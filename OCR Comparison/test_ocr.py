#import easyocr
import pyocr
import pyocr.builders
import re
from PIL import Image

#This script has been used to test two different Python ocr modules (easyocr and pyocr) on 10 images from Delpher.

#Define paths to image files and to output
image_dir = ""
outputdir = ""

#Define names of images to use ocr on
#filenames = ["1.heic","2.heic"]
filenames = ["test.jpg",]

# def use_easyocr():
#     reader = easyocr.Reader(['nl'])
#
#     with open(outputdir + "easyocr.txt", "w") as output_file:
#         for filename in filenames:
#             result = reader.readtext(image_dir + filename, detail=0)
#             print(str(result))
#             for index in range(len(result)):
#                 output_file.write(result[index] + (" " if index < len(result) - 1 else "\n"))

def use_pyocr():
    tool = pyocr.get_available_tools()[0]
    lang = tool.get_available_languages()[1]

    print(tool)
    print(lang)

    with open(outputdir + "pyocr.txt", "w") as output_file:
        for index in range(len(filenames)):
            txt = "Encountered an error in file %d!" % index
            try:
                txt = tool.image_to_string(
                    Image.open(image_dir + filenames[index]),
                    lang=lang,
                    builder=pyocr.builders.TextBuilder()
                )
            except Exception as ex:
                print(ex)
            txt = re.sub("\n"," ",txt)
            print(str(txt))
            output_file.write('%s\n' % txt)

#use_easyocr()
use_pyocr()