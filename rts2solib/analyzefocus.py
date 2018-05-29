from astropy.io import fits
import os
import numpy as np
import sep
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import sys
import math 
from scipy.interpolate import UnivariateSpline

global verbose
verbose = False
def setverbose(v):
	verbose = v

def printv(msg, verbose=False):
	if verbose:
		print(msg)

class shiftobjs:
	def __init__(self):
		self.avgx = 0.0
		self.avgy = 0.0
		self.objs = []

	def addobjs(self, common_objects, focpos, focalshift):
		sorted_objects = sorted(common_objects, key=lambda x: x['y'], reverse=True)
		#print focpos,focalshift
		for f in common_objects:
			#print focpos, f['x'], f['y']
			fwhm = 2 * math.sqrt(math.log(2) * (f['a']**2 + f['b']**2))
			#print f['y'], focpos, fwhm
			self.objs.append(focobj(f['x'], f['y'], f['a'], f['b'], focpos, fwhm, f['theta']))
			focpos = focpos + focalshift
		self.avgx = np.mean([x.x for x in self.objs])
		self.avgy = np.mean([x.y for x in self.objs])

class focobj:
	def __init__(self, x, y, a, b, focval, fwhm, theta):
		self.x = x
		self.y = y
		self.a = a
		self.b = b
		self.theta = theta
		self.focval = focval
		self.fwhm = fwhm

def resetplt(data_sub):
	fig, ax = plt.subplots()
	m, s = np.mean(data_sub), np.std(data_sub)
	im = ax.imshow(data_sub, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
	return fig, ax, im

def notalreadyadded(shiftobjects, shifts):
	ret = True
	for f in shifts:
		#print f.avgx, f.avgy
		#print shiftobjects.avgx, shiftobjects.avgy
		if abs(f.avgx - shiftobjects.avgx) < 5 and abs(f.avgy - shiftobjects.avgy) < 5:
			#print abs(f.avgx - shiftobjects.avgx), abs(f.avgy - shiftobjects.avgy)
			return False
	return True

class focalfit:

	def __init__(self, _img, _object_err_thresh=2.0, _object_minarea=5):
		self.img = _img

		self.object_err_thresh = _object_err_thresh

		self.object_minarea = _object_minarea


	def run(self):
		hdu = fits.open(self.img)
		hdr = hdu[0].header
		data = np.asarray(hdu[1].data, dtype=np.int32)
		focalval = float(hdr['FOC_POS'])
		focalshift = float(hdr['SHIFT_FO'])
		pixelshift = hdr['SHIFT_PX']
		nshifts = int(hdr['SHIFT_N'])
		bkg = sep.Background(data, bw=64, bh=64, fw=3, fh=3)
		bkg_image = bkg.back()
		bkg_rms = bkg.rms()
		data_sub = data - bkg
		objects = sep.extract(data_sub, self.object_err_thresh, err=bkg.globalrms, minarea=self.object_minarea)
		shifts, fwhm_av = [], []

		for o in objects:
			ox = o['x']
			oy = o['y']
			if abs(ox - 275) > 1:
				shiftobjects = shiftobjs()
				common_objects = [x for x in objects if abs(x['x'] - ox) < 1.5 and abs(x['y']-oy) < 140]
				if len(common_objects) >= nshifts:
					shiftobjects.addobjs(common_objects, focalval, focalshift)
					if notalreadyadded(shiftobjects, shifts):
						shifts.append(shiftobjects)
						focs = [x.focval for x in shiftobjects.objs]
						fwhms = [x.fwhm for x in shiftobjects.objs]
						spl = UnivariateSpline(focs, fwhms)

						a = np.polyfit(focs, fwhms, 2)
						b = np.poly1d(a)
						x_interp = np.arange(focs[0],focs[len(focs)-1], 0.001)
						y_interp = spl(x_interp)

						miny_ind = list(y_interp).index(min(y_interp))
						minfoc = x_interp[miny_ind]

						xmin, xmax = min(x_interp), max(x_interp)
						if minfoc >= (xmin + 0.125*xmin) or minfoc <= (xmin + 0.875*(xmax-xmin)):
							fwhm_av.append(minfoc)

		if len(fwhm_av) != 0:
			return np.mean(fwhm_av)
		else:
			return focalval

def main():
	#define files
	#loop over files
	#	open fits image
	#	locate sources
	#	find sources that are in the same line vertically
	#	group them
	#	loop over them
	#		analyze their FWHM 
	#		plot FWHM vs focal position
	#		plot a curve to it
	#		find minimum
	#		store in array
	#return average minimum?
	
	files = [x for x in os.listdir(os.getcwd()) if '.fits' in x]
	for f in files[:]:
		hdu = fits.open(f)
		header = hdu[0].header
		data0 = hdu[1].data
		data = np.asarray(data0, dtype=np.int32)
		print f
		focalval = float(header['FOC_POS'])
		focalshift = float(header['SHIFT_FO'])
		pixelshift = header['SHIFT_PX']
		nshifts = int(header['SHIFT_N'])


		bkg = sep.Background(data, bw=64, bh=64, fw=3, fh=3)
		bkg_image = bkg.back()
		bkg_rms = bkg.rms()
		data_sub = data - bkg
		objects = sep.extract(data_sub, 2, err=bkg.globalrms, minarea=5)
		print len(objects)
		shifts = []
		fwhm_av = []
		for o in objects:
			ox = o['x']
			oy = o['y']
			if abs(ox - 275) > 1:
				shiftobjects = shiftobjs()
				common_objects = [x for x in objects if abs(x['x'] - ox) < 1.5 and abs(x['y']-oy) < 140]
				if len(common_objects) >= nshifts:
					shiftobjects.addobjs(common_objects, focalval, focalshift)
					if notalreadyadded(shiftobjects, shifts):
						shifts.append(shiftobjects)
						
						fig, ax, im = resetplt(data_sub)			
						for f in common_objects:
							e = Ellipse(xy=(f['x'], f['y']),
								width=6*f['a'],
								height=6*f['b'],
								angle=f['theta']*180./np.pi)
							e.set_facecolor('none')
							e.set_edgecolor('red')
						
							ax.add_artist(e)
						plt.show()
						plt.clf()

						focs = [x.focval for x in shiftobjects.objs]
						fwhms = [x.fwhm for x in shiftobjects.objs]
						minfoc = -999
						#try:

						spl = UnivariateSpline(focs, fwhms)

						a = np.polyfit(focs, fwhms, 2)
						b = np.poly1d(a)
						x_interp = np.arange(focs[0],focs[len(focs)-1], 0.001)
						y_interp = spl(x_interp)

						miny_ind = list(y_interp).index(min(y_interp))
						minfoc = x_interp[miny_ind]

						xmin, xmax = min(x_interp), max(x_interp)
						if minfoc < (xmin + 0.125*xmin) or minfoc > (xmin + 0.875*(xmax-xmin)):
							print "bad fit data", minfoc, xmin, xmax
						else:
							fwhm_av.append(minfoc)
						#plt.plot(x_interp, y_interp, "-r")
						#plt.scatter([minfoc],[y_interp[miny_ind]], c="green")
							#except:
								#print "Unable to find minimum"
						#plt.scatter(focs, fwhms)
			
			#plt.show()

		if len(fwhm_av) != 0:
			print len(shifts)
			print np.mean(fwhm_av), np.std(fwhm_av)
		else:
			print "No good values"
		plt.show()
		plt.clf()
#main()

