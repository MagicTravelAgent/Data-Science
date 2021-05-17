import os
# Look to the path of your current working directory
working_directory = os.getcwd()
# Or: file_path = os.path.join(working_directory, 'my_file.py')
file_path = working_directory + r'C:\Users\koenv\OneDrive\Documenten\data science\Data-Science\Tesseract\OCR2\entry_2_cut_out.txt'


text = open(file_path)

print(text)
