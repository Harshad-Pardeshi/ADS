#import libraries
from bs4 import BeautifulSoup
import pandas as pd
import urllib
import requests
import zipfile
import datetime
import csv
import json
import boto
import boto.s3
import sys
from boto.s3.key import Key

# Create logfile.
logfile = open("edgar-year-logs.txt", "a")
def log_entry(s):
    #print('Date now: %s' % datetime.datetime.now())

    timestamp = '[%s] : ' % datetime.datetime.now()
    log_line = timestamp + s + '\n'
    logfile.write(log_line)
    logfile.flush()
    
    # Also write to standard output as a convenience.
    #print(log_line)

def mode(df, key_cols, value_col, count_col):
    return df.groupby(key_cols + [value_col]).size() \
             .to_frame(count_col).reset_index() \
             .sort_values(count_col, ascending=False) \
             .drop_duplicates(subset=key_cols)
			 
def getYear():
    #Taking data from user
    """CIK=input("Please enter a CIK number")
    fullCIK = CIK.zfill(10)
    accession_key=input("Please enter a accession_key number")
    """    
    #reading data from Json file(config.json)
    with open('config.json') as data_file:    
        data = json.load(data_file)
    
    log_entry("Year={year} : ".format(year=data["args"][0]))
    return data["args"][0]
	
def getAmazonS3keys():
    #Taking data from user
    """S3=input("Please enter your Amazon S3 Access Key ID:")
    SSK=input("Please enter your Amazon S3 Secret Access Key:")
    """    
    #reading data from Json file(config.json)
    with open('config.json') as data_file:    
        data = json.load(data_file)
    log_entry("Read Amazon keys from config file")
    return data["args"][1],data["args"][2]

#Read the year from config file
f_metadata = "https://www.sec.gov/data/edgar-log-file-data-set.html"
response = requests.get(f_metadata)
soup = BeautifulSoup(response.text, 'html.parser')
input_year = getYear()
try:
    int(input_year)
except Exception as e: 
    print("Year can have only numeric values")
    log_entry("Wrong Year to process : Non nuumeric vaues found in year")
if(int(input_year) < 2003 or int(input_year) > 2016):
    print("Year can have only numeric values between 2003 and 2016")
    log_entry("Wrong Year to process : Year out of range")
else:
    year = int(input_year)
    log_entry("Year to process : {year}".format(year=year))

# Months in the year and the quarter to which a month belongs are constants.
import zipfile, io
months_dict = [{"month":"01", "quarter":1}, {"month":"02", "quarter":1}, {"month":"03", "quarter":1},
              {"month":"04", "quarter":2}, {"month":"05", "quarter":2}, {"month":"06", "quarter":2},
              {"month":"07", "quarter":3}, {"month":"08", "quarter":3}, {"month":"09", "quarter":3},
              {"month":"10", "quarter":4}, {"month":"11", "quarter":4}, {"month":"12", "quarter":4}]

filenames = []
for m in months_dict:
    url = "http://www.sec.gov/dera/data/Public-EDGAR-log-file-data/{y}/Qtr{quarter}/log{y}{month}01.zip".format(y=year, month=m['month'], quarter = str(m['quarter']))
    log_entry("Downloading the zip file for year {year}, from {url} : ".format(year=year, url=url))
    print(url)
    filename = {'url':url,'filename':"log" + str(year) + m['month'] + "01.zip"}
    filenames.append(filename)
    log_entry("Saving the file for year : {year} {filename}: ".format(year=year, filename=filename))
    zfile = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(zfile.content))
    z.extractall()
    
print(filenames)

for num in range(1,13):
    currFile = "log{y}".format(y=year)+str(num).zfill(2)+"01.csv"
    log_entry("Opening file {filename} to handle missing data".format(filename=currFile))

    df = pd.read_csv(currFile)
    
    #Remove rows with null CIK
    df = df[df['cik'].notnull()]
    
    #Replace size of file by the mean of size of file of that (CIK and IP) and CIK 
    try:
        df['size'] = df['size'].fillna(df.groupby(['cik','ip'])['size'].transform('mean'))
        df['size'] = df['size'].fillna(df.groupby('cik')['size'].transform('mean'))
        df.to_csv("Clean_"+currFile, sep=',', encoding='utf-8')
        mode_browser = mode(df, ['cik'], 'browser', 'browswe_count')
    except Exception as er:
        log_entry("No numeric data to aggrigate: {year}".format(year=year))
    
    df['size'] = df['size'].fillna(0)
    
    

    #print(mode_browser)
    df = pd.merge(df, mode_browser, how='inner', on=['cik'], left_on=None, right_on=None,
         left_index=False, right_index=False, sort=True,
         suffixes=('', '_sub'), copy=True, indicator=False)
    
    #df.drop('browser', axis=1, inplace=True)
    
    #Add a new Column with time includind hh:mm
    df['time_only'] = df['time'].map(lambda x: str(x)[:5])
    
    #Sum of size of files by time 
    df['size_by_time'] = df['size'].groupby(df['time_only']).transform('sum')
    
    
    #print(df)
    log_entry("Writing modified data to file {filename}".format(filename=currFile))
    df.to_csv("Clean_"+currFile, sep=',', encoding='utf-8')

comb = open("logCombine{y}.csv".format(y=year), "a")
#testing 1 file
currFile = "log{y}0101.csv".format(y=year)
log_entry("Merging File {filename} into {MergeFile} : ".format(filename=currFile, MergeFile=comb))
for line in open (currFile):
    comb.write(line)
    
#combining all files of a particular year
for num in range(2,13):
    currFile = "log{y}".format(y=year)+str(num).zfill(2)+"01.csv"
    log_entry("Merging File {filename} into {MergeFile} : ".format(filename=currFile, MergeFile=comb))
    f = open(currFile)
    #print(str(num).zfill(2))
    next(f) #to skip the header
    for line in f:
        comb.write(line)
    f.close()
comb.close()

#uploading files to AWS S3 bucket

accessKey,secretKey=getAmazonS3keys()
AWS_ACCESS_KEY_ID = accessKey
AWS_SECRET_ACCESS_KEY = secretKey
TeamNumber='team10'

bucket_name = TeamNumber+ 'ads-assignment-1-Part2'
conn = boto.connect_s3(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY)

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
filenames.append("edgar-year-logs.txt")
filenames.append("logCombine{y}.csv".format(y=year))


def percent_cb(complete, total):
    sys.stdout.write('.')
    sys.stdout.flush()

for fname in filenames:
    bucket = conn.get_bucket(bucket_name)
    key = bucket.new_key(fname).set_contents_from_filename(fname,cb=percent_cb, num_cb=10)
    print ("uploaded file %s" % fname)
    log_entry("{fname} has been uploaded.".format(fname=fname)) 
    
