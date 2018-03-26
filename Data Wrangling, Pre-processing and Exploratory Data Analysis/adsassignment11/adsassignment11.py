#import pip
#def install(package):
   #pip.main(['install', package])

#install('BeautifulSoup4')
#install('HTMLParser')
#install('urllib')
#install('BeautifulSoup')

import urllib.request
#from lxml.html import parse 
from urllib.request import urlopen
from bs4 import BeautifulSoup as bsoup
import re
import csv
import os
import zipfile
import json
import glob

import numpy as np
import pandas as pd
import requests
import datetime

#import statements for s3 bucket
import boto
import boto.s3
import sys
from boto.s3.key import Key

# Create logfile.
logfile = open("CIK-logs.log", "a")
def log_entry(s):
   #print('Date now: %s' % datetime.datetime.now())

   timestamp = '[%s] : ' % datetime.datetime.now()
   log_line = timestamp + s + '\n'
   logfile.write(log_line)
   logfile.flush()
   
   # Also write to standard output as a convenience.
   #print(log_line)

def getURL(CIK,accession_key):
    
    middle_key=re.sub("-","",accession_key)
    print(middle_key)
    
    try:
        url=urllib.request.urlopen('https://www.sec.gov/Archives/edgar/data/'+ str(CIK) +'/'+str(middle_key) +'/'+ str(accession_key) + '-index.html')
        #url = urllib.request.urlopen('https://www.sec.gov/Archives/edgar/data/51143/000005114313000007/0000051143-13-000007-index.html')
        print('https://www.sec.gov/Archives/edgar/data/'+ str(CIK) +'/'+str(middle_key) +'/'+ str(accession_key) + '-index.html')
        log_entry("Generated URL is {url}: ".format(url=url))
        content3= url.read()
        soup3= bsoup(content3,'html.parser')
    except Exception as er:
        log_entry("Wrong URL generated. {url}".format(url='https://www.sec.gov/Archives/edgar/data/'+ str(CIK) +'/'+str(middle_key) +'/'+ str(accession_key) + '-index.html'))
        sys.exit()
        
    #find the 10q link
    #actual link: '/Archives/edgar/data/51143/000005114313000007/ibm33q3_10q.htm'
    #reg ex link: '^(.*?)\_10q\.htm$'
    link = ""
    for link in soup3.find_all('a', href=re.compile('^(.*?)\_10q\.htm$')):
        link=link.get('href')
        log_entry("Generated 10q link: {link}".format(link=link))
    
    if link == "":
        for link in soup3.find_all('a', href=re.compile('^(.*?)10\-kq(.*?)\.htm$')): 
            link=link.get('href') 
            log_entry("Generated 10K link :{link}".format(link=link))
    
    if link == "":
        print("Please enter a valid CIK or Accession key. It is invalid..!!")
        log_entry("Entered CIK and Accession_key is invalid.")
    
    else:
        url4='https://www.sec.gov'+link
        print(url4)
        return url4

def getCIK_and_Accession_key():
    #Taking data from user
    """CIK=input("Please enter a CIK number")
    fullCIK = CIK.zfill(10)
    accession_key=input("Please enter a accession_key number")
    """    
    #reading data from Json file(config.json)
    with open('config.json') as data_file:    
        data = json.load(data_file)
    
    log_entry("CIK={CIK}, Accession_Key={Accession_Key}: ".format(CIK=data["args"][0],Accession_Key=data["args"][1]))
    return data["args"][0],data["args"][1]

def getAmazonS3keys():
    #Taking data from user
    """S3=input("Please enter your Amazon S3 Access Key ID:")
    SSK=input("Please enter your Amazon S3 Secret Access Key:")
    """    
    #reading data from Json file(config.json)
    with open('config.json') as data_file:    
        data = json.load(data_file)
    log_entry("Read Amazon keys from config file")
    return data["args"][2],data["args"][3]

