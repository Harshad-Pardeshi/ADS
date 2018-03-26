import pip
def install(package):
   pip.main(['install', package])

#importing required packages
import urllib.request
import requests
import sys
import cgitb
import urllib3
import zipfile
import datetime
import io
import os 
import time
import glob
import pandas as pd
import numpy as np
import csv
import json
from bs4 import BeautifulSoup as bsoup
import matplotlib.pyplot as plt

import sklearn
from sklearn import datasets
from sklearn.preprocessing import LabelEncoder
from sklearn import linear_model
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import *

from pybrain.tools.shortcuts import buildNetwork
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer

# Create logfile.
logfile = open("Freddie-Mac-logs.txt", "a")
def log_entry(s):
    #print('Date now: %s' % datetime.datetime.now())

    timestamp = '[%s] : ' % datetime.datetime.now()
    log_line = timestamp + s + '\n'
    logfile.write(log_line)
    logfile.flush()

def getYear():
    #Taking data from user
    print("Please enter a year and quarter in config file(Example: Q12005)")
    with open('config.json') as json_file:    
        json_data = json.load(json_file)
    
    year_full=json_data["args"][0]
    try:
        year = int(year_full[2:])
        #print('year ',year)
        quarter = year_full[:2] 
        #print('quarter ',quarter)

        next_quarter = int(quarter[1:]) + 1
        next_year = year
        if next_quarter > 4:
            next_quarter = 1
            next_year = year+1
        next_year_full = "Q"+ str(next_quarter) + str(next_year)

        print(next_year_full)
        if(int(year) < 1999 or int(year) > 2016):
            print("Year can have only numeric values between 1999 and 2016")
            log_entry("Wrong Year to process : Year out of range")
        else:
            year = year_full
            next_year = next_year_full
            print(year,next_year)
            return year,next_year
    except Exception as e: 
        print("Year should be in format QNYYYY")
        log_entry("Wrong Year to process : Invalid format found in year")  

def get_login():
    url ="https://freddiemac.embs.com/FLoan/secure/auth.php"
    session = requests.session()
    
    with open('config.json') as json_file:    
        json_data = json.load(json_file)

    session_data = {'username':json_data["args"][1],
                  'password':json_data["args"][2]}

    r = session.post(url,data = session_data)
    #print(r.cookies)

    response = session.get("https://freddiemac.embs.com/FLoan/Data/download.php")
    #print(response.text)

    if 'Terms and Conditions' in response.text:
        session_data = {'username':json_data["args"][1] ,
                        'password':json_data["args"][2],
                        'accept':'Yes',
                        'action': 'acceptTandC',
                        'acceptSubmit':'Continue',
                        'accept.checked':'true'}

        r = session.post('https://freddiemac.embs.com/FLoan/Data/download.php',data = session_data)
        #print(r.text)

        response = session.get("https://freddiemac.embs.com/FLoan/Data/download.php")
        #print(response.content)
        return response,session

def get_historical_file_list():
    if not os.path.exists(directory):
        os.makedirs(directory)
    print(os.path.isdir(directory))
    historical_file_list = glob.glob(directory+'//historical_data*.txt')
    return historical_file_list
	
def get_sample_file_list():
    if not os.path.exists(directory):
        os.makedirs(directory)
    print(os.path.isdir(directory))
    historical_file_list = glob.glob(directory+'//sample*.txt')
    return historical_file_list

