import pip
def install(package):
   pip.main(['install', package])

import urllib.request
import requests
import sys
#import cgitb
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
from bs4 import BeautifulSoup as bsoup
import matplotlib.pyplot as plt
import json

import sklearn
from sklearn import datasets
from sklearn.preprocessing import LabelEncoder
from sklearn import linear_model
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import *

from sklearn.model_selection import cross_val_score

from pybrain.tools.shortcuts import buildNetwork
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer

import math
import operator

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
    print(os.path.isdir(directory))
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
        #print (os.getcwd())
        hist_data =  a.text[:24]+'txt'
        hist_data_time = a.text[:17] + 'time_' + a.text[17:24] + 'txt'
        
        hist_data1 = directory + "\\\\" + a.text[:24]+'txt'
        hist_data_time1 = directory + "\\\\" + a.text[:17] + 'time_' + a.text[17:24] + 'txt'
        if current_year in zip_file_url:
            count = 0
            #if any(hist_data in s for s in fileList):
            #if hist_data in fileList:
            if any(hist_data in s for s in fileList):
                count+= 1
            if any(hist_data in s for s in fileList):
                count+= 1
            if count != 2:
                print(zip_file_url)
                zfile = session.get(zip_file_url)
                z = zipfile.ZipFile(io.BytesIO(zfile.content))
                z.extractall(directory)
            currData = hist_data1
            
        if next_year in zip_file_url:
            count = 0
            if any(hist_data in s for s in fileList):
                count = count + 1     
            if any(hist_data in s for s in fileList):
                count = count + 1
            if count != 2:
                zfile = session.get(zip_file_url)
                z = zipfile.ZipFile(io.BytesIO(zfile.content))
                z.extractall(directory)
            nexData = hist_data1
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
    header = ['CreditScore','FirstPaymentDate','FirstTimeHomeBuyerFlag','MaturityDate',
    'MetropolitanStatisticalAreaOrMetropolitanDivision','MortgageInsurancePercentage','NumberOfUnits','OccupancyStatus',
    'OriginalCombinedLoan-To-Value(CLTV)','OriginalDebt-To-Income(DTI)Ratio','OriginalUPB','OriginalLoan-To-Value(LTV)',
    'OriginalInterestRate','Channel','PaymentPenaltyMortgage(PPM)Flag','ProductType','PropertyState','PropertyType',
    'PostalCode','LoanSequenceNumber','LoanPurpose','OriginalLoanTerm','NumberOfBorrowers','SellerName','ServicerName',
    'SuperConformingFlag']
    curr_data = pd.DataFrame(data)
    curr_data.columns = header
    return curr_data

