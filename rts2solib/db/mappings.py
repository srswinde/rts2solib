from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import mapper, sessionmaker

import glob
import os
from .. import Config
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
        print this_imdir

        return this_imdir


class abstract_row(object):

    
    def __init__(self, **kwargs):
        print "abstract_row initialized"
        for name, value in kwargs.iteritems():
            if hasattr(self, name):
                setattr(self, name, value)
            else:
                raise AttributeError("{} not in table {}".format( name, self.sql.__class__.__name__ ) )

    
    def pp(self):
        print type(self)


    def dictify(self):
        vals = copy.deepcopy(self.__dict__())
        vals.pop('_sa_instance_state')
        return vals
        

class dbtable(object):

    def __init__(self, **kwargs):

        if hasattr(self, 'tblname'):
            tblname = self.tblname
        else:
            tblname = self.__class__.tblname


        sql = type(tblname, (abstract_row,), {})


        self.cfg = Config()
        path = self.cfg["dbpath"]

        engine = create_engine( path )
        metadata = MetaData( engine )

        if hasattr(self, 'tblname'):
            tbl = Table( tblname, metadata, autoload=True)
        else:

            tbl = Table(self.__class__.__name__, metadata, autoload=True)

        mapper( sql, tbl )
        self.sql = sql()
        self.sql.engine = engine

   

    def add(self, **kwargs):
        engine = create_engine(self.cfg["dbpath"])
        session = sessionmaker( bind=engine )()
        row = self.sql.__class__( **kwargs )
        session.add( row )
        session.commit()
        return row


    

    def query(self):
        session = self.bounded_session()
        qr = session.query(self.sql.__class__)
        return qr


    def dataframe(self):
        qr = self.query()
        ex = qr.all()
        pd.read_sql(ex, )
        
 
    def bounded_session(self):
        engine = create_engine(self.cfg["dbpath"])
        session = sessionmaker( bind=engine )
        return session()

    

def qup():

    qt=queues_targets()
    qt.queue_id = 1
    qt.qid = 1000
    qt.tar_id = 1000
    qt.time_start = datetime.datetime.now()+datetime.timedelta(hours=2)
    qt.time_end = datetime.datetime.now()+datetime.timedelta(hours=6)
    qt.cfg = Config()
    qt.add()



class rts2_targets( dbtable ):
    tblname='targets'


    def keys( self ):
        return []


    def dataframe(self):
        qr=self.query()
        
        return pd.read_sql( qr.selectable, qr.session.bind )

class queues_targets(dbtable):
    tblname="queues_targets"

class queues(dbtable):
    pass

def create_session(path="postgresql://rts2obs:rts2obs@localhost/stars"):
    
    engine = create_engine( path )
    
    #initialize relational mapper
    metadata = MetaData(engine)
    
    obs = Table( "observations", metadata, autoload=True )
    mapper( Observations, obs )
    Session = sessionmaker()
    s = Session()

    return s



def main():
    session = create_session()
    resp = session.query(Observations).all()
    return resp

    

