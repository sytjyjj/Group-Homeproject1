'''
__author__ = 'marcopereira'
import numpy as np
import pandas as pd
import quandl
import pickle, os
from Scheduler.Scheduler import Scheduler
from parameters import WORKING_DIR


class CorporateRates(object):
    def __init__(self):
        self.OIS = []
        self.filename = WORKING_DIR + '/CorpData.dat'
        self.corporates = []
        self.ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC']
        self.corpSpreads = {}
        self.corporates = pd.DataFrame()
        self.tenors = []
        self.unPickleMe(file=self.filename)
        self.myScheduler=Scheduler()

    def getCorporates(self, trim_start, trim_end):
        curr_trim_end=trim_start
        if(self.corporates.size!=0):
            self.trim_start = self.corporates['OIS'].index.min().date()
            curr_trim_end = self.corporates['OIS'].index.max().date()
        if trim_end<=curr_trim_end:
            self.trim_end = curr_trim_end
            return self.corporates
        self.trim_start = trim_start
        self.trim_end = trim_end
        self.OIS = OIS(trim_start=trim_start, trim_end=trim_end)
        self.datesAll = self.OIS.datesAll
        self.datesAll.columns= [x.upper() for x in self.datesAll.columns]
        self.OISData = self.OIS.getOIS()
        for i in np.arange(len(self.OISData.columns)):
            freq = self.OISData.columns[i]
            self.tenors.append(self.myScheduler.extractDelay(freq=freq))
        for rating in self.ratings:
            index = 'ML/' + rating + 'TRI'
            try:
                corpSpreads = 1e-4 * (
                    quandl.get(index, authtoken="Lqsxas8ieaKqpztgYHxk", trim_start=trim_start, trim_end=trim_end))
                corpSpreads.reset_index(level=0, inplace=True)
                corpSpreads = pd.merge(left=self.datesAll, right=corpSpreads, how='left')
                corpSpreads = corpSpreads.fillna(method='ffill').fillna(method='bfill')
                self.corpSpreads[rating] = corpSpreads.T.fillna(method='ffill').fillna(method='bfill').T
            except:
                print(index, " not found")
        self.corpSpreads = pd.Panel.from_dict(self.corpSpreads)
        self.corporates = {}
        self.OISData.drop('DATE', axis=1, inplace=True)
        ntenors = np.shape(self.OISData)[1]
        for rating in self.ratings:
            try:
                tiledCorps = np.tile(self.corpSpreads[rating]['VALUE'], ntenors).reshape(np.shape(self.OISData))
                self.corporates[rating] = pd.DataFrame(data=(tiledCorps + self.OISData.values),
                                                       index=self.OISData.index, columns=self.OISData.columns)
            except:
                print("Error in addition of Corp Spreads")
        self.corporates['OIS'] = self.OISData
        self.corporates = pd.Panel(self.corporates)
        return self.corporates

    def getOISData(self, datelist=[]):
        if (len(datelist) != 0):
            return self.corporates["OIS"].loc[datelist]
        else:
            return self.self.corporates["OIS"]


    def getCorporateData(self, rating, datelist=[]):
        if (len(datelist) != 0):
            return self.corporates[rating].loc[datelist]
        else:
            return self.corporates[rating]

    def pickleMe(self):
        data = [self.corporates, self.corpSpreads]
        with open(self.filename, "wb") as f:
            pickle.dump(len(data), f)
            for value in data:
                pickle.dump(value, f)

    def unPickleMe(self, file):
        data = []
        if (os.path.exists(file)):
            with open(file, "rb") as f:
                for _ in range(pickle.load(f)):
                    data.append(pickle.load(f))
            self.corporates = data[0]
            self.corpSpreads = data[1]

    def saveMeExcel(self, whichdata, fileName):
        try:
            df = pd.DataFrame(whichdata)
        except:
            df = whichdata
        df.to_excel(fileName)

# Class OIS
class OIS(object):
    def __init__(self, trim_start="2005-01-10", trim_end="2010-01-10"):
        self.OIS = 0.01 * quandl.get("USTREASURY/YIELD", authtoken="Lqsxas8ieaKqpztgYHxk", trim_start=trim_start,
                                     trim_end=trim_end)
        self.OIS.reset_index(level=0, inplace=True)
        self.datesAll = pd.DataFrame(pd.date_range(trim_start, trim_end), columns=['DATE'])
        self.OIS.columns = [x.upper() for x in self.OIS.columns]
        self.OIS = pd.merge(left=self.datesAll, right=self.OIS, how='left')
        self.OIS = self.OIS.fillna(method='ffill').fillna(method='bfill')
        self.OIS = self.OIS.T.fillna(method='ffill').fillna(method='bfill').T
        self.OIS.index = self.datesAll.DATE

    def getOIS(self, datelist=[]):
        if (len(datelist) != 0):
            return self.OIS.iloc[datelist]
        else:
            return self.OIS
'''
from pandas.stats.tests.common import COLS
__author__ = 'marcopereira'
#edited by ryanrozewski
import numpy as np
import pandas as pd
import quandl
import pickle, os
from Scheduler.Scheduler import Scheduler
from parameters import WORKING_DIR
from MonteCarloSimulators.Vasicek.vasicekMCSim import MC_Vasicek_Sim
from fredapi import Fred

