import os
import json


class Config( object ):

    def __init__( self ):
        fname = os.path.join( "/home/rts2obs", '.mtnops', 'rts2_config.json' )
        with open( fname ) as fd:
            self.config = json.load(fd)


    
    def __getitem__(self, key):
        return self.config[key]


