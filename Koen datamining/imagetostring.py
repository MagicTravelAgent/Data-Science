# Simple image to string

try:
    from PIL import Image
except ImportError:
    import Image

import pytesseract as pt



txt = pt.image_to_string(Image.open("entry_103.jpeg"))
f = open("test_no_post.txt", "w", encoding="utf-8")
f.write(txt)
f.close()

