from astropy.io import fits
import os
import numpy as np
import sep
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import sys
import math 

def printv(msg, verbose=False):
	if verbose:
		print(msg)

class shiftobjs:
	def __init__(self):
		self.avgx = 0.0
		self.avgy = 0.0
		self.objs = []

	def addobjs(self, common_objects, focpos, focalshift, data_sub):
		common_objects = sorted(common_objects, key=lambda x: x['y'], reverse=False)
		for f in common_objects:
			#flux_radius = sep.flux_radius(data_sub, f['x'], f['y'] ,100, 0.8)
			fwhm = 2 * math.sqrt(math.log(2) * (f['a']**2 + f['b']**2))
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

def plotgroup(data_sub, common_objects):
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

def plotfocalfit(x_interp, y_interp, minfoc, miny_ind, focs, fwhms):
	plt.plot(x_interp, y_interp, "-r")
	plt.scatter([minfoc],[y_interp[miny_ind]], c="green")
		#except:
			#print "Unable to find minimum"
	plt.scatter(focs, fwhms)
	plt.show()

def notalreadyadded(shiftobjects, shifts):
	for f in shifts:
		if abs(f.avgx - shiftobjects.avgx) < 5 and abs(f.avgy - shiftobjects.avgy) < 5:
			return False
	return True

def remove_bad_points(focs, fwhms):
	npoints = len(focs)
	nremoved = npoints
	while nremoved > 0:
		print nremoved
		a = np.polyfit(focs[:], fwhms[:], 2)
		b = np.poly1d(a)
		x_interp = np.arange(focs[0],focs[len(focs)-1], 0.001)
		y_interp = b(x_interp)

		miny_ind = list(y_interp).index(min(y_interp))
		minfoc = x_interp[miny_ind]


		plt.plot(x_interp, y_interp, "-r")
		plt.scatter([minfoc],[y_interp[miny_ind]], c="green")
			#except:
				#print "Unable to find minimum"
		plt.scatter(focs, fwhms)
		plt.show()

		residuals = []
		for fw in fwhms:
			yval = min([abs(fw - y) for y in list(y_interp)])
			residuals.append(abs(fw-yval))
		res_mean, res_std = np.mean(residuals), np.std(residuals)
		print res_mean, res_std
		popps = [kk for kk,res in enumerate(residuals) if abs(res-res_mean) > 1.7*res_std]
		for aa,p in enumerate(popps):
			print "removing point", p
			focs.pop(p-aa)
			fwhms.pop(p-aa)
		nremoved = len(popps)
	return focs, fwhms

def test_positions(group, nshifty):
	#this will make sure that the group is in the correct offset.
	#making sure that it doesn't grab any thing that might be in the same column
	group = sorted(group, key=lambda x: x['y'], reverse=False)
	offsets = [abs(group[ii-1]['y'] - group[ii]['y']) for ii in range(1, len(group))]
	avgoffset = np.mean(offsets[0:len(offsets)-1])
	lastoffset = np.mean(offsets[len(offsets)-1:len(offsets)])/2.0
	return (abs(nshifty-avgoffset) < 5 and abs(nshifty-lastoffset) < 5)
		

