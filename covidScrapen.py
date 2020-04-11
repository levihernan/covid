#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
from lxml import html
import pandas as pd
import numpy as np
from pymaran import gSheets,mail
import datetime


# In[18]:


def scrap2sheet(url, 
                xPath='//*[@id="main"]/div[1]/table/*', 
                tableElement=2, 
                autoDate=True, 
                manualDate='', 
                n_cols = 5):
    global tree
    
    ### https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Fallzahlen.html
    pageContent=requests.get(url)
    tree = html.fromstring(pageContent.content)
    table = tree.xpath(xPath)
    tbody = table[tableElement]
    df_col = range(n_cols)
    #df_col = ['city','total_cases','daily_cases','cases_per_M','total_deaths','']
    df = pd.DataFrame(columns=df_col)
    count = 0
    for tr in tbody:
        temp_data = []
        for td in tr:
            #print(td.text_content())
            temp_data.append(td.text_content())
        df.loc[count] = temp_data
        count += 1
    if autoDate:
        df.loc[:,'date'] = datetime.date.today()
        df['date'] = df['date'].astype(str)
    else:
        df['date'] = manualDate
    sheet = gSheets.readSheet('covidCrawlen')
    
        
    ### Save parsed data
    
    df[1] = pd.to_numeric(df[1])
    df[4] = pd.to_numeric(df[4])
    df.loc[df[1].apply(lambda x: ~ (float(x) == np.floor(x))),1] = df[1]*1000
    df.columns = ['city','total_cases','new_cases','deaths_per_M','total_deaths','date']
    df = df.reindex(['city','total_cases','total_deaths','date'],axis=1)
    sheet = gSheets.readSheet('covidCrawlen')
    worksheet = sheet.worksheet('data')
    for i,r in df.iterrows():
        worksheet.append_row(list(r))
    print('success' + str(datetime.date.today()))
    return df


# In[19]:


try:
    df = scrap2sheet(
        'https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Fallzahlen.html',
        '//*[@id="main"]/div[1]/table/*',
        2,
        True, 
        '', 
        5)
except:
    print('error' + str(datetime.date.today()))


# In[20]:





# In[ ]:




