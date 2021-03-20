import csv
import re

csv_directory = "###"

#function to add information to the csv
def add_information(row, rowindex, information):
    if information != "":
        information = information.strip()
        if row[rowindex] == "":
            row[rowindex] = information
        else:
            if information not in row[rowindex].split("; "):
                row[rowindex] += "; " + information

#open the input csv and output csv
with open(csv_directory + "img_ocr.csv") as input_file:
    with open(csv_directory + "img_ocr_data.csv","w") as output_file:
        csv_reader = csv.reader(input_file)
        csv_writer = csv.writer(output_file)

        #check the ocr from each row for indications of certain information
        for row in csv_reader:
            if len(row) > 34:
                if row[34] != "OCR":
                    ocr = row[34]
                    ocr_lower = ocr.lower()

                    #Search for indications of type (column K/L)
                    if re.search("bank",ocr_lower):
                        add_information(row, 10, "Instelling")
                        add_information(row, 11, re.sub(r"^.*?([\w]*bank).*$",r"\1",ocr,flags=re.IGNORECASE))
                    elif re.search("verko[o]?p",ocr_lower):
                        add_information(row, 10, "Verkoop en Hypotheek")
                        add_information(row, 12, "hypotheek")
                        add_information(row, 13, "aanbod")
                    else:
                        add_information(row, 10, "False Positive")

                    #Indications of transaction type (column M)
                    if re.search("hypothe(ek|cair)",ocr_lower):
                        add_information(row, 12, "hypotheek")
                    if re.search("pandbrie",ocr_lower):
                        add_information(row, 12, "pandbrief")
                    if re.search("obligati",ocr_lower):
                        add_information(row, 12, "Obligaties")
                    if re.search("gevraagd",ocr_lower):
                        add_information(row, 12, "Lening")
                        add_information(row, 13, "vraag")

                    #Indications of supply/demand (column N)
                    if re.search("gee(ft|ven) uit|verstrek",ocr_lower):
                        add_information(row, 13, "aanbod")

                    #Indications of details (column O)
                    #for some reason these often seem to contain the word "kan"
                    #also this doesn't seem to be working yet
                    if re.search("^(\. )?([A-Z][^.]* kan [^.]*\.)( [A-Z].*)?$",ocr):
                        add_information(row, 14, re.sub(r"^(\. )?([A-Z][^.]* kan [^.]*\.)( [A-Z].*)?$",r"\1",ocr))

                    #Indications of contact person (column P, Q and R)
                    for name_indicator in ["Mr\.","den Heer","[Ff]ranco[^.]*aan"]:
                        #search for the name indicators, and grab the 10 words that follow it
                        name_areas = re.findall("( %s ([A-Z][^ .,]*[ .,]+)([^ .,]+[ .,]+){0,9})" % name_indicator,ocr)
                        for name_area in name_areas:
                            print("23: " + name_area[0])

                            #'te' antecedes a place. If you detect 'te', that's definitely not part of a contact person's name.
                            if re.search(" %s .* te " % name_indicator,name_area[0]):
                                #Check for commas, which also signify the end of a name
                                if re.search(" %s .*, .* te " % name_indicator,name_area[0]):
                                    add_information(row, 15, re.sub(r"^.* %s (.*),.* te .*$" % name_indicator,r"\1",name_area[0]))
                                    #the word after the comma might be a contact person's profession
                                    add_information(row, 16, re.sub(r"^.* %s .*,(.*) te .*$" % name_indicator, r"\1", name_area[0]))
                                else:
                                    add_information(row, 15, re.sub(r"^.* %s (.*) te .*$" % name_indicator,r"\1",name_area[0]))
                                #The piece of information following just after 'te' will be considered the contact person's location
                                #add_information(row, 17, re.sub(r"^.* te (([A-Z][A-Za-z-]*)( [A-Z][).*?$", r"\1",name_area[0])[:-1])
                                add_information(row, 17, re.sub(r"^.* te (([A-Z][A-Za-z-]* )*([A-Z][A-Za-z-]*[.,])?).*?$",r"\1",name_area[0])[:-1])
                                print(row[17])
                            else:
                                #Check for commas
                                if re.search(" %s .*," % name_indicator,name_area[0]):
                                    add_information(row, 15, re.sub(r"^.* %s (.*?),.*$" % name_indicator,r"\1",name_area[0]))
                                    #without 'te', the piece of information behind the comma is more likely to be a person's location than their profession
                                    add_information(row, 17, re.sub(r"^.* %s .*?, (?![A-Z]\.)(([A-Z][A-Za-z-]*[ ,]+)*([A-Z][A-Za-z-]*\.)?).*?$" % name_indicator, r"\1", name_area[0])[:-1])
                                    print(row[17])
                                else:
                                    add_information(row, 15, re.sub(r"^.* %s (([A-Z][^A-Z]* |van |de([nrs])? )*).*$" % name_indicator,r"\1",name_area[0]))

                    #Indications of numbers (columns U [amounts of money], AC [repayment period] AD [interest] and AE [moment])
                    numbers = re.findall("(([^ ]+ +){0,2}[^ ]*([0-9][0-9,. /]*)?[0-9][¼½¾]?%? ([^ ]+ ){0,2})",ocr)
                    for number in numbers:
                        #Is it interest?
                        if re.search("[Pp]ct.|[Ii]nterest|%",number[0]):
                            add_information(row, 29, re.sub(r"^.*? (((f|ƒ|fr\.|frs\.) )?[0-9]+[¼½¾]?(%| pct.)?( 'sjaars)?)([ .,]+[^ .,]*)*?$",r"\1",number[0]))
                        #Is it a date/time?
                        elif re.search("[0-9] [^ ]+ [12][0-9]{3}",number[0]):
                            add_information(row, 30, re.sub(r"^.*[^0-9]([0123]?[0-9] [^ ]+ [12][0-9]{3}).*$",r"\1",number[0]))
                        elif re.search("[0-9] (januarij?|februarij?|maart|april|mei|juni|juli|augustus|september|o[ck]tober|november|december)[ ,.]",number[0],flags=re.IGNORECASE):
                            add_information(row, 30, re.sub(r"^(.+[^0-9])?([0123]?[0-9] [^ ,.]+)[ ,.].*$",r"\2",number[0]))
                        elif re.search("in [12][0-9]{3}",number[0]):
                            add_information(row, 30, re.sub(r"^.*in ([12][0-9]{3}).*$",r"\1",number[0]))
                        elif re.search("^([^ ]* )*?(nam\. |avonds te |)[0-9]{1,2} uur[ .,]",number[0]):
                            add_information(row, 30, re.sub(r"^([^ ]* )*?((nam\. )?[0-9]{1,2} uur)[ .,].*$",r"\2",number[0]))
                        #Is it a (repayment) period?
                        elif re.search("(?<!oud) [0-9]+ (jaar|jaren|maanden)(?! oud)",number[0]):
                            add_information(row, 28, re.sub(r"^.*[^0-9]([0-9]+ (jaar|jaren|maanden)).*$",r"\1",number[0]))
                        #Is it an amount of money?
                        elif re.search(" (f|ƒ|fr.) ([0-9][0-9,./ ]*)?[0-9][ ,.]",number[0]):
                            add_information(row, 20, re.sub(r"^.* ((f|ƒ|fr) ([0-9][0-9,./ ]*)?[0-9])[ ,.].*$", r"\1", number[0]))
                        elif re.search(" ([0-9][0-9,./ ]*)?[0-9] frs.[ ,.]",number[0]):
                            add_information(row, 20, re.sub(r"^.* (([0-9][0-9,./ ]*)?[0-9] frs.)[ ,.].*$", r"\1", number[0]))
                csv_writer.writerow(row)