class focalfit:

	def __init__(self, img, 
					   object_err_thresh=8, 
					   object_minarea=5,
					   ellipticity_thresh=0.95,
					   deblend_cont=1.0,
					   plotimages = False,
					   thinking = False,
					   verbose = False):

		self.img = img

		self.object_err_thresh = object_err_thresh

		self.object_minarea = object_minarea

		self.ellipticity_thresh = ellipticity_thresh

		self.deblend_cont = deblend_cont

		self.thinking = thinking

		self.plotimages = plotimages

		self.verbose = verbose

		self.flags = []


	def run(self):
		hdu = fits.open(self.img)
		hdr = hdu[0].header
		data = np.asarray(hdu[1].data, dtype=np.int32)
		focalval = float(hdr['FOC_POS'])
		focalshift = float(hdr['SHIFT_FO'])
		pixelshift = int(hdr['SHIFT_PX'])
		nshifts = int(hdr['SHIFT_N'])
		binx, biny = int(hdr['CCDBIN1']), int(hdr['CCDBIN2'])

		nshift_y = (pixelshift/float(biny))
		shift_y = (nshifts*(pixelshift/float(biny)))+100
		shift_x = 5#pixelshift/binx

		#print shift_y, shift_x
		bkg = sep.Background(data, bw=64, bh=64, fw=3, fh=3)
		bkg_image = bkg.back()
		bkg_rms = bkg.rms()
		data_sub = data - bkg
		objects = sep.extract(data_sub, self.object_err_thresh, 
										err=bkg.globalrms, 
										minarea=self.object_minarea,
										filter_kernel=None,
										deblend_cont=self.deblend_cont)

		#There is a bad pixel at like 275. Remove all objects along it.
		#objects = [o for o in objects if abs(o['x'] - 275) > 1]
		#ellipticity culling
		objects = [o for o in objects if math.sqrt(1 - (o['b']*o['b'])/(o['a']*o['a'])) < self.ellipticity_thresh]

		if self.plotimages:
			plotgroup(data_sub, objects)

		groups, fwhm_av = [], []

		for o in objects:
			ox = o['x']
			oy = o['y']

			#initialize a shiftobs class	
			shiftobjects = shiftobjs()
			#find objects along the same line
			common_objects = [x for x in objects if abs(x['x'] - ox) < shift_x and abs(x['y']-oy) < shift_y]
			#we only want groupings that have the same number of shifts
			if len(common_objects) == nshifts:
				#add the objects and calculate the fwhm parameter for each, along with incrementing the focal position value
				shiftobjects.addobjs(common_objects, focalval, focalshift, data_sub)
				#test if it has already been added
				if notalreadyadded(shiftobjects, groups)and test_positions(common_objects, nshift_y):
					groups.append(shiftobjects)

					if self.plotimages:
						plotgroup(data_sub, common_objects)

					#grab the focal positions and fwhm parameters
					focs = [x.focval for x in shiftobjects.objs]
					fwhms = [x.fwhm for x in shiftobjects.objs]

					if self.thinking:
						focs, fwhms = remove_bad_points(focs, fwhms)

					#calculate the 2d polynomial interpretation
					a = np.polyfit(focs, fwhms, 2)
					b = np.poly1d(a)
					x_interp = np.arange(focs[0],focs[len(focs)-1], 0.001)
					y_interp = b(x_interp)
					#find the minimum
					miny_ind = list(y_interp).index(min(y_interp))
					minfoc = x_interp[miny_ind]

					#test to see if the minimum is on either of the low ends
					#if either is true, it didn't go through the focus
					xmin, xmax = min(x_interp), max(x_interp)

					#test concavity as well -> we want concave up -> second derivative > 0
					firstorder = np.diff(list(y_interp))
					secondorder = np.diff(firstorder)
					concave_up = np.mean(secondorder) >= 0

					#if not concave_up:
						#printv("CONCAVE DOWN", self.verbose)

					if self.plotimages:
						plotfocalfit(x_interp, y_interp, minfoc, miny_ind, focs, fwhms)

					if minfoc < (xmin + 0.125*(xmax-xmin)):
						printv("bad fit data. lowend", self.verbose)
						self.flags.append(1)
					elif minfoc > (xmin + 0.875*(xmax-xmin)):
						printv("bad fit data. high end", self.verbose)
						self.flags.append(2)
					elif not concave_up:
						printv("concave down!", self.verbose)
						self.flags.append(3)
					else:
						fwhm_av.append(minfoc)
						self.flags.append(0)

		if len(fwhm_av) != 0:
			return np.mean(fwhm_av)
		else:
			return focalval

def main():

	verbose = False
	files = [x for x in os.listdir(os.getcwd()) if '.fits' in x]
	#files = ['20180530050306-362-RA.fits']
	for f in files[:]:
		printv(f, verbose)
		focalrun = focalfit(img=f, plotimages=False, verbose=verbose)
		focalval = focalrun.run()

		printv("\n", verbose)
		printv(focalval, verbose)
		printv(focalrun.flags, verbose)
		printv("\n", verbose)
#main()

#psuedo code
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
	