def ConvertToNumeric1(curr_data): 
    #CreditScore - Mean
    curr_data['CreditScore'] = pd.to_numeric(curr_data['CreditScore'])
    curr_data['CreditScore'] = curr_data['CreditScore'].fillna((curr_data['CreditScore'].mean()))

    #MetropolitanStatisticalAreaOrMetropolitanDivision
    curr_data['MetropolitanStatisticalAreaOrMetropolitanDivision'] = pd.to_numeric(curr_data['MetropolitanStatisticalAreaOrMetropolitanDivision'])
    curr_data['MetropolitanStatisticalAreaOrMetropolitanDivision'] = curr_data['MetropolitanStatisticalAreaOrMetropolitanDivision'].fillna((curr_data['MetropolitanStatisticalAreaOrMetropolitanDivision'].mean()))

    #FirstTimeHomeBuyerFlag - Mode
    #curr_data['FirstTimeHomeBuyerFlag'] = pd.to_numeric(curr_data['OriginalInterestRate'])
    curr_data['FirstTimeHomeBuyerFlag'] = curr_data['FirstTimeHomeBuyerFlag'].fillna((curr_data['FirstTimeHomeBuyerFlag'].mode()))

    #MortgageInsurancePercentage - Mean
    curr_data['MortgageInsurancePercentage'] = pd.to_numeric(curr_data['MortgageInsurancePercentage'])
    curr_data['MortgageInsurancePercentage'] = curr_data['MortgageInsurancePercentage'].fillna((curr_data['MortgageInsurancePercentage'].mean()))

    #NumberOfUnits - Mode
    curr_data['NumberOfUnits'] = pd.to_numeric(curr_data['NumberOfUnits'])
    curr_data['NumberOfUnits'] = curr_data['NumberOfUnits'].fillna((curr_data['NumberOfUnits'].mode()))

    #OccupancyStatus
    #curr_data['OccupancyStatus'] = pd.to_numeric(curr_data['OccupancyStatus'])
    curr_data['OccupancyStatus'] = curr_data['OccupancyStatus'].fillna((curr_data['OccupancyStatus'].mode()))

    #OriginalCombinedLoan-To-Value(CLTV)
    curr_data['OriginalCombinedLoan-To-Value(CLTV)'] = pd.to_numeric(curr_data['OriginalCombinedLoan-To-Value(CLTV)'])
    curr_data['OriginalCombinedLoan-To-Value(CLTV)'] = curr_data['OriginalCombinedLoan-To-Value(CLTV)'].fillna((curr_data['OriginalCombinedLoan-To-Value(CLTV)'].mean()))

    #OriginalDebt-To-Income(DTI)Ratio
    curr_data['OriginalDebt-To-Income(DTI)Ratio'] = pd.to_numeric(curr_data['OriginalDebt-To-Income(DTI)Ratio'])
    curr_data['OriginalDebt-To-Income(DTI)Ratio'] = curr_data['OriginalDebt-To-Income(DTI)Ratio'].fillna((curr_data['OriginalDebt-To-Income(DTI)Ratio'].mean()))

    #OriginalUPB
    curr_data['OriginalUPB'] = pd.to_numeric(curr_data['OriginalUPB'])
    curr_data['OriginalUPB'] = curr_data['OriginalUPB'].fillna((curr_data['OriginalUPB'].mean()))

    #OriginalLoan-To-Value(LTV)
    curr_data['OriginalLoan-To-Value(LTV)'] = pd.to_numeric(curr_data['OriginalLoan-To-Value(LTV)'])
    curr_data['OriginalLoan-To-Value(LTV)'] = curr_data['OriginalLoan-To-Value(LTV)'].fillna((curr_data['OriginalLoan-To-Value(LTV)'].mean()))

    #OriginalInterestRate
    curr_data['OriginalInterestRate'] = pd.to_numeric(curr_data['OriginalInterestRate'])
    curr_data['OriginalInterestRate'] = curr_data['OriginalInterestRate'].fillna((curr_data['OriginalInterestRate'].mode()))

    #Channel
    #curr_data['Channel'] = pd.to_numeric(curr_data['Channel'])
    curr_data['Channel'] = curr_data['Channel'].fillna((curr_data['Channel'].mode()))

    #PaymentPenaltyMortgage(PPM)Flag
    #curr_data['PaymentPenaltyMortgage(PPM)Flag'] = pd.to_numeric(curr_data['PaymentPenaltyMortgage(PPM)Flag'])
    curr_data['PaymentPenaltyMortgage(PPM)Flag'] = curr_data['PaymentPenaltyMortgage(PPM)Flag'].fillna((curr_data['PaymentPenaltyMortgage(PPM)Flag'].mode()))

    #ProductType
    #curr_data['ProductType'] = pd.to_numeric(curr_data['ProductType'])
    curr_data['ProductType'] = curr_data['ProductType'].fillna((curr_data['ProductType'].mode()))

    #PropertyState
    #curr_data['PropertyState'] = pd.to_numeric(curr_data['PropertyState'])
    curr_data['PropertyState'] = curr_data['PropertyState'].fillna((curr_data['PropertyState'].mode()))

    #PropertyType
    #curr_data['PropertyType'] = pd.to_numeric(curr_data['PropertyType'])
    curr_data['PropertyType'] = curr_data['PropertyType'].fillna((curr_data['PropertyType'].mode()))

    #PostalCode
    #curr_data['PostalCode'] = pd.to_numeric(curr_data['PostalCode'])
    curr_data['PostalCode'] = curr_data['PostalCode'].fillna((curr_data['PostalCode'].mode()))

    #LoanPurpose
    #curr_data['LoanPurpose'] = pd.to_numeric(curr_data['LoanPurpose'])
    curr_data['LoanPurpose'] = curr_data['LoanPurpose'].fillna((curr_data['LoanPurpose'].mode()))

    #OriginalLoanTerm
    curr_data['OriginalLoanTerm'] = pd.to_numeric(curr_data['OriginalLoanTerm'])
    curr_data['OriginalLoanTerm'] = curr_data['OriginalLoanTerm'].fillna((curr_data['OriginalLoanTerm'].mean()))

    #NumberOfBorrowers
    #curr_data['NumberOfBorrowers'] = pd.to_numeric(curr_data['NumberOfBorrowers'])
    curr_data['NumberOfBorrowers'] = curr_data['NumberOfBorrowers'].fillna((curr_data['NumberOfBorrowers'].mode()))

    #SellerName
    #curr_data['SellerName'] = pd.to_numeric(curr_data['SellerName'])
    curr_data['SellerName'] = curr_data['SellerName'].fillna((curr_data['SellerName'].mode()))

    #ServicerName
    #curr_data['ServicerName'] = pd.to_numeric(curr_data['ServicerName'])
    curr_data['ServicerName'] = curr_data['ServicerName'].fillna((curr_data['ServicerName'].mode()))

    cols_to_transform = ['FirstTimeHomeBuyerFlag','OccupancyStatus','Channel','PaymentPenaltyMortgage(PPM)Flag','ProductType'
                         ,'PropertyState','PropertyType','LoanPurpose','SellerName','ServicerName'] 
    #df_with_dummies = curr_data.get_dummies( columns = cols_to_transform )
    cat_dict = curr_data[ cols_to_transform ].to_dict( orient = 'records' )
    
    return curr_data


