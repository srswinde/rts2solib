import os
import subprocess
import numpy
import requests
import re
from lxml import html
import json
import rts2
import rts2.target
from rts2solib import so_target, so_exposure

#PAM moved the slotis file declaration up to this location and 
# changed the file to a current file. 
#lotisdata = "lotis.txt"
lotisdata = "slotis.txt"
readtxt = False
readweb = True


#uvot - 1a VBU 
#Stand - standard stars
#AzTec - VBR 60 60 60 x3

# BJW - added lunarDistance and airmass constraints to rts2-target,
# changed default offset back to 1 arcmin

nami = 11
rai = 4
deci = 5
typi = 14
tid_index = 0 

filt_dict = {0:"180", 1:"120", 2:"90", 3:"60", 4:"50", 5:"45"}
type_dict = {"UVOT":0, "AzTEC":1, "SPOL":1, "ZTF":1}





class ObservationInfo:
	def __init__(self, filter, exptime, amount):
		self.filter = filter
		self.exptime = exptime
		self.amount = amount

class lotisimport:
	def __init__(self, sr):
		os = findoffset(sr)
		self.name = sr[nami-os]
		self.ra = formatcoord(sr[rai-os])
		self.dec = formatcoord(sr[deci-os])
		self.type = type_dict[sr[typi-os]]
		print "\nINIT: {}, {}, {}, {}".format(self.name, self.ra, self.dec, self.type)

def findoffset(sr):
	for key in type_dict.keys():
		if key in sr:
			typeindex = sr.index(key)
			return typi-typeindex
	return 0 

def formatcoord(coord):
	sine = ""
	if "-" in coord:
		coord = coord.split("-")[1]
		return "\" -{}:{}:{}\"".format(coord[0:2],coord[2:4],coord[4:])
	return "{}:{}:{}".format(coord[0:2],coord[2:4],coord[4:])

def findtargetid_targetlist(lotis_obj):
	cmd = "rts2-targetlist | grep -i {} > tmp.txt".format(lotis_obj.name)
	print cmd
	subprocess.call(cmd, shell=True)
	fi = open("tmp.txt")
	for row in fi:
		splitrow = row.split()
		#for ii,i in enumerate(splitrow):
		#	print ii, i
		if any(x for x in splitrow if str.lower(lotis_obj.name) in str.lower(x)):
			print "found index"
			targetid = splitrow[tid_index]
			return targetid
	fi.close()
	cmd = "rm tmp.txt"
	subprocess.call(cmd, shell=True)
	return createobj(lotis_obj)

def setscript(obs_type, targetid):
	#script = "BIG61.OFFS=(2m,0) "
	script = "BIG61.OFFS=(1m,0) "
	if obs_type == 0: #uvot
		for filt in [4,3,2,1,0]:
			tmp = "filter={} E {} ".format(str(filt), filt_dict[filt])
			script += (tmp * 3) 
	if obs_type == 1: #aztec
		for filt in [4,3,2,1,0]:
                        tmp = "filter={} E {} ".format(str(filt), filt_dict[filt])
                        script += (tmp * 3)
	#cmd = "rts2-target -c C0 -s \"{}\" {}".format(script, targetid)
	# BJW - constrain obs to 15 deg moon distance and airmass<2.2
	cmd = "rts2-target -c C0 --lunarDistance 15: --airmass :2.2 -s \"{}\" {}".format(script, targetid)
	# set no arguments to clear constraints
	#cmd = "rts2-target -c C0 --lunarDistance : --airmass : -s \"{}\" {}".format(script, targetid)
	print cmd
	subprocess.call(cmd, shell=True)

def setwebscript(obj, targetid):
	script = "BIG61.OFFS=(1m,0) "
	filterdict = {"U":0, "B":1, "V":2, "R":3, "I":4, "SCHOTT":5}
	for obs in obj.observation_info:
		tmp = "filter={} E {} ".format(filterdict[str.upper(obs.filter)], str(obs.exptime))
		script += (tmp * int(obs.amount))
	cmd = "rts2-target -c C0 --lunarDistance 15: --airmass :2.2 -s \"{}\" {}".format(script, targetid)
	print cmd
	subprocess.call(cmd, shell=True)


def createobj(lotis_obj):
	cmd = "python /home/scott/git-clones/rts2/scripts/newtarget.py --create {} {} {}".format(lotis_obj.ra, lotis_obj.dec, lotis_obj.name)
	print cmd
	subprocess.call(cmd, shell=True)
	return findtargetid_targetlist(lotis_obj)


def set_queue(targetids):
	if len(targetids) > 0:
		targetstring = ""
		for iid in targetids:
			targetstring += " {}".format(iid)
		cmd = "rts2-queue --queue plan --clear{}".format(targetstring)
		print cmd
		subprocess.call(cmd, shell=True)

def main(readweb,readtxt,lotisdata):
	targetids = []
	if readtxt:	
		fi = open(lotisdata, "r")
		names = []
		for row in fi:
			splitrow = row.split()
			if len(splitrow) > 14:
				#try:
				obj = lotisimport(splitrow)
				if obj.type in type_dict.values() and obj.name not in names:
					targetid = findtargetid_targetlist(obj)
					if targetid != 0: #remove once I figure out how to get newtarget working
						setscript(obj.type, targetid)
						targetids.append(targetid)
						names.append(obj.name)
			#except:
			#	print "bust"
			#	pass

	if readweb:
		page = requests.get("http://slotis.kpno.noao.edu/LOTIS/skypatrol.html")
		tree = html.fromstring(page.content)
		targetsinfo = tree.xpath('//h2/text()')[3:]
		targetsinfo = [re.sub('\n', '', x) for x in targetsinfo if '%' in x]
		lotisdata = []
		for line in targetsinfo:
			splitline = line.split()
			
			if len(splitline) > 12:
				name = splitline[9]
				ra = formatcoord(splitline[2])
				dec = formatcoord(splitline[3])
				exptime = splitline[5]
				filters = splitline[7]
				amounts = splitline[6]
				objtype = splitline[12]
				observationinfos = []
				for f in filters:
					observationinfos.append(so_exposure(f, exptime, amounts))
				#qer = QueueObject(name, ra, dec, objtype, observationinfos)
				qer = so_target(name, ra, dec, objtype, observationinfos)
				print qer
				qer.save()
				lotisdata.append( qer )
		
		for l in lotisdata:
			# targetid = findtargetid_targetlist(l)
			#setwebscript(l, targetid)
			targetids.append(l.id)
			
	
	# the following lines will now be done in the QueueObject
	setq_input = raw_input("Set Queue with LotisData? [y/n]: ")
	if setq_input in ["Y","y","yes"]:
		
		set_queue(targetids)

	print "fin"
	return lotisdata

objects = main(readweb,readtxt,lotisdata)

	#call rts2-targetlist | grep -a name > file
	#read file 
	#test if an observation is in there
	#if yes: get targetid
	#	 set script automoatically to UBV:120, 60 60 x3

	#if not: call create script
	#then find targetid
	#then set script automatically to VBU:60, 60, 120 x3

	#live your life: love your family
	