QUANDL_API_KEY = 'WgTCCAFvmDkTLv8Wqju4'
FRED_API_KEY = "d76b78ce98ac39e3100ed53b2ca05bf4"

class CorporateRates(object):
    def __init__(self):
        self.OIS = []
        self.filename = WORKING_DIR + '/CorpData.dat'
        self.corporates = []
        self.ratings = {'AAA':"BAMLC0A1CAAA",
                       'AA':"BAMLC0A2CAA",
                       'A':"BAMLC0A3CA",
                       'BBB':"BAMLC0A4CBBB",
                       'BB':"BAMLH0A1HYBB",
                        'B':"BAMLH0A2HYB",
                        'CCC':"BAMLH0A3HYC"}
        self.corpSpreads = {}
        self.corporates = pd.DataFrame()
        self.Qcorporates = pd.DataFrame() # survival function for corporates
        self.tenors = []
        self.unPickleMe(file=self.filename)
        self.myScheduler=Scheduler()
        #self.myVasicek = MC_Vasicek_Sim()
        self.R = 0.4

    def getCorporatesFred(self, trim_start, trim_end):
        self.corpSpreads={}
        fred = Fred(api_key=FRED_API_KEY)
        curr_trim_end=trim_start
        if(self.corporates.size!=0):
            self.trim_start = self.corporates['OIS'].index.min().date()
            curr_trim_end = self.corporates['OIS'].index.max().date()
        if trim_end<=curr_trim_end:
            self.trim_end = curr_trim_end
            return self.corporates
        self.trim_start = trim_start
        self.trim_end = trim_end
        self.OIS = OIS(trim_start=trim_start, trim_end=trim_end)
        self.datesAll = self.OIS.datesAll
        self.datesAll.columns= [x.upper() for x in self.datesAll.columns]
        self.datesAll.index = self.datesAll.DATE
        self.OISData = self.OIS.getOIS()
        for i in np.arange(len(self.OISData.columns)):
            freq = self.OISData.columns[i]
            self.tenors.append(self.myScheduler.extractDelay(freq=freq))
        for rating in self.ratings.keys():
            index = self.ratings[rating]
            try:
                corpSpreads = 1e-2*(fred.get_series(index,observation_start=trim_start, observation_end=trim_end).to_frame())
                corpSpreads.index = [x.date() for x in corpSpreads.index[:]]
                corpSpreads = pd.merge(left=self.datesAll, right=corpSpreads, left_index=True, right_index=True, how="left")
                corpSpreads = corpSpreads.fillna(method='ffill').fillna(method='bfill')
                corpSpreads = corpSpreads.drop("DATE", axis=1)
                self.corpSpreads[rating] = corpSpreads.T.fillna(method='ffill').fillna(method='bfill').T
            except Exception as e:
                print(e)
                print(index, " not found")
        self.corpSpreads = pd.Panel.from_dict(self.corpSpreads)
        self.corporates = {}
        self.OISData.drop('DATE', axis=1, inplace=True)
        ntenors = np.shape(self.OISData)[1]
        for rating in self.ratings:
            try:
                tiledCorps = np.tile(self.corpSpreads[rating][0], ntenors).reshape(np.shape(self.OISData))
                self.corporates[rating] = pd.DataFrame(data=(tiledCorps + self.OISData.values),
                                                       index=self.OISData.index, columns=self.OISData.columns)
            except:
                print("Error in addition of Corp Spreads")
        self.corporates['OIS'] = self.OISData
        self.corporates = pd.Panel(self.corporates)
        return self.corporates


    def getCorporateData(self, rating, datelist=None):
    # This method gets a curve for a given date or date list for a given rating (normally this will be just a date).  
    # It returns a dict of curves read directly from the corporate rates created by getCorporatesFred.
    # Derive delays from self.corporates[rating].columns
        if datelist is None:
            return
        outCurve = {}
        #need an iteratble object
        cols=list(self.corporates[rating].columns)
        myDelays=[]
        #just putting an iterable object together
        for i in range(0,len(cols)):
            myDelays.append(self.myScheduler.extractDelay(freq=cols[i]))
        myCurve=self.corporates[rating]
        #grabbing only the info with the rating I want and making a datelist to calulate time differences
        for day in datelist:
            dates=[(myDelays[x]+day) for x in range(0,len(myDelays))]
        #my array of interest rates
        r=np.zeros((len(datelist),len(dates)))
        nrows=len(dates)
        #multiplying the rate by the delta t in days and saving it to a spot in the array
        for j in range(0,len(datelist)):
            day_tenors=myCurve.loc[datelist[j]]
            for i in range(0,len(day_tenors)):
                 r[j,i]=r[j,i]+day_tenors[i-1]*(dates[i]-datelist[j]).days/365
        # Create curves
        # ..............
        # ..............
        # add curve to outcurve dict
        #integrating and taking e^-
        intR=r.cumsum(axis=0)
        outCurve=np.exp(-intR)
        out=pd.DataFrame(outCurve)
        out.columns=cols
        return out

    def getSpreads(self, rating, datelist=None):
        if datelist is None:
            return
        outCurve = {}
        #need an iteratble object
        #just putting an iterable object together
        myCurve=self.corpSpreads[rating]
        #grabbing only the info with the rating I want and making a datelist to calulate time differences
        #my array of interest rates
        r=np.zeros(len(datelist))
        #multiplying the rate by the delta t in days and saving it to a spot in the array
        for j in range(1,len(datelist)):
            r[j]=r[j-1]+myCurve['VALUE'].loc[j-1]*(datelist[j]-datelist[j-1]).days/365
        # Create curves
        # ..............
        # ..............
        # add curve to outcurve dict
        #integrating and taking e^-
        intR=r.cumsum(axis=0)
        outCurve=np.exp(-intR)
        out=pd.DataFrame(outCurve,index=datelist)
        return out

    def getCorporateQData(self, rating, datelist=None, R=0.4):
        self.R = R
        if datelist is None:
            return
        # Create Q curves using q-tilde equation
        outCurve=((1-(1/1-R)*(1-self.getCorporateData(rating=rating, datelist=datelist)/self.getCorporateData(rating='OIS',datelist=datelist))).values).tolist()
        out=pd.DataFrame(outCurve,index=datelist)
        out.columns=self.corporates[rating].columns
        return out


    def pickleMe(self):
        data = [self.corporates, self.corpSpreads]
        with open(self.filename, "wb") as f:
            pickle.dump(len(data), f)
            for value in data:
                pickle.dump(value, f)

    def unPickleMe(self, file):
        data = []
        if (os.path.exists(file)):
            with open(file, "rb") as f:
                for _ in range(pickle.load(f)):
                    data.append(pickle.load(f))
            self.corporates = data[0]
            self.corpSpreads = data[1]

    def saveMeExcel(self, whichdata, fileName):
        try:
            df = pd.DataFrame(whichdata)
        except:
            df = whichdata
        df.to_excel(fileName)



# Class OIS
class OIS(object):
    def __init__(self, trim_start="2005-01-10", trim_end="2010-01-10"):
        self.OIS = 0.01 * quandl.get("USTREASURY/YIELD", authtoken=QUANDL_API_KEY, trim_start=trim_start,
                                     trim_end=trim_end)
        self.OIS.reset_index(level=0, inplace=True)
        self.datesAll = pd.DataFrame(pd.date_range(trim_start, trim_end), columns=['DATE'])
        self.OIS.columns = [x.upper() for x in self.OIS.columns]
        self.OIS = pd.merge(left=self.datesAll, right=self.OIS, how='left')
        self.OIS = self.OIS.fillna(method='ffill').fillna(method='bfill')
        self.OIS = self.OIS.T.fillna(method='ffill').fillna(method='bfill').T
        self.OIS.index = self.datesAll.DATE

    def getOIS(self, datelist=[]):
        if (len(datelist) != 0):
            return self.OIS.iloc[datelist]
        else:
            return self.OIS
            
