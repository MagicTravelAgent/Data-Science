import pandas as pd
import re
import csv
import math

#This script can be used to calculate agreement between our automated scripts and the excel sheet that was filled in by hand
#This script hasn't been finished yet because we need more data before this becomes useful

#Convert xlsx to csv for easy comparison
#path_to_excel_file = "###"
#df = pd.read_excel(path_to_excel_file)
#rows = df.to_numpy().tolist()
#with open(re.sub("\.xlsx",".csv",path_to_excel_file),"w") as output_file:
#    csv_writer = csv.writer(output_file)
#    csv_writer.writerow(df.columns.values)
#    for row in rows:
#        row = [item if not (str(type(item)) == "<class 'float'>" and math.isnan(item)) else "" for item in row]
#        csv_writer.writerow(row)