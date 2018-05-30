from __future__ import print_function
import rts2
import json
import baseclasses
import os
from astropy.coordinates import Angle
from astropy import units as u
from .db.mappings import rts2_targets
from astroquery.mpc import MPC
from rts2_wwwapi import rts2comm

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
 
    def __repr__(self):
        return json.dumps( self.__dictify__() )


    def __getitem__( self, key ):
        return self.__dictify__()[key]

class so_target(object):
    """Class to hold and save to file a target's 
	observation parameters ie filters, number of
	exposure etc. This is based on Sam's 
	QueueObject class.

	The specifics of the observation are saved in 
	the /home/rts2obs/.rts2scripts directory. This
	file is later read by an rts2 script to carry
	out the observation. 
	"""

    def __init__(self, name, ra=None, dec=None, Type=None, tar_info=None, obs_info=None ):
	

        """Constructor method

        params:
            name: str 
                The name of the object must be uniqure from other objects in the database
            ra : str sexagesimal ra coordinate

            dec: str sexagesimal dec coordinate

            Type: char 
                The value of the type_id in the database this differentiates between
                stellar 'O' and non stellar 'E' and callibration. 

            tar_info: str
                Extra information about target like MPC or TLE. This corresponds to the
                tar_info in the database

            obs_info: list (of so_exposure)
                Information specific to the observation ie filters, exposure time etc. 

        """

        if obs_info is None:
            # no obs_info given use the default
            obs_info = [so_exposure()]
        self.cfg = baseclasses.Config()

        self.type = Type
        self.name = name
        assert self.type in ['O', 'E'], 'Using unsuported type {}'.format(self.type)
        if self.type is 'O':
            assert ra is not None and dec is not None, "Stellar like object Type O, should populate both ra and dec"

        elif self.type is 'E':
            assert tar_info is not None, "Asteroid objects type E, should populate tar_info"

        if ra is not None:
            self.ra = ra.replace('"', '').strip()
        else:
            self.ra = None
            assert dec is None, "if ra is not populated dec should not be populated."

        if dec is not None:
            self.dec = dec.replace('"', '').strip()
        else:
            self.dec = None
            assert ra is None, 'If dec is not populated ra should not be populated'


        self.observation_info = obs_info
        self.save()
        #self.id = self.create_target_db()


    def outputobjectinfo(self):
            print("Queue Object: {}, {}".format(self.name, self.type))
            print("RA: {}".format(self.ra))
            print("DEC: {}".format(self.dec))
            print("Observation Infos")
            for obs in self.observation_info:
                    print("     Filter: {}, Exposure Time {}, Amount {}".format(obs.filter, obs.exptime, obs.amount))


    def dictify(self):
            thedict = {
                    "name"	: self.name,
                    "type"	: self.type,
                    "ra"	: self.ra,
                    "dec"	: self.dec,
                    #"id"        : self.id,
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
        dbresp = self.create_target_db()
        self.id = dbresp.tar_id
	commer=rts2comm()
	commer.setscript(self.id, script="exe /home/rts2obs/.local/bin/targetscript.py")

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
        if self.type is not 'O':
            raise NotImplementedError("This type of target ({}) can not be saved to db".format(self.type))
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


class stellar(so_target):

    def __init__(self, name, ra, dec, obs_info=None ):

        super( self.__class__, self ).__init__(name, ra, dec, obs_info=obs_info, Type='O')

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

    def __init__( self, name, jsondata=None, mpc=None, obs_info=None ):
        mpc = MPC()
        result = mpc.query_object_async( "asteroid", name=name )
        
        self.vals = result.json()[0]
        self.mpc = self.mpc_format()
        super(self.__class__, self).__init__(name=self.vals['name'], Type='E', tar_info=self.mpc, obs_info=obs_info)



    def mpc_format( self ):

        stru = {
            'number': (1,7, '07d' ),
            'absolute_magnitude': (9 ,13 , '5.2f'),
            'phase_slope': (15 ,19 , '4.2f'),
            'epoch': ( 21, 25 , None ), # needs to be packed
            'mean_anomaly': ( 27, 35 , '8.5f'),
            'argument_of_perihelion': (38 ,46 , '8.5f' ),
            'ascending_node': ( 49, 57 , '8.5f' ),
            'inclination': ( 60, 68 , '8.5f' ),
            'eccentricity': ( 71, 79 , '8.7f' ),
            'mean_daily_motion': ( 81, 91, '10.8f' ),
            'semimajor_axis': ( 93, 103 , '10.7f' ),
            'orbit_uncertainty': ( 106, 106 , '1s'),
            'reference': ( 108, 116 , None ),
            'observations': ( 118, 122 , '05d'),
            'oppositions': ( 124, 126 , '03d'),
            'residual_rms': (138, 141, '4.2f' ),
            'first_observation_date_used': (128, 132, None ),
            'last_observation_date_used': (133, 136, None ),
            }

        thestr = [' ']*140
        for fkey, finfo in stru.iteritems():
            fpos = finfo[:2]
            fmt = finfo[2]
            numchars = ( fpos[1] - fpos[0] )+1
            if fkey in self.vals:
                strval = str( self.vals[fkey] )
                if fkey is 'epoch':
                    # The most obnoxious format:
                    # https://minorplanetcenter.net/iau/info/PackedDates.html
                    y,m,d = [ int(float(diter)) for diter in self.vals[fkey].split('-') ]
                    century = int(str(y)[:2])
                    cenchar = {18:'I', 19:'J', 20:'K'}[century]
                    day_month = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 
                            'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V']
                    daychar = day_month[d-1]
                    monchar = day_month[m-1]
                    strval = "{:1s}{:2d}{:1s}{:1s}".format(cenchar, y-century*100, monchar, daychar )

                elif fkey is 'first_observation_date_used':
                    strval=self.vals[fkey].split('-')[0]
                    strval=strval+'-'

                elif fkey is 'last_observation_date_used':
                    strval=self.vals[fkey].split('-')[0]

                if fmt is not None:
                    if fmt[-1] == 'd':
                        fval = format( int( strval ), fmt)

                    elif fmt[-1] == 'f':
                        fval = format( float(strval), fmt)

                    else:
                        fval = format(strval, fmt)
                else:
                    fval = strval

                listval = list( fval )
                
                diff = (numchars - len( fval ))
                
                if diff > 0:
                    
                    padded = diff *[' ']
                    padded.extend(listval)
                    listval = padded

                elif diff < 0:
                    raise ValueError("{}'s value, {}, has too many chars ({}) should be < {}".format(fkey, fval, len(fval), numchars))
                    


                thestr[fpos[0]-1:fpos[1]] = listval 
            else:
                thestr[fpos[0]-1:fpos[1]] = ['X']*(numchars)
        #extras

        return ''.join( thestr )


    def create_target_db(self):
        tar = rts2_targets()

        kwargs = {
            'tar_name':self.name,
            'tar_info':self.mpc,
            'type_id':self.type
        }
        tar.addrow(**kwargs)
                




fm = '00433   11.16  0.46 K1867 225.84280  178.79852  304.31681   10.82826  0.2226554  0.55993406   1.4578454  0 MPO435698  7839  51 1893-2017 0.66 M-v 38h MPCLINUX   1804    (433) Eros               20170604'

def test():

    for valname, pos in stru.iteritems():
        print(valname, fm[ pos[0]-1: pos[1] ])


def test2():
    kwargs = {'tar_name': 'ceres', 'tar_info':fm}
    t=rts2_targets()
    t.addrow(**kwargs)
