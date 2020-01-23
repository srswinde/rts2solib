#!/usr/bin/python

from rts2.bias_DS import Bias, BiasScript
import rts2.scriptcomm
import json
#from rts2solib.rts2_wwwapi import rts2comm
from rts2solib.big61filters import filter_set; Filters=filter_set()
import numpy
from telescope import kuiper;k=kuiper()

f = BiasScript(numbias=1,binning=2)

f.run()
