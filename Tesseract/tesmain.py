try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract as pt
import re


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
# txt = pt.image_to_string(Image.open('test.jpg'), lang='nld')
# f = open("test_with_dutch_post.txt", "w")
# f.write(txt)
# f.close()

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