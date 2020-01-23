#!/usr/bin/python3

from rts2solib import scriptcomm
import json
#from rts2solib.rts2_wwwapi import rts2comm
from rts2solib.big61filters import filter_set; Filters=filter_set()
from rts2solib import to_dataserver
import numpy
from telescope import kuiper;k=kuiper()
    

#class BiasScript (scriptcomm.Rts2Comm):
#
#    """Class for taking a bunch of biases."""
#
#
#    def __init__(
#            self, numbias=2, binning=3 ):
#        scriptcomm.Rts2Comm.__init__(self)
#
#        self.numbias = numbias
#        self.binning = binning
#
#    def takeBias(self):
#        self.setValue('SHUTTER', 'DARK')
#        self.setValue('exposure', 0)
#        filename = self.exposure(None, "yo.fits")
#        
#        to_dataserver(filename, "yo.fits")
#        i = 0
##        while i < self.numbias:
##            i += 1
##            bias = self.exposure()
##            self.toDark(bias)
#
#
#    def run(self):
#        self.takeBias()
 
script = scriptcomm.Rts2Comm()
script.setValue('SHUTTER', 'LIGHT')
script.setValue('exposure', 0)
script.setValue('binning',3)

filename = script.exposure(None, "thisisatest.fits")

to_dataserver(filename, "daveisaprogrammer.fits")

