#!/usr/bin/env python
# coding: utf-8

# In[14]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.xkcd()
import seaborn as sns
import datetime
from pymaran import gSheets
import io
import requests
from dateutil.rrule import rrule, MONTHLY


# # Get Data

# In[15]:


### Germany
de = pd.DataFrame(gSheets.readSheet('covidCrawlen').worksheet('data').get_all_values())
de.columns = de.iloc[0]
de = de[1:]


# In[40]:


de.loc[de['city']=='Nordrhein-West­falen','city'] = "Nordrhein-Westfalen"
de.loc[de['city']=='Rhein­land-Pfalz','city'] = "Rheinland-Pfalz"
de.loc[de['city']=='Schles­wig-Holstein','city'] = "Schleswig Holstein"
de.loc[de['city']=='Schleswig Holstein','city'] = "Schleswig-Holstein"
de.loc[de['city']=='Baden-Württem­berg','city'] = "Baden-Wurttemberg"
de.loc[de['city']=='Baden-Württemberg','city'] = "Baden-Wurttemberg"
de.loc[de['city']=='Mecklenburg-Vor­pommern','city'] = "Mecklenburg-Vorpommern"
de.loc[de['city']=='Mecklenburg-\nVor­pommern','city'] = "Mecklenburg-Vorpommern"
de.loc[de['city']=='Thüringen','city'] = "Thuringen"
de.loc[de['city']=='Gesamt','city'] = "Total"


# In[17]:


de['total_cases'] = pd.to_numeric(de['total_cases'])
de['old_date'] = pd.to_datetime(de['date'],format='%d/%m/%Y',errors='coerce')
de['new_date'] = pd.to_datetime(de['date'],format='%Y-%m-%d',errors='coerce')
de['date'] = de['old_date'].fillna(de['new_date'])
de.drop(columns=['old_date','new_date'], inplace=True)


# In[18]:


### World
url="https://datahub.io/core/covid-19/r/time-series-19-covid-combined.csv"
s=requests.get(url).content
c=pd.read_csv(io.StringIO(s.decode('utf-8')))


# In[19]:


c['Date'] = pd.to_datetime(c['Date'])
world = c.groupby(['Country/Region','Date'])['Confirmed'].sum().reset_index()
world.columns = ['country','date','cases']


# ## Process

# In[20]:


def getAvg(x,days=7):
    global story
    story = []
    for i in range(days):
        if i is not np.NaN:
            story.append(x.shift(i)['growth'])
            
    #return np.mean([x[-1:].values for x in story])
    return pd.DataFrame([x[:] for x in story]).apply(lambda x: np.mean(x),axis=0)


# In[21]:


def processCases(df,group='city',var='total_cases'):
    df = df.sort_values('date')
    day_data = df.groupby(group).apply(lambda x: x[[var]] -  x.shift(1)[[var]])
    day_data.columns = ['growth']
    active_data = df.groupby(group).apply(lambda x: x[[var]] -  x.shift(14)[[var]].fillna(0))
    active_data.columns = ['active cases']
    df = df.join(day_data,rsuffix='_')
    df = df.join(pd.DataFrame(df.groupby(group).apply(lambda x: getAvg(x,7)),columns=['avg growth']).reset_index().set_index('level_1').drop(group,axis=1))
    df = df.join(active_data)
    return df


# In[22]:


total = world.groupby('date')['cases'].sum().reset_index()
total['country'] = 'World'


# In[23]:


world = world.append(total).reset_index(drop=True)


# In[24]:


de = processCases(de)
world = processCases(world,'country','cases')


# In[25]:


de.columns = ['city', 'total cases', 'total deaths', 'date', 'growth', 'avg growth',
       'active cases']
world.columns = ['country', 'date', 'total cases', 'growth', 'avg growth', 'active cases']


# In[41]:


countryList = ['Argentina','Mexico','Finland','New Zealand','Australia','Spain','United Kingdom','China','US','Iran','Germany','Brazil','France','Italy','Korea, South']
cityList= ['Berlin','Bayern','Bremen','Hamburg','Hessen','Thuringen','Niedersachsen','Total','Nordrhein-Westfalen','Baden-Wurttemberg']


# ### new cases vs total_cases

# In[37]:


world['country'].nunique()


# In[27]:


w = world[world['country'].isin(countryList)]
w.sort_values(['country','date'],inplace=True)


# In[28]:


def datePlot(title,file,
             data, var='total cases',hue='country'):
    months = [dt for dt in rrule(MONTHLY, dtstart=data['date'].min().replace(day=1), until=data['date'].max())]
    fig,ax = plt.subplots(figsize=(13,7))
    plt.title(title)
    sns.lineplot('date',var,hue=hue,
                 data=data)
    ax.set_xticks(months)
    ax.set_xlim(data['date'].min(), data['date'].max() + datetime.timedelta(days=14))
    for i,ls in data.sort_values(var,ascending=False).groupby(hue).first().iterrows():
        ax.annotate(i,(ls['date'],ls[var]),clip_on=True)
    plt.savefig(file)


# In[104]:


def datePlotU(title,date,file,
             data, var='total cases',hue='country'):
    months = [dt for dt in rrule(MONTHLY, dtstart=data['date'].min().replace(day=1), until=data['date'].max())]
    fig,ax = plt.subplots(figsize=(13,7))
    plt.title(title)
    plt.suptitle('(last updated '+ str(date) +')',fontsize=12, y=0, alpha=0.5)

    sns.lineplot('date',var,hue=hue,
                 data=data)
    ax.set_xticks(months)
    ax.set_xlim(data['date'].min(), data['date'].max() + datetime.timedelta(days=14))
    for i,ls in data.sort_values(var,ascending=False).groupby(hue).first().iterrows():
        ax.annotate(i,(ls['date'],ls[var]),clip_on=True)
    plt.savefig(file)


# In[30]:


def logPlot(title,file,
            data,hue='country',x='total cases',y='avg growth',
            autoLim=True,xlim=[10**4,10**6.5],ylim=[10**4,10**6.5],
            legend=True
           ):
    
    fig,ax = plt.subplots(figsize=(13,10))
    plt.title(title)

    sns.lineplot(x,y,hue=hue,sort=False,
                 data=data)
    
    if autoLim:
        ax.set_xlim([10,data[x].max()*10**0.5])
        ax.set_ylim([10,data[y].max()*10**0.5])
    else:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
            
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    if legend:
        ax.legend(loc='upper left')
    else:
        ax.legend().remove()

    for i,ls in data.groupby(hue).last().iterrows():
        ax.annotate(i,(ls[x],ls[y]),clip_on=True)

        
    plt.savefig(file)


# In[30]:


def logPlotU(title,date,file,
            data,hue='country',x='total cases',y='avg growth',
            autoLim=True,xlim=[10**4,10**6.5],ylim=[10**4,10**6.5],
            legend=True
           ):
    
    fig,ax = plt.subplots(figsize=(13,10))
    plt.title(title)
    plt.suptitle('(last updated '+ str(date) +')',fontsize=12, y=0, alpha=0.5)

    sns.lineplot(x,y,hue=hue,sort=False,
                 data=data)
    
    if autoLim:
        ax.set_xlim([10,data[x].max()*10**0.5])
        ax.set_ylim([10,data[y].max()*10**0.5])
    else:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
            
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    if legend:
        ax.legend(loc='upper left')
    else:
        ax.legend().remove()

    for i,ls in data.groupby(hue).last().iterrows():
        ax.annotate(i,(ls[x],ls[y]),clip_on=True)

        
    plt.savefig(file)


# In[105]:


datePlotU('total cases','2020-04-10','test.png',w)

