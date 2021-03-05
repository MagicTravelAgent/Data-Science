try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract as pt

# in order to use tesseract we must install it
# https://medium.com/quantrium-tech/installing-and-using-tesseract-4-on-windows-10-4f7930313f82

# If you don't have tesseract executable in your PATH, include the following:
#pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'

# Simple image to string
#print(image_to_string(Image.open('test.jpg')))

# List of available languages
print(pt.get_languages(config=''))

# Dutch text image to string
txt = (pt.image_to_string(Image.open('test.jpg'), lang='nld'))
f = open("test.txt", "w")
f.write(txt)
f.close()

# In order to bypass the image conversions of pytesseract, just use relative or absolute image path
# NOTE: In this case you should provide tesseract supported images or tesseract will return error
#print(image_to_string('test.jpg'))

# Batch processing with a single file containing the list of multiple image file paths
#print(image_to_string('images.txt'))

# Get bounding box estimates
#print(image_to_boxes(Image.open('test.jpg')))

# Get verbose data including boxes, confidences, line and page numbers
#print(image_to_data(Image.open('test.jpg')))

# Get information about orientation and script detection
#print(image_to_osd(Image.open('test.jpg')))

# Get a searchable PDF
# pdf = image_to_pdf_or_hocr('test.jpg', extension='pdf')
# with open('test.pdf', 'w+b') as f:
#     f.write(pdf) # pdf type is bytes by default

# Get HOCR output
# hocr = image_to_pdf_or_hocr('test.jpg', extension='hocr')

# Get ALTO XML output
# xml = image_to_alto_xml('test.jpg')