def tableToCSV(fname, t, bodyStart):
    print("filename = " +fname)
    
    cCount = 0
    rCount = 0
    column = []
    consistent_table = True
    custom_headers = False

    rows = t.find_all("tr")
    rCount = len(rows)
    
    # Find the shape of the table.
    for r in rows:
        # It's best if there's a header row with explicit column names.
        #header_cells = r.find_all("th")

        # If there are no header elements, just use a normal row.
        data_cells = r.find_all("td")
        row_columns = len(data_cells)
        if ((cCount == 0) | (row_columns > cCount)):
            cCount = row_columns
    
    if len(column) == 0:
        # found no column headers, so use integers
        column = range(0, cCount)
    
     # Create the dataframe.
    data = pd.DataFrame(columns=column, index=range(0, rCount))
    
    # Now insert the data into the dataframe.
    current_row = 0
    for r in rows:
        # Get each cell and put it into the dataframe.
        # Skip the header by only considering 'td' elements.
        # print(r)
        
        padding = ""

        if(int(bodyStart) > current_row):
            isHeader = True
        else:
            isHeader = False
            
        data_cells = r.findAll("td")
        #print(data_cells)
        current_column = 0
        
        if(data_cells[0].get_text().strip() == ""):
            first_cell_blank = True
        else:
            first_cell_blank = False
            
        for dc in data_cells:
            value = dc.get_text().strip()
            
            if not first_cell_blank:
                padding = ""
            
            if isHeader:
                data.iat[current_row, current_column] = value.replace("\n"," ").strip()
                current_column += 1
            else:
                if value is not "" and value is not "$":
                    data.iat[current_row, current_column] = str(padding) + str(value.replace("\n"," ")).strip()
                    first_cell_blank = False
                    if not first_cell_blank:
                        current_column += 1
                        padding = "\t" + padding
                        #print('11111')
        
        current_row += 1
    
    # Strip any columns that contain no data.
    data.dropna(axis=1, how='all', inplace=True)

    # Strip any rows that contain no data.
    data.dropna(axis=0, how='all', inplace=True)
    
    # If we didn't find custom column names, we can rename the columns to be consecutive integers.
    if not custom_headers:
        data.columns = range(0,len(data.columns))
        #print(data)

    # Replace any remaining NA values with empty strings.
    data.fillna(value="", axis=0, inplace=True)
    #print(data)
    
    # Write the dataframe to a CSV file.
    data.to_csv(fname, encoding='utf-8')
    
    log_entry("CSV ganarated from table")
    return True

def get_body_start(table):
    count = 0
    trs = table.findAll("tr")
    for tr in trs:
        tds = tr.findAll("td")
        if(tds[0].get_text().strip() == ""):
            count += 1
        else:
            log_entry("Body of this table starts with {count}: ".format(count=count))
            return count
    log_entry("Body of this number starts with {count}: ".format(count=count))
    return 0

CIK,accession_key = getCIK_and_Accession_key()

url = getURL(CIK,accession_key)
if url!="":
    response = requests.get(url)
    r = requests.head(url)
    page = bsoup(response.text, 'html.parser')
#if r.status_code == 200:
#    print("The url exists")
#else:
#    print("The url does not exists. Pleas choose a valid CIK or Accession key")
#page

tables = page.findAll("table",{"style" : "border:none;border-collapse:collapse;width:100%;"})
i = 0
for table in tables:
    headers = table.parent.parent#.get_text().replace("\n"," ").strip()
    childdiv = headers.find_all('div')
    fName = childdiv[0].getText()[:50].replace("\n"," ") 
    #print("-----------------------------------------------------------------------")
    tableToCSV(str(CIK) + "-" +str(i).zfill(2) + "-" + fName + ".csv", table, get_body_start(table))
    i = i+1

zFolder = zipfile.ZipFile('zip_'+str(CIK)+'.zip', 'w')
for folder, subfolders, files in os.walk('.\\'):
    for file in files:
        if file.startswith(str(CIK)):
            zFolder.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file),'.\\'),compress_type = zipfile.ZIP_DEFLATED)

log_entry("Zip folder has been created.")            
print("The zip folder is created on the current directory.")
zFolder.close()

#uploading files to AWS S3 bucket

accessKey,secretKey=getAmazonS3keys()
AWS_ACCESS_KEY_ID = accessKey
AWS_SECRET_ACCESS_KEY = secretKey
TeamNumber='team10'

bucket_name = TeamNumber+ 'ads-assignment-1'
conn = boto.connect_s3(AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY)

try:
    bucket = conn.create_bucket(bucket_name,location=boto.s3.connection.Location.DEFAULT)
    log_entry("Connection with Amazon S3 bucket is successful.")
except Exception as e:  
    log_entry("Amazon access key or secret key is invalid")
    print("Amazon access key or secret key is invalid")
    sys.exit()
    
#uploading multiple files
filenames=[]
#filenames =glob.glob(".\\'zip_"+str(CIK)+".zip")
filenames.append("CIK-logs.log")
filenames.append("zip_"+str(CIK)+".zip")


def percent_cb(complete, total):
    sys.stdout.write('.')
    sys.stdout.flush()

for fname in filenames:
    bucket = conn.get_bucket(bucket_name)
    key = bucket.new_key(fname).set_contents_from_filename(fname,cb=percent_cb, num_cb=10)
    print ("uploaded file %s" % fname)
    log_entry("{fname} has been uploaded.".format(fname=fname)) 
    
