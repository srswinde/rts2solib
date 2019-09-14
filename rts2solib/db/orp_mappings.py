from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData
from rts2solib import Config
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u
from astropy.time import Time
from astroplan import Observer
import datetime
import pytz


def get_orp_target_by_name(name):
    cfg = Config()
    engine = create_engine( cfg["orp_dbpath"] )
    meta = MetaData()
    meta.reflect(bind=engine)
    obsreqs = meta.tables["obsreqs"]
    session = sessionmaker(bind=engine)()
    db_resp = session.query(obsreqs).filter( obsreqs.columns["object_name"]==name )
    return db_resp



def get_session_and_table():
    cfg = Config()
    engine = create_engine( cfg["orp_dbpath"] )
    meta = MetaData()
    meta.reflect(bind=engine)
    obsreqs = meta.tables["obsreqs"]
    session = sessionmaker(bind=engine)()
    return session, obsreqs



class OrpIface(Config):

    def __init__(self):
        super().__init__()

        self.engine = create_engine( self.config["orp_dbpath"] ) 
        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)
        self.table = self.meta.tables["obsreqs"]
        self.session = sessionmaker(bind=self.engine)()


    def query( self,  filt=None ):

        
        if filt is None:
            qry = self.session.query(self.table)

        else:
            qry = self.session.query(self.table).filter(filt)

        return qry


    def query_up(self, time=None):
        if  time is None:
            time =  datetime.datetime.now( tz=pytz.timezone("US/Arizona") )

        bigelow = Observer.at_site( "mtbigelow", timezone="US/Arizona" )
        st = bigelow.local_sidereal_time( time ).deg
        lower_ra = self.__getattr__('ra_deg') > (st - 15*5) 
        upper_ra = (st + 15*5) > self.__getattr__('ra_deg')
        lower_dec = self.__getattr__('dec_deg') > -30.0 
        upper_dec = 60.0 > self.__getattr__('dec_deg')
        qry = self.query().filter(lower_ra).filter(upper_ra).filter(lower_dec).filter(upper_dec)


        return qry

    def __getattr__(self, attr):
        if attr in self.table.columns.keys():
            resp = self.table.columns[attr]

        else:
            raise AttributeError( "Attribute '{}' does not exist ".format(attr) )

        return resp


    def query_name(self, name):
        return self.query(self.__getattr__("object_name") == name)
