from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import mapper, sessionmaker

import glob
import os
from rts2solib import Config
import datetime


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


class abstract_table(object):

    def __init__(self):
        pass

    def query(self):
        Session = sessionmaker()
        session = Session()
        qr = session.query(self.__class__)
        return qr


    
    def pp(self):
        print type(self)

    def add(self):
        engine = create_engine(self.cfg["dbpath"])
        session = sessionmaker( bind=engine )()
        session.add( self )
        session.commit( )
        session.close()


def qup():
    qt=queues_targets()
    qt.queue_id = 1
    qt.qid = 1000
    qt.tar_id = 1000
    qt.time_start = datetime.datetime.now()+datetime.timedelta(hours=2)
    qt.time_end = datetime.datetime.now()+datetime.timedelta(hours=6)
    qt.cfg = Config()
    qt.add()


class rts2db_factory(object):

    def __new__(cls ):

        class newclass(abstract_table):
            pass

        cfg = Config()
        path = cfg["dbpath"]


        engine = create_engine( path )
        metadata = MetaData(engine)
        tbl = Table( cls.tblname, metadata, autoload=True )
        mapper( newclass, tbl )
        cls.cfg = cfg
        
        instance = newclass()
        instance.tblname = cls.tblname
        instance._meta = cls

        return instance

       

class targets( rts2db_factory ):
    
    tblname='targets'
        
    
class queues_targets(rts2db_factory):
    tblname="queues_targets"

class queues(rts2db_factory):
    tblname="queues"


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

    



