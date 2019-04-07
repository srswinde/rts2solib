from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData
from rts2solib import Config




def get_orp_target_by_name(name):
    cfg = Config()
    engine = create_engine( cfg["orp_dbpath"] )
    meta = MetaData()
    meta.reflect(bind=engine)
    obsreqs = meta.tables["obsreqs"]
    session = sessionmaker(bind=engine)()
    db_resp = session.query(obsreqs).filter( obsreqs.columns["object_name"]==name )
    return db_resp


