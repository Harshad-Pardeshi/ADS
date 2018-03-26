import pip
def install(package):
   pip.main(['install', package])

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
import csv
import json

from bs4 import BeautifulSoup as bsoup
import sklearn
from sklearn import datasets
import numpy as np
from sklearn.preprocessing import LabelEncoder

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

def get_file_list():
    if not os.path.exists(directory):
        os.makedirs(directory)
    #print(os.path.isdir(directory))
    historical_file_list = glob.glob(directory+'//historical_data*.txt')
    return historical_file_list

def getData(current_year,next_year,response,session):
    url1 = 'https://freddiemac.embs.com/FLoan/Data/'
    soup= bsoup(response.text,'lxml')
    #print(url1)

    href = soup.findAll ('a',limit=None)

    fileList = get_file_list()
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
            currData = hist_data_time
        if next_year in zip_file_url:
            print('yes')
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
            nexData = hist_data_time       
    return currData,nexData

def df_strip(df):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == np.object:
            df[c] = pd.core.strings.str_strip(df[c])
        df = df.rename(columns={c:c.strip()})
    return df

def missing_values_table(df): 
        mis_val = df.isnull().sum()
        mis_val_percent = 100 * df.isnull().sum()/len(df)
        mis_val_table = pd.concat([mis_val, mis_val_percent], axis=1)
        mis_val_table_ren_columns = mis_val_table.rename(
        columns = {0 : 'Missing Values', 1 : '% of Total Values'})
        return mis_val_table_ren_columns 

def add_header(data):
    header = ['LOAN_SEQUENCE_NUMBER','MONTHLY_REPORTING_PERIOD','CURRENT_ACTUAL_UPB','CURRENT_LOAN_DELINQUENCY_STATUS',
              'LOAN_AGE','REMAINING_MONTHS_TO_LEGAL_MATURITY','REPURCHASE_FLAG','MODIFICATION_FLAG',
              'ZERO_BALANCE_CODE','ZERO_BALANCE_EFFECTIVE_DATE','CURRENT_INTEREST_RATE','CURRENT_DEFERRED_UPB',
              'DUE_DATE_OF_LAST_PAID_INSTALLMENT','MI_RECOVERIES','NET_SALES_PROCEEDS','NON_MI_RECOVERIES','EXPENSES','Legal_Costs',
              'Maintenance_and_Preservation_Costs','Taxes_and_Insurance','Miscellaneous_Expenses','Actual_Loss_Calculation',
              'Modification_Cost']
    curr_data = pd.DataFrame(data)
    curr_data.columns = header
    return curr_data

