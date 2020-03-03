#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import json
from datetime import datetime
import os
from pathlib import Path
import pandas as pd
import sys
from compilation import *

url = 'https://ipt.pricefx.eu/classic/priceFxWeb.html?locale=en#loginPage'

# initialise current_date_year to None first
current_date_year = None

# if user passes in argument, make it the month/year
if len(sys.argv) > 1:
    current_date_year = sys.argv[1]
else:
    current_date_year = str(datetime.now().month) + '_' + str(datetime.now().year)

userid = os.environ['username']
partition = 'aaap'
pw = os.environ['password']


options = webdriver.ChromeOptions()

download_path = os.path.join(os.getcwd(),'files',current_date_year)

# Makes a new folder of the month's file the programme is suppose to download.
try:
    Path(download_path).mkdir(parents=True)
except FileExistsError:
    print('Folder already exists. Continuing..')

options.add_experimental_option('prefs',{"download.default_directory": download_path})
options.add_argument('headless')
driver = webdriver.Chrome('/usr/local/bin/chromedriver',options=options)
delay = 10 # set delay for loading browser

# wait for login page to load
retry = 0
success = False
while retry < 5:
    try:
        driver.get(url)

        myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'isc_W'))) # find if isc_W exists
        print("Page is ready!")
        
        driver.find_element_by_id('isc_W').send_keys(userid)
        driver.find_element_by_id('isc_10').send_keys(partition)
        driver.find_element_by_id('isc_14').send_keys(pw)
        driver.find_element_by_id('isc_Q').click() #login button
        success = True
        break
    except TimeoutException:
        print("Loading took too much time!\nReattempting login")
        retry += 1
if success == False:
    print('Failed to login. Killing browser.')
    driver.close()
else:
    retry = 0
    success = False

# wait for home page to load
try:
    myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'sectionHeaderopened'))) # make sure login complete
    print('Homepage Loaded.')
except TimeoutException:
    print("Did not load in time!")
    

# create script to generate output of 500 records. data sorted by lastUpdateDate

script = """
    var url = "https://ipt.pricefx.eu/pricefx/aaap/quotemanager.fetchlist?dataLocale=default&onConflict=validationError&isc_dataFormat=json";

    data = {
        "operationType":"fetch", 
        "startRow":0, 
        "endRow":1000, 
        "sortBy":[
            "-lastUpdateDate"
        ], 
        "textMatchStyle":"exact", 
        "data":{
        }, 
        "oldValues":null
    }
    
    var output = await fetch(url,{method:'POST', body:JSON.stringify(data)})
                .then(function(response){
                    return Promise.resolve(response)
                })
                .then(function(response){
                    return response.json()
                });
    return output
"""

output = driver.execute_script(script)

data = output['response']['data']

# Create dataframe
df = pd.DataFrame(data)
print("Current date", current_date_year)
df['createDate'] = df['createDate'].apply(lambda x: datetime.strptime(x,'%Y-%m-%dT%H:%M:%S'))
# extract out month and year from createDate records - "month/year"
df['month_year'] = df.createDate.apply(lambda x: str(x.month) + '_' + str(x.year) )
df['day'] =  df.createDate.apply(lambda x: int(x.day))
# get dataframe that matches DEAL and current month
current_month = df[(df['month_year'] == current_date_year) & (df['quoteStatus'] == "DEAL")]

#extract all the listing numbers
listing = list(current_month.rootUniqueName)
print("Number of Files in system for the current month: ",len(listing))

exisiting_files = os.listdir(download_path)
all_urls_to_download = [f"https://ipt.pricefx.eu/pricefx/aaap/quotemanager.fetchxls/{listing_num}?templateName=P" for listing_num in listing if listing_num+'.xlsm' not in exisiting_files ]

print("Current Number of files: ", len(exisiting_files))
print("Number of new files to download: ", len(all_urls_to_download))

def downloadfile(url,driver):
    print('Downloading:' , url)
    driver.get(url)

for i in all_urls_to_download:
    downloadfile(i,driver)

# wait for last file to finish downloading
sleep(1)

for i in os.listdir(download_path):
    if i.endswith('.xlsm') and '_' in i:
        filename = i.split('_')[0] + '.xlsm'
        print(f'renaming file {i} to {filename}')
        os.rename(os.path.join(download_path,i),os.path.join(download_path,filename))

print('Closing Driver')
driver.close()

# execute script to download all files
main(current_date_year)

categories = {
    'rebook': 'rebook|rebooking',
    'stock': 'stock clearance|sell out',
    'warranty': 'warranty',
    'promo': 'campaign|special promotion|promo',
    'volume': 'volume'
}


def create_category_file(current_month_df, categories, category):
    columns = [
        "SKU",
        "Customer",
        "Deal Reason",
        "QuoteQuantity",
        "Business Unit",
        "Product Group 3",
        "Net Price",
        "Net Price Unit",
        "IPP Current",
        "IPP New",
        "FEPAA"
    ]

    file = current_month[current_month['label'].str.lower().str.contains(categories[category])]
    listing = list(file.rootUniqueName)

    df_init = pd.DataFrame(columns=columns)
    for i in listing:
        file = os.path.join(download_path,i+'.xlsm')
        df_init = combinefile(file,df_init,columns)
    filename =  current_date_year + f'_PriceFxData_{category}.csv'
    df_init.SKU = df_init.SKU.apply('="{}"'.format)
    df_init.to_csv(os.path.join(os.getcwd(),'output',filename), index=False)


# create files separated into respective categories
create_category_file(current_month,categories, 'rebook')
create_category_file(current_month,categories, 'stock')
create_category_file(current_month,categories, 'warranty')
create_category_file(current_month,categories, 'promo')
create_category_file(current_month,categories, 'volume')
