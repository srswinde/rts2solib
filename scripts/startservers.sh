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

#echo Running pre start setup
#ssh -t rts2obs@bigartn /usr/local/bin/rts2_startup_settings.py;

xterm -e "ssh -t rts2obs@bigartn sudo /home/scott/git-clones/ARTN_RTS2_Proj/rts2www/__init__.py || sleep 30" &
xterm -e "ssh -t rts2obs@bigpop docker-compose -f /home/scott/git-clones/indi_webclient/docker-compose-big61.yml up -d" 
#xterm -e "ssh -t rts2obs@bigartn 'rts2-mon' " > /dev/null 2>&1 & 

sleep 8

echo "starting RTS2 Web page"
firefox http://bigartn:1080 > /dev/null 2>&1 &

ipython -i dataserver.py


ssh -t rts2obs@bigartn sudo /usr/local/bin/rts2-stop;