def ConvertToNumeric1(curr_data): 
    #CreditScore - Mean
    
    #print(curr_data[curr_data['CURRENT_LOAN_DELINQUENCY_STATUS'] == 'R'] = 1)
    curr_data = curr_data[pd.notnull(curr_data['LOAN_SEQUENCE_NUMBER'])]
    #curr_data['LOAN_SEQUENCE_NUMBER'] = pd.to_numeric(curr_data['LOAN_SEQUENCE_NUMBER'])
    #curr_data['LOAN_SEQUENCE_NUMBER'] = curr_data[curr_data['LOAN_SEQUENCE_NUMBER'].isnull()== False]['LOAN_SEQUENCE_NUMBER']
    #curr_data['LOAN_SEQUENCE_NUMBER'] = curr_data['LOAN_SEQUENCE_NUMBER'].fillna((curr_data['LOAN_SEQUENCE_NUMBER'].mean()))

    #MONTHLY_REPORTING_PERIOD
    curr_data['MONTHLY_REPORTING_PERIOD'] = pd.to_numeric(curr_data['MONTHLY_REPORTING_PERIOD'])
    curr_data['MONTHLY_REPORTING_PERIOD'] = curr_data['MONTHLY_REPORTING_PERIOD'].fillna((curr_data['MONTHLY_REPORTING_PERIOD'].mode()))

    #CURRENT_ACTUAL_UPB - Mode
    curr_data['CURRENT_ACTUAL_UPB'] = pd.to_numeric(curr_data['CURRENT_ACTUAL_UPB'])
    curr_data['CURRENT_ACTUAL_UPB'] = curr_data['CURRENT_ACTUAL_UPB'].fillna((curr_data['CURRENT_ACTUAL_UPB'].mean()))

    #CURRENT_LOAN_DELINQUENCY_STATUS - Mean
    curr_data[curr_data['CURRENT_LOAN_DELINQUENCY_STATUS'] == 'R'] = 1
    curr_data['CURRENT_LOAN_DELINQUENCY_STATUS'] = pd.to_numeric(curr_data['CURRENT_LOAN_DELINQUENCY_STATUS'])
    curr_data['CURRENT_LOAN_DELINQUENCY_STATUS'] = curr_data['CURRENT_LOAN_DELINQUENCY_STATUS'].fillna((curr_data['CURRENT_LOAN_DELINQUENCY_STATUS'].mean()))

    #LOAN_AGE - Mode
    curr_data['LOAN_AGE'] = pd.to_numeric(curr_data['LOAN_AGE'])
    curr_data['LOAN_AGE'] = curr_data['LOAN_AGE'].fillna((curr_data['LOAN_AGE'].mode()))

    #REMAINING_MONTHS_TO_LEGAL_MATURITY
    curr_data['REMAINING_MONTHS_TO_LEGAL_MATURITY'] = pd.to_numeric(curr_data['REMAINING_MONTHS_TO_LEGAL_MATURITY'])
    curr_data['REMAINING_MONTHS_TO_LEGAL_MATURITY'] = curr_data['REMAINING_MONTHS_TO_LEGAL_MATURITY'].fillna((curr_data['REMAINING_MONTHS_TO_LEGAL_MATURITY'].mean()))

    #REPURCHASE_FLAG
    #curr_data['REPURCHASE_FLAG'] = pd.to_numeric(curr_data['REPURCHASE_FLAG'])
    curr_data['REPURCHASE_FLAG'] = curr_data['REPURCHASE_FLAG'].fillna((curr_data['REPURCHASE_FLAG'].mode()))

    #MODIFICATION_FLAG
    #curr_data['MODIFICATION_FLAG'] = pd.to_numeric(curr_data['MODIFICATION_FLAG'])
    curr_data['MODIFICATION_FLAG'] = curr_data['MODIFICATION_FLAG'].fillna((curr_data['MODIFICATION_FLAG'].mode()))

    #ZERO_BALANCE_CODE
    curr_data['ZERO_BALANCE_CODE'] = pd.to_numeric(curr_data['ZERO_BALANCE_CODE'])
    curr_data['ZERO_BALANCE_CODE'] = curr_data['ZERO_BALANCE_CODE'].fillna((curr_data['ZERO_BALANCE_CODE'].mode()))

    #ZERO_BALANCE_EFFECTIVE_DATE
    curr_data['ZERO_BALANCE_EFFECTIVE_DATE'] = pd.to_numeric(curr_data['ZERO_BALANCE_EFFECTIVE_DATE'])
    curr_data['ZERO_BALANCE_EFFECTIVE_DATE'] = curr_data['ZERO_BALANCE_EFFECTIVE_DATE'].fillna((curr_data['ZERO_BALANCE_EFFECTIVE_DATE'].mode()))

    #CURRENT_INTEREST_RATE
    curr_data['CURRENT_INTEREST_RATE'] = pd.to_numeric(curr_data['CURRENT_INTEREST_RATE'])
    curr_data['CURRENT_INTEREST_RATE'] = curr_data['CURRENT_INTEREST_RATE'].fillna((curr_data['CURRENT_INTEREST_RATE'].mode()))

    #CURRENT_DEFERRED_UPB
    #curr_data['CURRENT_DEFERRED_UPB'] = pd.to_numeric(curr_data['CURRENT_DEFERRED_UPB'])
    curr_data['CURRENT_DEFERRED_UPB'] = curr_data['CURRENT_DEFERRED_UPB'].fillna((curr_data['CURRENT_DEFERRED_UPB'].mode()))

    
    return curr_data


