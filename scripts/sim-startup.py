#from rts2solib import so_targets, asteroids, rts2comm
from rts2solib import rts2comm




def main():
    commer = rts2comm()
    commer.set_rts2_value('SEL', "queue_only", True)
    commer.set_rts2_value("SEL", "plan_queing", 3) 
    commer.set_rts2_value("BIG61", "pec_state", 1)   
    commer.set_rts2_value("EXEC", "auto_loop", False) 
    
    commer.set_state( 'on' )


main()