def ConvertToNumeric2(curr_data):
    number = LabelEncoder()
    #print(curr_data['ServicerName'])

    # N=0,Y=1 
    curr_data['FirstTimeHomeBuyerFlag'] = number.fit_transform(curr_data['FirstTimeHomeBuyerFlag'].astype('str'))

    # I=0,O=1,S=2 
    curr_data['OccupancyStatus'] = number.fit_transform(curr_data['OccupancyStatus'].astype('str'))

    # B=0,C=1,R=2,T=3
    curr_data['Channel'] = number.fit_transform(curr_data['Channel'].astype('str'))

    # N=0,Y=1
    curr_data['PaymentPenaltyMortgage(PPM)Flag'] = number.fit_transform(curr_data['PaymentPenaltyMortgage(PPM)Flag'].astype('str'))

    # FRM=0
    curr_data['ProductType'] = number.fit_transform(curr_data['ProductType'].astype('str'))

    # 0 to 53 Alphabetically
    curr_data['PropertyState'] = number.fit_transform(curr_data['PropertyState'].astype('str'))

    # CO=1,CP=2,LH=3,MH=4,PU=5,SF=6
    curr_data['PropertyType'] = number.fit_transform(curr_data['PropertyType'].astype('str'))

    # C=0,N=1,P=2
    curr_data['LoanPurpose'] = number.fit_transform(curr_data['LoanPurpose'].astype('str'))

    # Alphabetically
    curr_data['SellerName'] = number.fit_transform(curr_data['SellerName'].astype('str'))

    # Alphabetically
    curr_data['ServicerName'] = number.fit_transform(curr_data['ServicerName'].astype('str'))

    #print(curr_data['ServicerName'])
    return curr_data

def selectColumns():    
    cols_to_keep = ['CreditScore',
                    #'FirstPaymentDate',
                    'FirstTimeHomeBuyerFlag',
                    #'MaturityDate',
                    'MetropolitanStatisticalAreaOrMetropolitanDivision',
                    'MortgageInsurancePercentage',
                    #'NumberOfUnits',
                    'OccupancyStatus',
                    'OriginalCombinedLoan-To-Value(CLTV)',
                    'OriginalDebt-To-Income(DTI)Ratio',
                    'OriginalUPB',
                    'OriginalLoan-To-Value(LTV)',
                    'Channel',
                    'PaymentPenaltyMortgage(PPM)Flag',
                    'ProductType',
                    'PropertyState',
                    'PropertyType',
                    #'PostalCode',
                    'LoanPurpose',
                    'OriginalLoanTerm',
                    #'NumberOfBorrowers',
                    'SellerName','ServicerName']
    return cols_to_keep

from sklearn import linear_model
def linear_model1(X,Y,X1,Y1):
    lm=linear_model.LinearRegression()
    lm.fit (X, Y)
    print('Linear Model -> Fit successful')
    print('Linear Model -> Intercept : ', lm.intercept_)
    print('Linear Model -> Score : ',lm.score(X, Y))
    test_pred=lm.predict(X1)
    print('Linear Model -> mean_absolute_error : ',mean_absolute_error(Y1,test_pred))
    print('Linear Model -> mean_squared_error : ',mean_squared_error(Y1,test_pred))
    print('Linear Model -> median_absolute_error : ',median_absolute_error(Y1,test_pred))
    
    %matplotlib inline

    x=curr_data[cols_to_keep]
    y=curr_data['OriginalInterestRate']

    print(x.shape,y.shape)
    #plt.scatter(X,Y)
    plt.plot(x, x*lm.coef_+lm.intercept_, color='red',linewidth=2)

