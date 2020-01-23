#!/usr/bin/python

# Example configuation of flats.
# (C) 2010 Petr Kubanek
#
# Please see flats.py file for details about needed files.
#
# You most probably would like to modify this file to suit your needs.
# Please see comments in flats.py for details of the parameters.

from rts2solib import flats
from flats import FlatScript, Flat
import rts2.scriptcomm
import json
#from rts2solib.rts2_wwwapi import rts2comm
from rts2solib.big61filters import filter_set; Filters=filter_set()
import numpy
from telescope import kuiper;k=kuiper()




# You would at least like to specify filter order, if not binning and
# other thingsa

# binning[0]==3x3 and binning[1]=1x1
expt = numpy.arange(1, 5, 0.2)
expt = numpy.append(expt, numpy.arange(5, 10, 0.5))
expt = numpy.append(expt, numpy.arange(10, 41))
f = FlatScript(
    eveningFlats=[
 #       Flat((Filters['U'],), binning=0, window='100 100 500 500'),
        Flat((Filters['V'],), binning=0, window='100 100 500 500'),
        Flat((Filters['B'],), binning=0, window='100 100 500 500'),
        Flat((Filters['R'],), binning=0, window='100 100 500 500'),
        Flat((Filters['I'],), binning=0, window='100 100 500 500'),
    ],
    maxBias=1, maxDarks=0, expTimes=expt
)

# Change deafult number of images
f.flatLevels(optimalFlat=20000, defaultNumberFlats=5, biasLevel=1000, allowedOptimalDeviation=0.3)

# Run it..
# Configure domeDevice,tmpDirectory and mountDevice if your device names differ
#try:
f.run()
	#raise Exception("test error")
#except Exception as err:
#	f.log("E", "there was an erro in creating the master flats {}".format(err) )