def ConvertToNumeric2(curr_data):
    number = LabelEncoder()
    #print(curr_data['ServicerName'])

    # N=0,Y=1 
    curr_data['REPURCHASE_FLAG'] = number.fit_transform(curr_data['REPURCHASE_FLAG'].astype('str'))

    # N=0,Y=1
    curr_data['MODIFICATION_FLAG'] = number.fit_transform(curr_data['MODIFICATION_FLAG'].astype('str'))
    
    
    curr_data['LOAN_ORIGNATION_QUARTER'] = number.fit_transform(curr_data['LOAN_ORIGNATION_QUARTER'].astype('str'))

    #print(curr_data['ServicerName'])
    return curr_data


def seperateData(curr_data):
    curr_data['MONTHLY_REPORTING_YEAR'] = curr_data['MONTHLY_REPORTING_PERIOD'].apply(lambda x: str(x)[:4])
    curr_data['MONTHLY_REPORTING_YEAR'] = pd.to_numeric(curr_data['MONTHLY_REPORTING_YEAR'])
    curr_data['MONTHLY_REPORTING_MONTH'] = curr_data['MONTHLY_REPORTING_PERIOD'].apply(lambda x: str(x)[4:])
    curr_data['MONTHLY_REPORTING_MONTH'] = pd.to_numeric(curr_data['MONTHLY_REPORTING_MONTH'])
    curr_data['MONTHLY_REPORTING_MONTH'] = curr_data['MONTHLY_REPORTING_MONTH'].fillna((curr_data['MONTHLY_REPORTING_MONTH'].mode()))

    curr_data['LOAN_ORIGNATION_YEAR'] = curr_data['LOAN_SEQUENCE_NUMBER'].apply(lambda x: str(x)[2:4])
    curr_data['LOAN_ORIGNATION_YEAR'] = pd.to_numeric(curr_data['LOAN_ORIGNATION_YEAR'])
    curr_data['LOAN_ORIGNATION_YEAR'] = curr_data['LOAN_ORIGNATION_YEAR'].fillna((curr_data['LOAN_ORIGNATION_YEAR'].mode()))

    curr_data['LOAN_ORIGNATION_QUARTER'] = curr_data['LOAN_SEQUENCE_NUMBER'].apply(lambda x: str(x)[4:6])
    curr_data['LOAN_ORIGNATION_QUARTER'] = curr_data['LOAN_ORIGNATION_QUARTER'].fillna((curr_data['LOAN_ORIGNATION_QUARTER'].mode()))

    #curr_data['LOAN_ORIGNATION_QUARTER'] = pd.to_numeric(curr_data['LOAN_ORIGNATION_QUARTER'])
    
    return curr_data 


def selectColumns(curr_data):
    res = missing_values_table(curr_data)
    col_to_consider = res.index[res['% of Total Values']<60]
    return col_to_consider.values.tolist()

directory = 'all_data'
year,next_year = getYear()

response, session = get_login()
#hist_data,hist_data_time = getData(year,next_year,response,session)
#getData(year,next_year,response,session)
dataFile,dataFile1 = getData(year,next_year,response,session)
data = pd.read_csv(dataFile,delimiter='|', header=None,low_memory=True)
data1 = pd.read_csv(dataFile1,delimiter='|', header=None,low_memory=True)


#data = pd.read_csv('historical_data1_time_Q120051.txt',delimiter='\t', header=None,low_memory=True)
#data =  np.loadtxt(fname = 'all_data\\historical_data1_Q12013.txt', delimiter = '|')
#data

#data1 = data
#data1 = pd.read_csv('historical_data1_time_Q120051.txt',delimiter='\t', header=None,low_memory=True)

curr_data = add_header(data)
curr_data = df_strip(data)
missing_values_table(curr_data)
curr_data = df_strip(curr_data)
curr_data = ConvertToNumeric1(curr_data)
curr_data = seperateData(curr_data)
curr_data = ConvertToNumeric2(curr_data)

#print(curr_data[curr_data['NumberOfUnits'].isnull()== True]['NumberOfUnits'])
col_to_consider=selectColumns(curr_data)
#print(col_to_consider)