def getHistoricalData(current_year,next_year,response,session):
    url1 = 'https://freddiemac.embs.com/FLoan/Data/'
    soup= bsoup(response.text,'lxml')
    #print(url1)

    href = soup.findAll ('a',limit=None)

    fileList = get_historical_file_list()
    print("File list type=",type(fileList),sep=" ")
    for a in href:
        zip_file_url = url1+a['href']
        #print(zip_file_url)
        #print (os.getcwd())
        hist_data = directory + "\\\\" + a.text[:24]+'txt'
        hist_data_time = directory + "\\\\" + a.text[:17] + 'time_' + a.text[17:24] + 'txt'
        if current_year in zip_file_url:
            count = 0
            #if any(hist_data in s for s in fileList):
            #if hist_data in fileList:
            if any(current_year in s for s in fileList):
                count+= 1     
            if any(current_year in s for s in fileList):
                count+= 1
            if count != 2:
                print(zip_file_url)
                zfile = session.get(zip_file_url)
                #time.sleep(5)
                print(zfile)
                z = zipfile.ZipFile(io.BytesIO(zfile.content))
                z.extractall(directory)
            currData = hist_data
        if next_year in zip_file_url:
            count = 0
            if any(next_year in s for s in fileList):
                count = count + 1     
            if any(next_year in s for s in fileList):
                count = count + 1
            if count != 2:
                print(zip_file_url)
                zfile = session.get(zip_file_url)
                #time.sleep(5)
                print(zfile)
                z = zipfile.ZipFile(io.BytesIO(zfile.content))
                z.extractall(directory)
            nextData = hist_data        
    return currData,nextData
	
def getSampleData(current_year,next_year,response,session):
    url1 = 'https://freddiemac.embs.com/FLoan/Data/'
    soup= bsoup(response.text,'lxml')
    #print(url1)

    href = soup.findAll ('a',limit=None)

    fileList = get_sample_file_list()
    print("File list type=",type(fileList),sep=" ")
    for a in href:
        zip_file_url = url1+a['href']
        #print(zip_file_url)
        #print (os.getcwd())
        val_orig = 'sample_orig_'+a.text[7:11]+'.txt'
        val_svcg = 'sample_svcg_'+a.text[7:11]+'.txt'
        if 'sample' in zip_file_url:
            count = 0
            if any(val_orig in s for s in fileList):
                count+= 1     
            if any(val_svcg in s for s in fileList):
                count+= 1
            if count != 2:
                zfile = session.get(zip_file_url)
                z = zipfile.ZipFile(io.BytesIO(zfile.content))
                z.extractall(directory)
            currData = hist_data      
    #return currData

directory = 'all_data'
year,next_year = getYear()

response, session = get_login()
hist_data,hist_data_time = getHistoricalData(year,next_year,response,session)
datafile1=getSampleData(year,next_year,response,session)

#opening and reading file
with open(datafile1,"r") as file:
    data=file.readlines()

#Analysis 1:Find the frequency count of number of people taking loan in an area
print("Analysis 1:Find the frequency count of number of people taking loan in an area")
stateFrequency={}
for row in data:
    cell=row.split("|")
    #if state[16] == istate.strip():
    if cell[2] == "Y":
        if cell[16] not in stateFrequency:
            stateFrequency[cell[16]]=1
        else:
            stateFrequency[cell[16]]+=1
print(stateFrequency)

#generate plot
plt.bar(range(len(stateFrequency)), stateFrequency.values(), align='center')
plt.xticks(range(len(stateFrequency)), stateFrequency.keys())
width = 1/1.5
plt.show()

#Analysis 2:Find the state-wise frequency count of first time house buyers
print("Analysis 2:Find the state-wise frequency count of first time house buyers")
areaFrequency={}
for row in data:
    cell=row.split("|")
    #if state[16] == istate.strip():
    if cell[16] != '' and cell[18] != '':
        if cell[16] not in areaFrequency:
            areaFrequency[cell[16]]= {}
            areaFrequency[cell[16]][cell[18]]=1
        else:
            if cell[18] in areaFrequency[cell[16]].keys():
                areaFrequency[cell[16]][cell[18]]+=1
            else:
                areaFrequency[cell[16]][cell[18]] = 1
print(areaFrequency)

#Write the output in a csv
fields=['state','zipcode','count']
#with open("OutputAnalysis3.csv", "w") as f:
w = csv.DictWriter(sys.stdout, fields)
with open('PostalCode.csv','w',newline='') as out:
    writer = csv.DictWriter(out, fields)
    writer.writeheader()
    for key in areaFrequency:
        writer.writerow({field: areaFrequency[key].get(field) or key for field in fields})

print("Output has been saved in PostalCode.csv")		
		
