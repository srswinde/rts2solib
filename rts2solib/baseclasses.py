import os
import json
from pathlib import Path


class Config( object ):

    def __init__( self ):
        rts2path = os.environ.get("RTS2SOLIBPATH")
        if rts2path is None:
            #TODO stop hardcoding directory names
            fname = Path( "/home/scott", '.mtnops', 'rts2_config.json' )
        else:
            fname = Path( rts2path, 'rts2_config.json' )

        with fname.open() as fd:
            self.config = json.load(fd)


    
    def __getitem__(self, key):
        return self.config[key]