def deci_tree(X,Y):
    clf_1 = DecisionTreeRegressor(max_depth=2)
    clf_2 = DecisionTreeRegressor(max_depth=5)
    print(clf_1.fit(X, Y))
    print(clf_2.fit(X, Y))

def rand_forest(X,Y,X1,Y1):
    max_depth = 30
    regr_rf = RandomForestRegressor(max_depth=max_depth, random_state=2)
    regr_rf.fit(X, Y)
    print('Random Forest -> Fit successful')
    
    # Predict on new data 
    y_rf = regr_rf.predict(X1)
    #print(y_rf)
    score=cross_val_score(regr_rf,X,Y).mean()
    
    print('Random Forest -> Score : ',score)
    print('Random Forest -> mean_absolute_error : ',mean_absolute_error(Y1,y_rf))
    print('Random Forest -> mean_squared_error : ',mean_squared_error(Y1,y_rf))
    print('Random Forest -> median_absolute_error : ',median_absolute_error(Y1,y_rf))

def Neural_nwt(curr_data,next_data):
    net = buildNetwork(18,5, 1)
    ds = SupervisedDataSet(18,1)

    for index, row in curr_data.iterrows():
        input_data = row[cols_to_keep]
        output_data = row['OriginalInterestRate']
        ds.addSample(input_data,output_data)
    
    print('Neural_nwt -> Samples Added')
    print('Neural_nwt -> Training network')
    trainer = BackpropTrainer(net, ds)
    trainer.trainUntilConvergence()
    
    print('Neural_nwt -> Activating inputs')
    for index, row in next_data.iterrows():
        input_data = row[cols_to_keep]
        output_data = row['OriginalInterestRate']
        #ds.addSample(input_data,output_data)
        print(net.activate(input_data))

def loadDataset(training_filename,test_filename, split, trainingSet=[] , testSet=[]):
    with open(training_filename, 'r') as csvfile:
        lines = csv.reader(csvfile)
        dataset = list(lines)
        for x in range(len(dataset)-1):
            for y in range(4):
                dataset[x][y] = float(dataset[x][y])
            trainingSet.append(dataset[x])
    with open(training_filename, 'r') as csvfile:
        lines = csv.reader(csvfile)
        dataset = list(lines)
        for x in range(len(dataset)-1):
            for y in range(4):
                dataset[x][y] = float(dataset[x][y])
            testSet.append(dataset[x])

def euclideanDistance(instance1, instance2, length):
    distance = 0
    for x in range(length):
        distance += pow(float((instance1[x])) - float((instance2[x])), 2)
    return math.sqrt(distance)	

def getNeighbors(trainingSet, testInstance, k):
    distances = []
    length = len(testInstance)-1
    for x in range(len(trainingSet)):
        dist = euclideanDistance(testInstance, trainingSet[x], length)
        distances.append((trainingSet[x], dist))
    distances.sort(key=operator.itemgetter(1))
    neighbors = []
    for x in range(k):
        neighbors.append(distances[x][0])
    return neighbors

def getResponse(neighbors):
    classVotes = {}
    for x in range(len(neighbors)):
        response = neighbors[x][-1]
        if response in classVotes:
            classVotes[response] += 1
        else:
            classVotes[response] = 1
    sortedVotes = sorted(classVotes.items(), key=operator.itemgetter(1), reverse=True)
    return sortedVotes[0][0]

def getAccuracy(testSet, predictions):
    correct = 0
    for x in range(len(testSet)):
        if testSet[x][-1] == predictions[x]:
            correct += 1
    return (correct/float(len(testSet))) * 100.0

