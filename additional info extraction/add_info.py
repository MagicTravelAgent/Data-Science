# -*- coding: utf-8 -*-
"""
Created on Wed Apr  7 10:25:23 2021

@author: burtibo
"""

# extracted:
    #geographical location
    #year
    #is it demand or supply - vraag, aanbod, bieden, 
    #actor(private of company)
    
import pandas as pd  
import re
writer = pd.ExcelWriter('demo.xlsx', engine='xlsxwriter')

#list of cities in the Netherlands
cities_dir=""
txt_cities = open(cities_dir, encoding="utf8")
cities_list = txt_cities.read().strip()

#extracted info as arrays to put into excel
entry_ = []
vraag=[]
aanbod=[]
year=[]
company=[]
individual=[]
cities=[]

#k is the entry_ number, so it is the number of the adverts
k=0
while k<200:
    try: 
        #open adverts
        txt_file = open(r"\directory where you stored your files with this (so it can loop though files(k))->\entry_{}.txt".format(k), encoding="utf8")
        text = txt_file.read().strip()
        
        #entry
        entry_.append(k)
       
        #vraag
        if 'vraag' in text:
            vraag.append('vraag')
        else: 
            vraag.append('-')
       
        #aanbod
        if 'bied' in text or 'bod' in text or 'aanbod' in text:
            aanbod.append('aanbod')
        else:
            aanbod.append('-')
            
        
        #company 
        if 'bank' in text or 'kantoor' in text or 'kantore' in text or 'bedrijf' in text:
            company.append('company')
        else: 
            company.append('-')
        
        #individual
        if 'notaris' in text or 'erven'in text:
            individual.append('individual')
        else: 
            individual.append('-')
            
        #year
        year_sub=[]
        year_str = re.findall('\d{4}', text)
        if len(year_str)>0:
            for i in range(len(year_str)):
                year_int = int(year_str[i])
                if year_int>1700 and year_int<2000:
                        year_sub.append(year_int)
        year.append(year_sub)
        
        #location
        cities_sub=[]
        for x in cities_list.split('\n'):
            if x in text:
                cities_sub.append(x)
        cities.append(cities_sub)        
       
        k=k+1
    except OSError:
        k=k+1        

#test if everything is ok
print(vraag)
print(aanbod)   
print (year)  
print(company)   
print (individual)
print(cities)

#save to the excel file
update = pd.DataFrame({"entry_": entry_, 'vraag':vraag, 'aanbod': aanbod, 'company': company, "individual":individual, 'year':year, 'location':cities})   
update.to_excel(r"\save it there-directiry.xlsx", index= False)

