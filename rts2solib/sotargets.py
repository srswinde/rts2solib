import rts2
import json
import baseclasses
import os
from astropy.coordinates import Angle
from astropy import units as u


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
                    "ra" 	: self.ra,
                    "dec"	: self.dec,
                    "id"        : self.id,
                    "obs_info" : [] 
                    
            }
            for obs in self.observation_info:
                    thedict['obs_info'].append(
                            {
                                    "filter"  : obs.filter,
                                    "exptime" : obs.exptime,
                                    "amount"  : obs.amount,
                                            
                            }
                    )
            return thedict

    def __str__( self ):
        return json.dumps( self.dictify() )


    def __repr__( self ):
        return "<QueueObject {name} {ra} {dec}>".format(**self.dictify())

    def save( self, save_path="/home/rts2obs/.rts2scripts", save_file=None ):
        if save_file is None:
                save_file = "{}.json".format( self.name )
        fpath = os.path.join( save_path, save_file )

        with open(fpath, 'w') as fd:
                json.dump( self.dictify(), fd, indent=2 )
            
    def create_target( self, prx=None ):
        if prx is None:
            rts2.createProxy( "http://localhost:8889", username=self.cfg["username"], password=self.cfg["password"] )

        ra = Angle(self.ra, unit=u.hour)
        dec = Angle(self.dec, unit=u.deg)
        return rts2.target.create( self.name, ra.deg, dec.deg)




class so_target2( rts2.target.Target ):

    def __init__(self, name, ra, dec):
        self.cfg = baseclasses.Config()
        self.name = name
        self.ra = ra
        self.dec = dec


        tfinfo = rts2.target.get( self.name ) 
        # target doesn't exist
        if len( tginfo ) == 0:
           ID = rts2.target.create(self.name, self.ra)
        else:
           pass



