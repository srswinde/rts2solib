#!/bin/bash


killall -9 galilserver
echo Starting galilserver
galilserver > /dev/null 2>&1 &
echo "Stopping RTS2"
ssh -t rts2obs@bigartn sudo /usr/local/bin/rts2-stop;
echo Starting RTS2

ssh -t rts2obs@bigartn sudo /usr/local/bin/rts2-start;
echo "Starting Safe Telescope GUI" 

sleep 2.0

# for some reasone these need to not fork on the 
# remote machine but forked here. 
xterm -e "ssh -t rts2obs@bigartn sudo /usr/local/bin/rts2-start -l C0" &
xterm -e "ssh -t rts2obs@bigartn sudo /usr/local/bin/rts2-start -l W0" &

saferts2.py &