def knn_main(curr_data,next_data):
    cols_to_keep_knn =  ['CreditScore',
               #'FirstPaymentDate',
               #'FirstTimeHomeBuyerFlag',
               #'MaturityDate',
               'MetropolitanStatisticalAreaOrMetropolitanDivision',
               'MortgageInsurancePercentage',
               #'NumberOfUnits',
               #'OccupancyStatus',
               'OriginalCombinedLoan-To-Value(CLTV)',
               'OriginalDebt-To-Income(DTI)Ratio',
               'OriginalUPB',
               'OriginalLoan-To-Value(LTV)',
               'OriginalInterestRate',
               #'Channel',
               #'PaymentPenaltyMortgage(PPM)Flag',
               #'ProductType',
               #'PropertyState',
               #'PropertyType',
               #'PostalCode',
               #'LoanSequenceNumber',
               #'LoanPurpose',
               'OriginalLoanTerm',
               #'NumberOfBorrowers',
               #'SellerName',
                #'ServicerName',
                #'SuperConformingFlag',
               #'FirstTimeHomeBuyerFlag',
               'OccupancyStatus',
               'Channel',
               'PaymentPenaltyMortgage(PPM)Flag',
               'ProductType',
               #'PropertyState',
               'PropertyType',
               'LoanPurpose',
               #'SellerName',
               #'ServicerName'
               ]
    curr_data[cols_to_keep_knn].to_csv(r'knn.txt', header=None, index=None, sep=',', columns = cols_to_keep)
    next_data[cols_to_keep_knn].to_csv(r'knn1.txt', header=None, index=None, sep=',', columns = cols_to_keep)
    
    trainingSet=[]
    testSet=[]
    split = 0.995
    loadDataset('knn.txt', 'knn1.txt', split, trainingSet, testSet)
    # generate predictions
    predictions=[]
    k = 3
    for i in range(len(testSet)):
        neighbors = getNeighbors(trainingSet, testSet[i], k)
        result = getResponse(neighbors)
        predictions.append(result)
        print('> predicted=' + repr(result) + ', actual=' + repr(testSet[i][-1]))
    accuracy = getAccuracy(testSet, predictions)
    print('Accuracy: ' + repr(accuracy) + '%')

directory = 'all_data'
year,next_year = getYear()

response, session = get_login()
#hist_data,hist_data_time = getData(year,next_year,response,session)
#getData(year,next_year,response,session)
data,data1 = getData(year,next_year,response,session)

data = pd.read_csv(data,delimiter='|', header=None)
#data =  np.loadtxt(fname = 'all_data\\historical_data1_Q12013.txt', delimiter = '|')

data1 = pd.read_csv(data1,delimiter='|', header=None)

curr_data = add_header(data)
curr_data = df_strip(data)
missing_values_table(curr_data)
curr_data = df_strip(curr_data)
curr_data = ConvertToNumeric1(curr_data)
curr_data = ConvertToNumeric2(curr_data)
#print(curr_data[curr_data['NumberOfUnits'].isnull()== True]['NumberOfUnits'])
cols_to_keep=selectColumns()

next_data = add_header(data1)
next_data = df_strip(data1)
missing_values_table(next_data)
next_data = df_strip(curr_data)
next_data = ConvertToNumeric1(next_data)
next_data = ConvertToNumeric2(next_data)
#print(next_data[next_data['NumberOfUnits'].isnull()== True]['NumberOfUnits'])
cols_to_keep=selectColumns()

#print(curr_data.shape)
X = curr_data[cols_to_keep]
Y = curr_data['OriginalInterestRate']
#X.reshape((351739,1))
Y = np.ravel(Y)

X1 = next_data[cols_to_keep]
Y1 = next_data['OriginalInterestRate']

linear_model1(X,Y,X1,Y1)

deci_tree(X,Y)

rand_forest(X,Y,X1,Y1)

Neural_nwt(curr_data,next_data)

knn_main(curr_data,next_data)

curr_data[cols_to_keep_knn].to_csv(r'knn.txt', header=None, index=None, sep=',', columns = cols_to_keep)
next_data[cols_to_keep_knn].to_csv(r'knn1.txt', header=None, index=None, sep=',', columns = cols_to_keep)

trainingSet=[]
testSet=[]
split = 0.995
loadDataset('knn.txt', 'knn1.txt', split, trainingSet, testSet)
# generate predictions
predictions=[]
k = 3
for i in range(len(testSet)):
    neighbors = getNeighbors(trainingSet, testSet[i], k)
    result = getResponse(neighbors)
    predictions.append(result)
    print('> predicted=' + repr(result) + ', actual=' + repr(testSet[i][-1]))
accuracy = getAccuracy(testSet, predictions)
print('Accuracy: ' + repr(accuracy) + '%')
