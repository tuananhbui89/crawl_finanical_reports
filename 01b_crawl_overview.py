import numpy as np 
import pandas as pd
from bs4 import BeautifulSoup
import urllib.request as ur
from urllib.request import Request, urlopen

# url_ = 'https://www.marketwatch.com/investing/stock/bub?countrycode=au&mod=mw_quote_tab'
url_ = 'https://www.marketwatch.com/investing/stock/clv/company-profile?countrycode=au&mod=mw_quote_tab'


req = Request(url_, headers={'User-Agent': 'Mozilla/5.0'})    
read_data = urlopen(req).read()
soup_is= BeautifulSoup(read_data,'lxml')

print(soup_is)

ls= [] # Create empty list
for l in soup_is.find_all('div'): 
    #Find all data structure that is ‘div’
    ls.append(l.string) # add each element one by one to the list


exclude_keys = [
    'Operating Expenses',
    'Non-recurring Events',
]
ls = [e for e in ls if e not in exclude_keys] # Exclude those columns

new_ls = list(filter(None,ls))

with open('temp.txt', 'w') as writer: 
    writer.write(str(soup_is))
