__author__ = 'marcopereira'
from pandas import DataFrame
import numpy as np
import pandas as pd
from parameters import WORKING_DIR
from scipy.optimize import minimize
import os
import bisect


class MC_Vasicek_Sim(object):
    def __init__(self, datelist,x, simNumber,t_step):
        self.kappa = x[0]
        self.theta = x[1]
        self.sigma = x[2]
        self.r0 = x[3]
        self.simNumber = simNumber
        self.t_step = t_step
    #internal representation of times series - integer multiples of t_step
        self.datelist = datelist
    #creation of a fine grid for Monte Carlo integration
        #Create fine date grid for SDE integration
        minDay = min(datelist)
        maxDay = max(datelist)
        self.datelistlong = pd.date_range(minDay, maxDay).tolist()
        self.datelistlong = [x.date() for x in self.datelistlong]
        self.ntimes = len(self.datelistlong)
        # print(self.ntimes)
        self.libor=[]
        self.smallLibor = []
        self.liborAvg=pd.DataFrame()

    def getLibor(self):
        rd = np.random.standard_normal((self.ntimes,self.simNumber))   # array of numbers for the number of samples
        r = np.zeros(np.shape(rd))
        #print(np.shape(rd))
        #print(np.shape(r))
        nrows = np.shape(rd)[0]
        #print(nrows)
        sigmaDT = self.sigma* np.sqrt(self.t_step)
    #calculate r(t)
        r[1,:] = self.r0+r[1,:]
        for i in np.arange(2,nrows):
            r[i,:] = r[i-1,:]+ self.kappa*(self.theta-r[i-1,:])*self.t_step + sigmaDT*rd[i,:]
    #calculate integral(r(s)ds)
        integralR = r.cumsum(axis=0)*self.t_step
        #print(np.shape(integralR))
    #calculate Libor
        self.libor = np.exp(-integralR)
        #print(np.shape(self.libor))
        self.liborAvg=np.average(self.libor,axis=1)
        #self.libor=np.c_[self.liborAvg,self.libor]
        #print(np.shape(self.libor))
        self.libor = pd.DataFrame(self.libor,index=self.datelistlong)
        #print(np.shape(self.libor))
        #print(self.datelistlong)
        return self.libor

    def getSmallLibor(self, x=[], datelist=[], simNumber=1):
        if(datelist is None):
            datelist=self.datelist
        ind = self.return_indices1_of_a(self.datelistlong, datelist)
        self.smallLibor = self.libor.loc[datelist]


        return self.smallLibor
            #pd.DataFrame(self.smallLibor, index=datelist)



    def setParams(self,x):
        self.kappa = x[0]
        self.theta = x[1]
        self.sigma = x[2]
        self.r0 = x[3]

    def getParams(self):
        ## Estimate the parameters in the vasicek model ##


        return [self.kappa,self.theta,self.sigma,self.r0]


    def getLiborAvg(self):
        if(len(self.libor) == 0):
            self.getLibor()
            return self.libor[0]
        else:
            return self.libor[0]

    def fitParams(self,discountCurves):
        pass

    def error(self,params,discountCurves):
        simulator = MC_Vasicek_Sim(datelist = list(discountCurves.index), x = params, simNumber = 100, t_step = 1.0 / 365)
        simulatedCurve = simulator.getLiborAvg()# sum of squares
        initValues = [0.000377701101971, 0.06807420742631265, 0.020205128906558, 0.002073084987793]
    pass


#####################################################################################
    def saveMeExcel(self):
        """ Saves the value of 'libor' as OpenXML spreadsheet.
        """
        df = DataFrame(self.libor)
        df.to_excel(os.path.join(WORKING_DIR,'MC_Vasicek_Sim.xlsx'), sheet_name='libor', index=False)

#####################################################################################
    def return_indices1_of_a(self, a, b):
        b_set = set(b)
        ind = [i for i, v in enumerate(a) if v in b_set]
        return ind
#####################################################################################
    def return_indices2_of_a(self, a, b):
        index=[]
        for item in a:
            index.append(bisect.bisect(b,item))
        return np.unique(index).tolist()

    def setVasicek(self,x, minDay, maxDay, simNumber, t_step):
        self.t_step=t_step
        self.simNumber=simNumber
        self.minDay = minDay
        self.x = x
