try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract as pt
import re
import io
import glob
import csv
#from improve_spelling import improve_spelling


# in order to use tesseract we must install it
# https://medium.com/quantrium-tech/installing-and-using-tesseract-4-on-windows-10-4f7930313f82

# If you don't have tesseract executable in your PATH, include the following:
#pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'

# Simple image to string
# txt = pt.image_to_string(Image.open('test.jpg'))
# f = open("test_no_post.txt", "w")
# f.write(txt)
# f.close()

# List of available languages
# print(pt.get_languages(config=''))

# Dutch text image to string
# text = pt.image_to_string(Image.open('test.jpg'), lang='nld')
# f = open("test_with_dutch_post.txt", "w")
# f.write(text)
# f.close()

# Entire directory of dutch text images to strings
#image_directory = "###"
#output_directory = "###"
#for image_filename in glob.glob(image_directory + "*.jpeg"):
#      try:
#            text = pt.image_to_string(Image.open(image_filename), lang='nld')
#            f = open(re.sub(r"^%s(.*)\.jpeg$" % (image_directory),r"%s\1.txt" % (output_directory),image_filename), "w")
#            f.write(text)
#            f.close()
#      except Exception as ex:
             #Astraea tested this with 100 images and 15 of them threw an error like this:
             #(-11, 'Tesseract Open Source OCR Engine v4.0.0 with Leptonica Warning: Invalid resolution 0 dpi. Using 70 instead. Estimating resolution as 126 contains_unichar_id(unichar_id):Error:Assert failed:in file ../../src/ccutil/unicharset.h, line 502')
             #Help I have no idea how to solve it
#            print(ex)

#assuming that the text files exist we run the code to get the text out:
f = open("test_with_dutch_post.txt", "r")
text = f.read()
f.close()

#now the text is open we split based on two empty lines of text:
text = text.split("\n ")
print(len(text))

#we check each split to see if it contains anything from the regular expression
#so first we build the regular expression:
reg = ".*hypothe+.*"

for i in text:
    x = re.search(reg, i)
    if x:
      print("YES! We have a match!")
      print(i)
    else:
      print("No match")

# This was Astraea trying to detect ocr from 100 images, worked only for 2 of them so don't try this at home
#text_directory = "###"
#output_directory = "###"
#output_file = open(output_directory + "img_ocr.csv","w")
#csv_writer = csv.writer(output_file)
#csv_writer.writerow(["ID_CVB2","ID_CVB","IDv2","ID","Titel","Dag","DAG","Maand","MAAND","Jaar","Type","Type_Detail","Soort Transactie","Vraag/Aanbod","Detail","Contact","Beroep","Locatie_Contact","Handelt namens","Advertentie_Opmerking","Bedragen","Bedrag_range_minimum","Bedrag_range_maximum","Reden","Onderpand","Locatie_Onderpand","Loan-to-value","Tegenpartij_Voorkeur","Aflossing","Rente","Moment","Hypotheek_Opmerking","URL","tblResultaatMetadatakey","OCR"])
#filenames = glob.glob(text_directory + "*.txt")
#filenames.sort()
#for filename in filenames:
#      print("Opening %s..." % (filename))
#      f = open(filename, "r")
#      #f = io.open("test_with_dutch_post.txt", "r", encoding="ISO-8859-15")
#      text = f.read()
#      f.close()

#      text = text.split("\n ")
#      #print(len(text))

#      reg = "^.*(" \
#            "(?= 1e )(?= hypothe)|" \
#            "(?= 1ste )(?= hypothe)|" \
#            "(?= a[^ ]*ngebo[^ ]*den )(?= onderpa)|" \
#            "(?= b[^ ]*sch[^ ]*kba[^ ]*r )(?= tegen )(?= rente)|" \
#            "(?= bil[^ ]*k)(?= rente)|" \
#            "(?= Bouwfonds)|" \
#            "(?= eerste)(?= hypothe)|" \
#            "(?= Eerste)(?= schepenke)|" \
#            "(?= genoeg )(?= overwa[^ ]*rde)|" \
#            "(?= gevr[^ ]*g)(?= onderpa)|" \
#            "(?= gevr[^ ]*g)(?= tegen )(?= rente)|" \
#            "(?= gez[^ ]*ht )(?= tegen )(?= rente)|" \
#            "(?= gezocht )(?= onderpa)|" \
#            "(?= grond[^ ]*red[^ ]*t)|" \
#            "(?= hyp. )(?= verban)|" \
#            "(?= hypoth)(?= b[^ ]*sch[^ ]*kba[^ ]*r )|" \
#            "(?= hypothe[^ ]*b)|" \
#            "(?= Hypothe[^ ]*r )(?= verban)|" \
#            "(?= Ie )(?= hypothe)|" \
#            "(?= Iste )(?= hypothe)|" \
#            "(?= le )(?= hypothe)|" \
#            "(?= leen )(?= onderpa)|" \
#            "(?= leen )(?= tegen )(?= rente)|" \
#            "(?= lste )(?= hypothe)|" \
#            "(?= mak[^ ]*el[^ ]*r )(?= hypoth)|" \
#            "(?= notaris )(?= hypothe)|" \
#            "(?= onderpa)(?= aanwe[^ ]*ig )|" \
#            "(?= onderpa)(?= overwa[^ ]*rde)|" \
#            "(?= Pandbrie)|" \
#            "(?= ru[^ ]*me)(?= overwa[^ ]*rde)|" \
#            "(?= secuur )(?= onderpa)|" \
#            "(?= soli[^ ]*d)(?= onderpa)|" \
#            "(?= vold[^ ]*nde)(?= overwa[^ ]*rde)" \
#            ").*$"

#      match = ""
#      for i in text:
#          x = re.search(reg, i.replace("\n"," "))
#          if x:
#                match += i
#      if match == "":
#            for i in text:
#                  i = improve_spelling(i)
#                  x = re.search(reg, i.replace("\n", " "))
#                  if x:
#                        print(i)
#                        match += i
#      else:
#            match = improve_spelling(match)
#            print(match)
#      csv_writer.writerow(["","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",match])
#output_file.close()