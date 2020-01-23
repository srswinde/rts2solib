#!/usr/bin/python

import sys
import string
import time
import scriptcomm

from datetime import datetime


class Bias:

    """Flat class. It holds system configuration for skyflats.
    filters are filter (single string) or filters (FILTA, FILTB.. array)
        for flats to expose
    """

    def __init__(
        self, binning=None 
    ):
        
        self.binning = binning
        
        
        

class BiasScript (scriptcomm.RtsComm):

    """Class for taking a bunch of biases."""


    def __init__(
            self, numbias=2, binning=3
    ):
        scriptcomm.Rts2Comm.__init__(self)

        self.numbias = numbias
        self.binning = binning

    def takeBias(self):
        self.setValue('SHUTTER', 'DARK')
        self.setValue('exposure', 0)
        i = 0
        while i < self.numbias:
            i += 1
            bias = self.exposure()
            self.toDark(bias)

        

#This is Dave Sand's cheap-o script to


#from rts2.flats import FlatScript, Flat
#import rts2.scriptcomm
#import json
#from rts2solib.rts2_wwwapi import rts2comm
#from rts2solib.big61filters import filter_set; Filters=filter_set()
#import numpy
#from telescope import kuiper;k=kuiper()




#f=FlatScript(maxBias=3,maxDarks=0,expTimes=0)


#f.run()
