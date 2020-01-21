#!/usr/bin/python3

# Sidereal targets
import sys
sys.path.insert(0, "/home/rts2obs/git-clones/rts2solib")

from rts2solib import Queue

from rts2solib import stellar, so_exposure


# two 30 second exposures in filters R and U
# the amount arg is how many repititions.
exps = [
        so_exposure(Filter='R', exptime=30, amount=1),
        so_exposure(Filter='U', exptime=30, amount=1)
        ]

# create the target
test_target = stellar(
        name="testtarg", # the name cannot end with "target"
        ra="10:00:00", 
        dec="32:00:00", 
        obs_info=exps, 
        artn_obs_id="obsid", 
        artn_group_id="grpid" )





# before a target can be queued up for the 
# night it needs to be added to the rts2
# database. This is done by the save method
# It will assign it a target id
# if a target of the same name already exists
# it will reload that target.
test_target.save()


print(test_target.id)


# now we create the night queue it is called plan.
q = Queue( "plan" )
q.add_target(test_target.id)

# if you have more than target you can add them here
# with 
# q.add_target(test_target2.id)
# q.add_target(test_target3.id)
# q.add_target(test_target4.id)
# ...


q.load() # load the added targets to a list
q.save() # give rts2 the queue. 






