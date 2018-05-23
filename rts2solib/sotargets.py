import rts2
import json
import baseclasses
import os
from astropy.coordinates import Angle
from astropy import units as u
from .db import rts2_targets
from astroquery.mpc import MPC

class so_exposure:
    def __init__( self, filter_name="R", exptime=30, num_exposures=1 ):
        self.filter = filter_name
        self.exptime = exptime
        self.num_exposures = num_exposures


    def __dictify__(self):
        thedict = {
                "filter": self.filter,
                "exptime":self.exptime,
                "amount" :self.num_exposures,
                }


       
class so_target:
    """Class to hold and save to file a target's 
	observation parameters ie fitlers, number of
	exposure etc. This is based on Sam's 
	QueueObject class.

	The specifics of the observation are saved in 
	the /home/rts2obs/.rts2scripts directory. This
	file is later read by an rts2 script to carry
	out the observation. 
	"""

    def __init__(self, name=None, ra=None, dec=None, Type=None, obs_info=None, init_method="lotis" ):
	
        if init_method=="focus":
            self.type = Type
            self.name = name
            self.ra = ra.replace('"', '').strip()
            self.dec = dec.replace('"', '').strip()
 

        if obs_info is None:
            # no obs_info given use the default
            obs_info = [so_exposure()]
        self.cfg = baseclasses.Config()

        self.type = Type
        self.name = name
        self.ra = ra.replace('"', '').strip()
        self.dec = dec.replace('"', '').strip()
        self.observation_info = obs_info
        self.id = self.create_target()


    def outputobjectinfo(self):
            print "Queue Object: {}, {}".format(self.name, self.type)
            print "RA: {}".format(self.ra)
            print "DEC: {}".format(self.dec)
            print "Observation Infos"
            for obs in self.observation_info:
                    print "     Filter: {}, Exposure Time {}, Amount {}".format(obs.filter, obs.exptime, obs.amount)


    def dictify(self):
            thedict = {
                    "name"	: self.name,
                    "type"	: self.type,
                    "ra"	: self.ra,
                    "dec"	: self.dec,
                    "id"        : self.id,
                    "obs_info" : [] 
                    
            }
            for obs in self.observation_info:
                    thedict['obs_info'].append(
                            {
                                    "filter"  : obs.filter,
                                    "exptime" : obs.exptime,
                                    "amount"  : obs.num_exposures,
                            }
                    )
            return thedict

    def __str__( self ):
        return json.dumps( self.dictify() )


    def __repr__( self ):
        return "<so_target {name} {ra} {dec}>".format( **self.dictify() )

    def save( self, save_path="/home/rts2obs/.rts2scripts", save_file=None ):
        if save_file is None:
                save_file = "{}.json".format( self.name )
        fpath = os.path.join( save_path, save_file )

        with open(fpath, 'w') as fd:
                json.dump( self.dictify(), fd, indent=2 )


    def create_target_api( self, prx=None ):
	"""This uses the rts2 api to create a target
	I would rather sqlalchemy to write directly to
	the database. 
	"""
        if prx is None:
            rts2.createProxy( "http://localhost:8889", username=self.cfg["username"], password=self.cfg["password"] )

        ra = Angle( self.ra, unit=u.hour )
        dec = Angle( self.dec, unit=u.deg )
        return rts2.target.create( self.name, ra.deg, dec.deg )

    def create_target_db( self ):
        ra = Angle( self.ra, unit=u.hour )
        dec = Angle( self.dec, unit=u.deg )
        
        # access the database
        tar = rts2_targets()

        # we leave out the tar_id as it is 
        # the primary key. Better to let the
        # the rts2_target class handle that internally
        rowvals = {
            "tar_name" : self.name,
            "tar_ra" : ra.deg,
            "tar_dec" : dec.deg,
            "tar_pm_ra" : 0,
            "tar_pm_dec" : 0,
            "interruptible" : True,
            "tar_bonus" : 0,
            "tar_enabled" : True,
            "type_id" : 'O',
        }

        return tar.addrow(** rowvals)

class asteroid(so_target):
    def __init__( self, name ):
        mpc = MPC()
        result = mpc.query_object_async( "asteroid", name=name )
        self.vals = result.json()


    def mpc_format( data ):
        pass

def test():
    fm = '00433   11.16  0.46 K1867 225.84280  178.79852  304.31681   10.82826  0.2226554  0.55993406   1.4578454  0 MPO435698  7839  51 1893-2017 0.66 M-v 38h MPCLINUX   1804    (433) Eros               20170604'
    stru = {
            'number': (1,7),
            '': ( , ),
            }
    print fm[0:7]
    print fm[8:13]
    print fm[14:19]
