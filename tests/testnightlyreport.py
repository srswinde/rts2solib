import datetime
from rts2solib.db import rts2_images, rts2_observations, rts2_targets 
from datetime import timedelta


class obsinfo():
	def __init__(self, name, ra, dec):
		self.name = name
		self.ra = ra
		self.dec = dec



def nightlyreportshit():
	now = datetime.datetime.now()
	nowtime = now.time()
	nowhour = nowtime.hour

	nownow = now - timedelta(days=1)
	obs = rts2_observations()
	tars = rts2_targets()
	dummys = range(1800, 1900, 1)
	nightlyobs = obs.query().filter(obs._rowdef.obs_id.in_(dummys)).all()
	tarids = [x.tar_id for x in nightlyobs]
	obsids = [x.obs_id for x in nightlyobs]
	
	targets = tars.query().filter(tars._rowdef.tar_id.in_(tarids)).all()

	imgs = rts2_images()
	nightlyimages = imgs.query().filter(imgs._rowdef.obs_id.in_(obsids)).all()
	imgids = [x.obs_id for x in nightlyimages]


	for ob in nightlyobs:
		tar = [t for t in targets if t.tar_id == ob.tar_id][0]
		if 'Dark' not in tar.tar_name and 'Flat' not in tar.tar_name:
			print tar.tar_name, tar.tar_ra, tar.tar_dec, ob.obs_id
			images = [i for i in nightlyimages if i.obs_id == ob.obs_id]
			for im in images:
				print "     ", im.img_date, im.img_exposure, im.filter_id

	#print tarids
	#print obsids
	#print imgids

nightlyreportshit()

