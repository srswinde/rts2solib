from sqlalchemy import create_engine, MetaData, Table, func
from sqlalchemy.orm import mapper, sessionmaker

import glob
import os
from ..baseclasses import Config
import datetime
import copy
import pandas as pd
IMDIR = "/home/rts2obs/rts2images/queue"
CAMERA = "C0"

#object to map to database
class Observations(object):
    pass

    def __str__(self):
        return str(self.dict())

    
    def __iter__(self):
        for key in self.keys():
            yield key, self.__dict__[key]


    def dict(self):
        return dict( [(key,val) for key, val in self.__iter__()] )


    def keys(self):
        return (
            "obs_ra",        
            "plan_id", 
            "obs_alt",
            "obs_dec",
            "obs_state",
            "obs_start",
            "obs_id",
            "obs_end",
            "obs_az",
            "tar_id",
            "obs_slew",
            "user_input"
        )


    def duration(self):
        if self.obs_start and self.obs_end:
            return self.obs_end - self.obs_start

    def find_images(self):

        #TODO: need to make this work for beggining of month and year
        if( self.obs_start.hour < 12 ):
            day = self.obs_start.day - 1
        else:
            day = self.obs_start.day 
        
        imdatestr = "{}{}{}".format(self.obs_start.year, self.obs_start.month, day)
        this_imdir = "{}/{}/{}/{:05d}".format(IMDIR, imdatestr, CAMERA, self.tar_id)

        imnames = glob.glob(this_imdir)
        #TODO: read the list of files in convert their names (They are in UTC) to dates and compare that with the start and end observation times. 


        return this_imdir


class abstract_row(object):
    """This is the abstract defintion of the 
    dbtable.sql member of dbtable."""
    
    def __init__(self, **kwargs):
        for name, value in kwargs.iteritems():
            if hasattr(self, name):
                setattr(self, name, value)
            else:
                raise AttributeError("{} not in table ".format( name ) )

    
    def pp(self):
        print type(self)


    def dictify(self):
        vals = copy.deepcopy(self.__dict__())
        vals.pop('_sa_instance_state')
        return vals
        
    def addrow(self, **kwargs):
        """This shouldn't be called but it is when 
        we use the super(...).addrow in the rts2_targets
        class not sure why! Somehow t._rowdef and rts2_targets
        are considered siblings. Again not sure why."""
        pass


class dbtable(object):

    """This is an abstract class for database
    interaction. Table specific classes should 
    inherit from this class. """

    def __init__(self, **kwargs):

        if hasattr(self, 'tblname'):
            tblname = self.tblname
        else:
            tblname = self.__class__.tblname

        # On the fly class creation.
        # the sqlalchemy orm mapper depends on
        # mapping the class and not the instance
        # Therefore, we need to create a class
        # on the fly to map to the specific table
        self._rowdef = type(tblname, (abstract_row,), {})


        self.cfg = Config()
        path = self.cfg["dbpath"]

        engine = create_engine( path )
        metadata = MetaData( engine )

        if hasattr(self, 'tblname'):
            tbl = Table( tblname, metadata, autoload=True)
        else:

            tbl = Table(self.__class__.__name__, metadata, autoload=True)

        mapper( self._rowdef, tbl )
        self._rowdef.engine = engine
        self.tbl = tbl

   
    def column_names( self ):
        return [str(col).replace("{}.".format(self.tbl.name), '') for col in self.tbl.columns]

    def columns(self):
        return self.tbl.columns

    def rmrow( self, pkval ):
        pk = self.primary_key()
        qr = self.query()
        qr.filter(pk==pkval).delete()
        qr.session.commit()
        
        

    def addrow(self, **kwargs):
        """Add a row to the database table"""

        updater = {}
        pk = self.primary_key()
        for col in self.columns():
            if col.name == pk.name:
             # for the primary key have a default
             # value one greater than the last
                if col.name not in kwargs:
                    
                    kwargs[pk.name] = self.pkmax()+1

   
            elif col.name not in kwargs:
                if col.nullable:
                    # send null value to database
                    updater[col.name] = None

                else:
                    raise ValueError("{} is not in the addrow args and it must have a value in this row (not nullable)".format( col.name ))

        kwargs.update(updater)
        engine = create_engine(self.cfg["dbpath"])
        session = sessionmaker( bind=engine )()
        row = self._rowdef( **kwargs )

        session.add( row )
        session.commit()

        return row

        
    def primary_key(self):
        for col in self.columns():
            if col.primary_key:
                return col

    def query(self):
        """query object to pull data from the db."""
        session = self.bounded_session()
        qr = session.query(self._rowdef )
        return qr

        
    def pkmax(self):
        """Get the max primary key so we don't reuse it"""
        pk = self.primary_key()
        session = self.bounded_session()
        return session.query(func.max(pk) ).scalar()

    def dataframe(self):
        """ Put all rows in the database into a pandas data frame."""
        qr = self.query()
        ex = qr.all()
        pd.read_sql( ex, )
        
 
    def bounded_session(self):
        engine = create_engine(self.cfg["dbpath"])
        session = sessionmaker( bind=engine )
        return session()

    



class rts2_targets( dbtable ):
    tblname='targets'

    fm = '00433   11.16  0.46 K1867 225.84280  178.79852  304.31681   10.82826  0.2226554  0.55993406   1.4578454  0 MPO435698  7839  51 1893-2017 0.66 M-v 38h MPCLINUX   1804    (433) Eros               20170604'

    def keys( self ):
        return []


    def dataframe(self):
        qr=self.query()
        
        return pd.read_sql( qr.selectable, qr.session.bind )

    def addrow( self, **kwargs ):
        print ("adding row")
        defaults = {
            "tar_enabled" : True,
            "tar_priority" : 0,
            "tar_bonus" : 0, 
            "interruptible": True, 
            "tar_pm_ra": 0,
            "tar_pm_dec":0,
            
        }
        if "tar_name" in kwargs:
            tarnames = self.query().filter(self.columns()['tar_name']==kwargs['tar_name']).all()
            if len(tarnames) > 0:
                raise ValueError("tar_name {} already exists as {}".format(kwargs['tar_name'], tarnames[0].tar_id) )

        else:
            raise ValueError("tar_name must have a value. Like: tar.addrow(tar_name='thename',ra=142, ...)")
        
        if "type_id" in kwargs:
            if kwargs["type_id"] == 'O':
                if "tar_ra" not in kwargs or "tar_dec" not in kwargs:
                    raise ValueError("For target type opportunity 'O' the tar_ra and tar_dec values must be set")

            elif kwargs['type_id'] == 'E':
                if "tar_info" not in kwargs:
                    raise ValueError("For target type elliptical 'E', the tar_info must be set to the MPC format.")
                assert len(kwargs['tar_info']) >= 126,\
	    		    "MPC orbit format must be atleast 126 charachters have a look:\
                     https://minorplanetcenter.net/iau/info/MPOrbitFormat.html" 

            else:
                raise NotImplementedError("type_id '{}' has not been implemented yet.".format(kwargs['type_id']))
        else:
            raise ValueError("type_id must have a value")

        for dkey, dval in defaults.iteritems():
            if dkey not in kwargs:
                kwargs[dkey] = dval

    
        super(rts2_targets, self).addrow( **kwargs )

    
        
class queues_targets(dbtable):
    tblname="queues_targets"

class queues(dbtable):
    pass


