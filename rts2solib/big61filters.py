import rts2.rtsapi
import json
class filter_set:


    """Class to simplify look up of filter by name and number
    

    uses the python [] operator to lookup filter number
    or name. If you give it the name it will return the 
    number and vice versa. it also uses aliases for the
    lookup. RTS2 and the Galil like to use long names
    like "Harris-U" observers like short names like "U"
    either format is acceptable as long as the alias 
    is in the dictionary below. 
    """

    config_file = "/home/rts2obs/.mtnops/flask_rts2.json"
    # Filter Name Aliases. 
    # The keyword is the name of the filter as told by 
    # the galil and RTS2, the value in the dict is a tupple
    # of possible aliases for each filter
    alias = {
            "Bessell-U": ("U", 'bessell-u'),
            # "Harris-U": ("U"), 
            "Harris-R": ("R", "harris-r"), 
            "Harris-V": ("V","harris-v" ), 
            "Arizona-I": ("I",), 
            "Harris-B": ("B",),
            "Schott-8612": ("Schott",),
            "Open": ("Open", "open", "OPEN")  }


    def __init__(self, filters = None, prx=None):
        
        if filters is None:
            if prx is None:
                with open(self.config_file) as fd:
                    login=json.load(fd)   
                prx = rts2.rtsapi.createProxy( "http://localhost:8889", **login )
                filt_names = prx.getValue("W0", 'filter_names', True)
            self._filter_list = filt_names.split()

        elif type(filters) == list:
            self._filter_list = filters

        elif type(filters) == dict:
            # this assumes that the keywords of the dictionary are 
            # the fitler names and the value is the filter number. 

            
            #sort by filter number and reverse look up. 
            for key, value in sorted(filters.iteritems(), key=lambda (k,v): (v,k)):
                self._filter_list.append( key )

        elif type(filters) == str or type(filters) == unicode:
            self._filter_list = str(filters).split()

        else:
            raise TypeError("Unexpected filter type {}, type must be string, unicode, list or dict".format(type(filters)))


    def check_alias( self, alias ):
        
        for name, aliases in self.alias.iteritems():
            if alias == name:
                return alias

            else:
                for al in aliases:
                    if al == alias:
                        return name

        # we didn't find the alias
        return None
            
    def __str__(self):
        return "<filter_set: "+str(self._filter_list)+">"

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, key):
        if type(key) == int:
            return self._filter_list[key]

        elif type(key) == str or type(key) == unicode:
            realname = self.check_alias(key)
            if realname is not None:
		print(realname)
                return self._filter_list.index(realname)
        raise ValueError( "cannot find filter {}".format(key) )

        


