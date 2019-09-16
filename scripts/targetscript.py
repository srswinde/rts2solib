#!/usr/bin/python2

import rts2
import json
from rts2 import scriptcomm

from rts2solib.big61filters import filter_set
from rts2solib import Config
from rts2solib import to_dataserver
import requests
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from telescope import kuiper
import datetime
import math

class scripter(scriptcomm.Rts2Comm):
    """
        Rts2Comm scripter class

        Description:
        Reads and executes the instructions
        in the json script file.
    """

    def __init__( self  ):
        scriptcomm.Rts2Comm.__init__(self)
        self.cfg = Config()
        self.filters = filter_set()
        targetid = self.getValue("current_target", "SEL")
        self.tel = kuiper()
        self.tel.comBIAS("OFF")
        self.script = None
#        target = rts2.target.get(targetid)
#        self.script = None
#        if len( target ) == 0:
#            self.log("E", "Can't find Target {}".format(targetid))
#            self.script = None

        name = self.getValue("current_name", "EXEC")

        engine = create_engine( self.cfg["orp_dbpath"] )
        meta = MetaData()
        meta.reflect(bind=engine)
        obsreqs = meta.tables["obsreqs"]
        session = sessionmaker(bind=engine)()
        db_resp = session.query(obsreqs).filter(obsreqs.columns["rts2_id"]==targetid)
        self.script = db_resp[0].rts2_doc
        self.setValue('ObservationID', db_resp[0].observation_id, "C0")
        self.setValue('GroupID', db_resp[0].group_id, "C0")

        if db_resp[0].non_sidereal:
            self.rates = db_resp[0].non_sidereal_json
            self.tel.comBIAS("ON")

            # The idea here is that the non sidereal
            # targets will have an RA and Dec, RA Bias rate, Dec bias rate,
            # position epoch, object time epoch, position angle, bias_percentage
            # and object rate. The telescope should go to the coordinates
            # RA+sin(position_angle)*object_rate, Dec+cos(position_angle)*object_rate
            # and set the bias rates to 
            # RA_bias_rate*bias_percentage, Dec_bias_rate*bias_percentage
            # Scott June 2019

            dt_epoch = pytz.utc.localize(datetime.datetime.strptime(self.rates["UTC_At_Position"], "%Y-%m-%dT%H:%M:%S"))
            now = pytz.utc.localize(datetime.datetime.now())
            delta_time = dt_epoch-now
            
            position_angle = float(self.rates['PositionAngle'])*math.pi/180
            object_rate = float(self.rates['ObjectRate'])
            ra_obj_rate = object_rate*math.sin(position_angle)
            dec_obj_rate = object_rate*math.cos(position_angle)
            ra_offset = ra_obj_rate*delta_time.total_seconds()
            dec_offset = dec_obj_rate*delta_time.total_seconds()

            rapct = float(self.rates["RA_BiasPerCent"])
            decpct = float(self.rates['Dec_BiasPerCent'])
            biasra = float(self.rates["RA_BiasRate"])*rapct/100.0
            biasdec = float(self.rates["Dec_BiasRate"])*decpct/100.0

            self.log("I", "Setting rates to {} {}".format(biasra, biasdec))
            self.tel.command("BIASRA {}".format(biasra))
            self.tel.command("BIASDEC {}".format(biasdec))

            self.log("I", "object_rate:{} position_angle:{} now:{} dt_epoch:{}".format(object_rate, position_angle, now, dt_epoch) )
            self.log("I", "Setting offset to {}s {}s".format(ra_offset, dec_offset))
            self.setValue( 'woffs', '{}s {}s'.format(ra_offset, dec_offset), 'BIG61')

            


        
        
        

#        scriptjson = os.path.join(self.cfg['script_path'], "{}.json".format( name ))
#        self.log("I", "id {}, name {} scriptjson {}".format(targetid, name, scriptjson))
#        self.log("I", "DOES THIS CHANGE IT?????????")
#        if os.path.exists(scriptjson):
#            with open(scriptjson, 'r') as jsonfd:
#                self.script = json.load( jsonfd )  
            
        self.has_exposed = False
 



    def run( self ):
        if self.script is not None:
            self.setValue("SHUTTER", 0, "C0")
            self.log("I", "running target {name} at {ra} {dec}".format( **self.script  ) )

            # move the object from the center of the chip
            #self.setValue( 'woffs', '1m 0', 'BIG61')
            total_exposures = 0
            for exp in self.script['obs_info']:
                total_exposures += int( exp["amount"] )

            exp_num = 0
            for exp in self.script['obs_info']:
                self.setValue("exposure", exp['exptime'] )
                try:
                    repeat = int( exp["amount"] )
                except ValueError:
                    repeat = 1
                self.log('W', "repeat is {}".format(repeat))
                for ii in range(repeat):
                    if exp['Filter'].lower() == 'clear':
                        filt = 'Open'
                    else:
                        filt = exp['Filter']

                    self.setValue("filter",self.filters[exp['Filter']], 'W0' )
                    exp_num+=1
                    self.log("W", "Calling exp {} of {}".format(exp_num, total_exposures) )
                    self.log("W", "exp string is %b/queue/%N/%c/%t/%f" )
                    imgfile = self.exposure( self.before_exposure, "%b/queue/%N/%c/%t/%f" )
                    self.log("W", "imgfile is {}".format(imgfile))
                    self.log("W", "did we get here")
                    path = os.path.dirname(imgfile)
                    basename = os.path.basename(imgfile)
                    try:
                        to_dataserver(imgfile, basename )
                    except Exception as err:
                        self.log("W", "Could not send to dataserver {}".format(err))

            if not self.has_exposed:
                self.setValue("exposure", 30 )
                imgfile = self.exposure(self.before_exposure)
                path = os.path.dirname(imgfile)
                basename = os.path.basename(imgfile)
                try:
                    to_dataserver(imgfile, basename )
                except Exception as err:
                    self.log("W", "Could not send to dataserver {}".format(err))


        else:
            self.log("E", "there doesn't seem to be script file taking useless 30 sec exposure")

            self.setValue("exposure",200 )
            imgfile = self.exposure(self.before_exposure, "%b/queue/%N/%c/%t/%f" )
            path = os.path.dirname(imgfile)
            basename = os.path.basename(imgfile)
            try:
                to_dataserver(imgfile, basename )
            except Exception as err:
                self.log("W", "Could not send to dataserver {}".format(err))



            self.log("W",imgfile )


        if self.script is not None:
            if "requeue" in self.script:
                try:
                    self.requeue('requeue', int(self.script["requeue"] ) )
                except Exception as err:
                    self.log("E", "could not requeue b/c {}".format(err) )

        self.tel.comBIAS("OFF")       

    def before_exposure(self):
        self.has_exposed = True



sc=scripter()
sc.run()
