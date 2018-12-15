from rts2solib import stellar
from rts2solib.big61filters import filter_set;FILTERS=filter_set()
from astropy.time import Time
import astropy.units as u
from astropy.coordinates import Angle

import datetime
tucson = ('110d', '32d')

def test_stellar():
	st=Time(datetime.datetime.now(), location=tucson).sidereal_time('apparent')
	rastr = "{}:{}:{:2.2f}".format( int(st.hms[0]), int(st.hms[1]), st.hms[2] )
	decstr="32:00:00.0"
	s = stellar("testtarg", rastr, decstr)
	return s
	

def test_two_stellar():
	"""Test two stellar targets hour before and after the meridian"""
	st=Time(datetime.datetime.now(), location=tucson).sidereal_time('apparent')
	ra1= st+Angle(1, u.hour)
	ra2= st-Angle(1, u.hour)
	decstr="32:00:00.0"
	return stellar("testarg2", ra1.to_string(sep=":"), decstr)
	
