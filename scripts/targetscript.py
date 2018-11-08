#!/usr/bin/python2

import rts2
import json
from rts2 import scriptcomm

from rts2solib.big61filters import filter_set
from rts2solib import Config
from rts2solib import to_dataserver
import os


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

        target = rts2.target.get(targetid)
        self.script = None
        if len( target ) == 0:
            self.log("E", "Can't find Target {}".format(targetid))
            self.script = None

        name = target[0][1]

        scriptjson = os.path.join(self.cfg['script_path'], "{}.json".format( name ))
        self.log("I", "id {}, name {} scriptjson {}".format(targetid, name, scriptjson))
        if os.path.exists(scriptjson):
            with open(scriptjson, 'r') as jsonfd:
                self.script = json.load( jsonfd )  
            
        self.has_exposed = False
 



    def run( self ):
        if self.script is not None:
            self.log("I", "running target {name} at {ra} {dec}".format( **self.script  ) )

            # move the object from the center of the chip
            self.setValue( 'OFFSET', '1m 0', 'BIG61')

            for exp in self.script['obs_info']:
                self.setValue("exposure", exp['exptime'] )
                try:
                    repeat = int( exp["amount"] )
                except ValueError:
                    repeat = 1
                self.log('W', "repeat is {}".format(repeat))
                for ii in range(repeat):

                    self.setValue("filter", self.filters[ exp['filter'] ], 'W0' )
                    self.log("W", "Calling exp now")
                    imgfile = self.exposure( self.before_exposure, "%b/queue/%N/%c/%t/%f" )
                    path = os.path.dirname(imgfile)
                    basename = os.path.basename(imgfile)
                    to_dataserver(imgfile, basename )

            if not self.has_exposed:
                self.setValue("exposure", 30 )
                imgfile = self.exposure(self.before_exposure)
                path = os.path.dirname(imgfile)
                basename = os.path.basename(imgfile)
                to_dataserver(imgfile, basename )

        else:
            self.log("E", "there doesn't seem to be script file taking useless 30 sec exposure")

            self.setValue("exposure",200 )
            imgfile = self.exposure(self.before_exposure, "%b/queue/%N/%c/%t/%f" )
            path = os.path.dirname(imgfile)
            basename = os.path.basename(imgfile)
            to_dataserver(imgfile, basename )


            self.log("W",imgfile )


        if self.script is not None:
            if "requeue" in self.script:
                try:
                    self.requeue('requeue', int(self.script["requeue"] ) )
                except Exception as err:
                    self.log("E", "could not requeue b/c {}".format(err) )



    def before_exposure(self):
        self.has_exposed = True



sc=scripter()
sc.run()
