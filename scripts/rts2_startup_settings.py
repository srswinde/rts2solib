from rts2solib import rts2comm
import time


def main():
    time.sleep(45)
    commer = rts2comm()
    commer.set_rts2_value('SEL', "queue_only", True)
    commer.set_rts2_value("SEL", "plan_queing", 3) 
    commer.set_rts2_value("BIG61", "pec_state", 1)   
    commer.set_rts2_value("EXEC", "auto_loop", False) 
    
main()