next_data = add_header(data1)
next_data = df_strip(data1)
missing_values_table(next_data)
next_data = df_strip(next_data)
next_data = ConvertToNumeric1(next_data)
next_data = seperateData(next_data)
next_data = ConvertToNumeric2(next_data)

#print(curr_data[curr_data['NumberOfUnits'].isnull()== True]['NumberOfUnits'])
col_to_consider=selectColumns(next_data)
#print(col_to_consider)

#print(curr_data[curr_data['CURRENT_LOAN_DELINQUENCY_STATUS'] == 'R'])

curr_data[col_to_consider].dtypes

col_to_consider.remove('LOAN_SEQUENCE_NUMBER')
col_to_consider.remove('CURRENT_LOAN_DELINQUENCY_STATUS')
col_to_consider.remove('MONTHLY_REPORTING_PERIOD')
col_to_consider.remove('MONTHLY_REPORTING_MONTH')
col_to_consider.remove('LOAN_ORIGNATION_YEAR')
col_to_consider.remove('LOAN_ORIGNATION_QUARTER')


curr_data['YN_CURRENT_LOAN_DELINQUENCY_STATUS'] = (curr_data.CURRENT_LOAN_DELINQUENCY_STATUS > 0).astype(int)
#next_data['YN_CURRENT_LOAN_DELINQUENCY_STATUS'] = (next_data.CURRENT_LOAN_DELINQUENCY_STATUS > 0).astype(int)
#print(curr_data['YN_CURRENT_LOAN_DELINQUENCY_STATUS'] )
#curr_data = curr_data.dropna() 
print(curr_data[curr_data['YN_CURRENT_LOAN_DELINQUENCY_STATUS'] == 0])
#print(curr_data[col_to_consider])

X = curr_data[col_to_consider]
y = curr_data['YN_CURRENT_LOAN_DELINQUENCY_STATUS']
y = np.ravel(y)

from sklearn.linear_model import LogisticRegression
model = LogisticRegression()
model = model.fit(X, y)

X_test = next_data[col_to_consider]

#Run the model on the test set
y_pred = model.predict(X_test)

from sklearn.metrics import confusion_matrix
confusion_matrix(y, y_pred)

model.score(X, y)

model.coef_

import statsmodels.api as sm
from statsmodels.formula.api import logit, probit, poisson, ols
from sklearn.metrics import roc_curve, auc
logit = sm.Logit(y, X.astype(float))
model = logit.fit()
print(model.summary())

# Add prediction to dataframe
curr_data['pred'] = model.predict(X.astype(float))

fpr, tpr, thresholds =roc_curve(y, curr_data['pred'])
roc_auc = auc(fpr, tpr)
print(fpr, tpr, thresholds)
print("Area under the ROC curve : %f" % roc_auc)

import matplotlib.pyplot as plt
plt.figure()
plt.plot(fpr, tpr, label='ROC curve')
plt.plot([0, 1], [0, 1], 'k--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('1-Specificity')
plt.ylabel('Sensitivity')
plt.title('ROC curve')
plt.legend(loc="lower right")
plt.show()

net = buildNetwork(8,5, 1)

ds = SupervisedDataSet(8,1)

for index, row in curr_data.iterrows():
    input_data = row[col_to_consider]
    output_data = row['OriginalInterestRate']
    ds.addSample(input_data,output_data)

trainer = BackpropTrainer(net, ds)

trainer.train()

trainer.trainUntilConvergence()

for index, row in next_data.iterrows():
    input_data = row[cols_to_keep]
    output_data = row['OriginalInterestRate']
    #ds.addSample(input_data,output_data)
    print(net.activate(input_data))

from sklearn import svm
#SVM Model
clf = svm.SVC(kernel='linear')
clf.fit(X.astype(int), y.astype(int))

Trianing
y1= curr_data['YN_CURRENT_LOAN_DELINQUENCY_STATUS']

pred = clf.predict(X1)
pred

#Performance on test dataset
pd.crosstab(pred,y1[1],rownames=['pred'], colnames=['y1'])