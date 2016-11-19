__author__ = 'marcopereira'
import numpy as np
from pandas import DataFrame
from Scheduler.Scheduler import Scheduler
from parameters import xR,t_step,simNumber,trim_end,trim_start
from MonteCarloSimulators.Vasicek.vasicekMCSim import MC_Vasicek_Sim

class Bond(object):
    def __init__(self, libor, start, maturity, freq, referencedate, coupon, t_series):
        self.libor=libor #remove libor
        self.coupon=coupon
        self.delay=Scheduler.extractDelay(freq=freq)
        self.datelist = []
        self.t_series = t_series
        self.ntimes=len(self.t_series)
        self.pvAvg=0.0
        self.ntimes = np.shape(self.libor)[0]
        self.ntrajectories = np.shape(self.libor)[1]
        self.cashFlows = DataFrame()
        return

getschedulecomplete - list of dates for cf, observationdate
setlibor
PV
getliboravg
getYield
fitmodeltocurve
fcurve

    def PV(self):
        deltaT= np.zeros(self.ntrajectories)
        ones = np.ones(shape=[self.ntrajectories])
        for i in range(1,self.ntimes):
            deltaTrow = ((self.t_series[i]-self.t_series[i-1]).days/365)*ones
            deltaT = np.vstack ((deltaT,deltaTrow) )
        self.cashFlows= self.coupon*deltaT
        principal = ones
        self.cashFlows[self.ntimes-1,:] +=  principal
        pv = self.cashFlows*self.libor
        self.pvAvg = np.average(pv,axis=1)
        return self.pvAvg

    def getYield(self):
        pass

if(__name__=="__main__"):
    coupon = 0.03
    myScheduler = Scheduler()
    datelist = myScheduler.getSchedule(start=trim_start,end=trim_end,freq="3M",referencedate=trim_start)
    myMC = MC_Vasicek_Sim(x=xR,datelist=datelist,simNumber = simNumber, t_step = t_step)
    libor = myMC.getSmallLibor(datelist=datelist)
    mybond = Bond(libor=libor,start=trim_start,maurity=trim_end, coupon=coupon, freq="3M",referencedate=trim_start)
    myPV = mybond.PV()
    print(myPV)
    a=1