#Analysis 3:Find the frequency count of Occupancy Status state-wise
print("Analysis 3:Find the frequency count of Occupancy Status state-wise")
OccupancyFrequency={}
for row in data:
    cell=row.split('|')
    if cell[7] != '' and cell[16] != '':
        if cell[16] not in OccupancyFrequency:
            OccupancyFrequency[cell[16]] = {}     
            OccupancyFrequency[cell[16]][cell[7]] = 1
        else:
            if cell[7] in OccupancyFrequency[cell[16]].keys():
                OccupancyFrequency[cell[16]][cell[7]]+= 1
            else:
                OccupancyFrequency[cell[16]][cell[7]] = 1
print(OccupancyFrequency)

#Write the output in a csv
fields=['state','O','I','S']
#with open("OutputAnalysis3.csv", "w") as f:
w = csv.DictWriter(sys.stdout, fields)
with open('OccupancyStatus.csv','w',newline='') as out:
    writer = csv.DictWriter(out, fields)
    writer.writeheader()
    for key in stateFrequency:
        writer.writerow({field: stateFrequency[key].get(field) or key for field in fields})
		
print("Output has been saved in OccupancyStatus.csv")

data = pd.read_csv('E:\\newtest\\historical_data1_time_Q12005.txt',delimiter='|', header=None)

header = ['LOAN_SEQUENCE_NUMBER','MONTHLY_REPORTING_PERIOD','CURRENT_ACTUAL_UPB','CURRENT_LOAN_DELINQUENCY_STATUS',
'LOAN_AGE','REMAINING_MONTHS_TO_LEGAL_MATURITY','REPURCHASE_FLAG','MODIFICATION_FLAG',
'ZERO_BALANCE_CODE','ZERO_BALANCE_EFFECTIVE_DATE','CURRENT_INTEREST_RATE','CURRENT_DEFERRED_UPB',
'DUE_DATE_OF_LAST_PAID_INSTALLMENT','MI_RECOVERIES','NET_SALES_PROCEEDS','NON_MI_RECOVERIES','EXPENSES','Legal_Costs',
'Maintenance_and_Preservation_Costs','Taxes_and_Insurance','Miscellaneous_Expenses','Actual_Loss_Calculation',
'Modification_Cost','']
curr_data = pd.DataFrame(data)
curr_data.columns = header

#Data Cleaning and pre-processing
curr_data['REPURCHASE_FLAG'] = curr_data['REPURCHASE_FLAG'].fillna('U')
curr_data['ZERO_BALANCE_CODE'] = curr_data['ZERO_BALANCE_CODE'].fillna('00')
curr_data['ZERO_BALANCE_EFFECTIVE_DATE'] = curr_data['ZERO_BALANCE_EFFECTIVE_DATE'].fillna('999912')

#deleting unknown columns which cannot be predicted
del curr_data['MODIFICATION_FLAG']
del curr_data['DUE_DATE_OF_LAST_PAID_INSTALLMENT']
del curr_data['MI_RECOVERIES']
del curr_data['NET_SALES_PROCEEDS']
del curr_data['NON_MI_RECOVERIES']
del curr_data['EXPENSES']
del curr_data['Legal_Costs']
del curr_data['Maintenance_and_Preservation_Costs']
del curr_data['Taxes_and_Insurance']
del curr_data['Miscellaneous_Expenses']
del curr_data['Actual_Loss_Calculation']
del curr_data['Modification_Cost']
del curr_data['']

#Analysis 4 and 5
print("Analysis 4 and 5")
for year in range(1999, 2016):
    with open("E:\\newtest\\sample_svcg_"+str(year)+".txt","r") as file:
        data = file.readlines()
        loanlist = []
        yearquarter = []
        for row in data:
            cell=row.split('|')
            if (cell[0],) not in loanlist:
                year = cell[0][2:4]
                quarter = cell[0][4:6]
                yearquarter.append((year,quarter))
                loanlist.append((cell[0],))
    
    with open("yearquarter"+str(year)+".csv",'w',newline='') as item:
        wr = csv.writer(item)
        wr.writerow(['Year','Quarter'])
        for row in yearquarter:
            wr.writerow(row)
        
    tup = (str(year),len(loanlist))
    with open("loanlist"+str(year)+".csv",'a', newline='') as item:
        count = 0
        wr = csv.writer(item)
        wr.writerow(['Year','Loan'])
        #for row in loanlist:
        wr.writerow(tup)