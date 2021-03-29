import pandas as pd
import re

#This script generates frequency files based on the Excel sheet
#To use this script, define paths to the input and output directories/filenames below, and run it
path_to_excel_file = "/home/astraea/Files/Programmeren/Python/Projects/Educatie/Delpher/Local/output/data_files/"
excel_filename = "SAMEN_David_en_Lennart_met_OCR_v2.xlsx"
path_to_frequency_file = "/home/astraea/Files/Programmeren/Python/Projects/Educatie/Delpher/Local/output/data_files/"
query_frequency_filename = "type_query_frequencies.csv"
numOfMatches_frequency_filename = "type_numOfMatches_frequencies.csv"

#Read the Excel file and keep only the relevant columns
df = pd.read_excel(path_to_excel_file + excel_filename)
df = pd.DataFrame({'Type': df['Type'], 'URL': df['URL']})

#Add a query column based on the contents of the URL column
queries = []
for _, data in df.iterrows():
    query = re.sub(r"^.*&query=([\w\d%+.]+)&.*$", r"\1", data['URL'])
    for pattern in [("%28", ""), ("%29", ""), ("%2A", "*"), ("\+", " ")]:
        query = re.sub("%s" % pattern[0], "%s" % pattern[1], query)
    queries.append(query)
df['Queries'] = pd.Series(queries)

#We're gonna make two frequency files: one based on individual queries and one based on the total number of queries per row
#Let's start with individual queries

#Count types for each query
counts = {}
for _, data in df.iterrows():
    type = data['Type'].strip().lower()
    for query in data['Queries'].split():
        if query not in counts.keys():
            counts[query] = {"false positive":0,"individu":0,"instelling":0,"verkoop en hypotheek":0}
        counts[query][type] += 1
freqs = pd.DataFrame(counts.values(),index=list(counts.keys()),dtype=int)

#Calculate accuracy metrics
freqs["precision"] = (freqs["individu"] + freqs["instelling"] + freqs["verkoop en hypotheek"]) / (freqs["false positive"] + freqs["individu"] + freqs["instelling"] + freqs["verkoop en hypotheek"]) * 100
freqs["recall"] = (freqs["individu"] + freqs["instelling"] + freqs["verkoop en hypotheek"]) / (sum(freqs["individu"]) + sum(freqs["instelling"]) + sum(freqs["verkoop en hypotheek"])) * 100
freqs["f-measure"] = (2 * (freqs["precision"] / 100) * (freqs["recall"] / 100)) / ((freqs["precision"] / 100) + (freqs["recall"] / 100))
freqs["f-measure"] = freqs["f-measure"].fillna(0)

#Make a neat data frame
freqs = freqs.sort_values(by="f-measure",ascending=False)
freqs = freqs.round({"false positive":0,"individu":0,"instelling":0,"verkoop en hypotheek":0,"precision":2,"recall":2,"f-measure":2})
for column in ["precision","recall"]:
    newcolumn = []
    for _, data in freqs.iterrows():
        newcolumn.append(str(data[column]) + "%")
    freqs[column] = newcolumn

#Write the dataframe to the destination path
freqs.to_csv(path_to_frequency_file + query_frequency_filename)

#Now, let's continue to find the relation between total number of queries and false-positivity
#Count types for each number of total queries
counts = {}
for _, data in df.iterrows():
    type = data['Type'].strip().lower()
    queryNum = len(data['Queries'].split())
    if queryNum not in counts.keys():
        counts[queryNum] = {"false positive":0,"individu":0,"instelling":0,"verkoop en hypotheek":0}
    counts[queryNum][type] += 1
freqs = pd.DataFrame(counts.values(),index=list(counts.keys()),dtype=int)
freqs = freqs.sort_index()

#Calculate accuracy metrics
freqs["precision"] = (freqs["individu"] + freqs["instelling"] + freqs["verkoop en hypotheek"]) / (freqs["false positive"] + freqs["individu"] + freqs["instelling"] + freqs["verkoop en hypotheek"]) * 100
freqs["recall"] = (freqs["individu"] + freqs["instelling"] + freqs["verkoop en hypotheek"]) / (sum(freqs["individu"]) + sum(freqs["instelling"]) + sum(freqs["verkoop en hypotheek"])) * 100
freqs["f-measure"] = (2 * (freqs["precision"] / 100) * (freqs["recall"] / 100)) / ((freqs["precision"] / 100) + (freqs["recall"] / 100))
freqs["f-measure"] = freqs["f-measure"].fillna(0)

#Make a neat data frame
freqs = freqs.round({"false positive":0,"individu":0,"instelling":0,"verkoop en hypotheek":0,"precision":2,"recall":2,"f-measure":2})
for column in ["precision","recall"]:
    newcolumn = []
    for _, data in freqs.iterrows():
        newcolumn.append(str(data[column]) + "%")
    freqs[column] = newcolumn

#Write the dataframe to the destination path
freqs.to_csv(path_to_frequency_file + numOfMatches_frequency_filename)