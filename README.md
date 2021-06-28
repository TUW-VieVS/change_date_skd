[![Python package](https://github.com/TUW-VieVS/change_date_skd/actions/workflows/ci.yml/badge.svg)](https://github.com/TUW-VieVS/change_date_skd/actions/workflows/ci.yml)
[![test](https://badgen.net/badge/developed/SPACE@ETH/:color)](https://space.igp.ethz.ch/)
[![test](https://badgen.net/badge/license/GNUv3/)](https://www.gnu.org/licenses/gpl-3.0.txt)
# Change session start time in .skd file 

There are three supported strategies:

## GMST 
Changes the date by adjusting the start time to keep scans to same Greenwich mean sidereal time (GMST). 

## sky 
Changes the date and time by adjusting the source right ascension to keep the same azimuth/elevation angles. 

**Warning:** Note that this is only useful if you run a dry run, meaning, you do not plan to correlate the data. 

## rotate 
Changes the date and time by rotating the scan sequence (it starts by observing the scan with closest GMST of the new session start time in the original schedule. From there on, it continues to observe all scans keeping the order of the original schedule. At the original session end, it start by adding the first scans from the original schedule until all scans are scheduled)
    
Only works for 24 hour sessions. 

**Warning**: At the wrap from the end of the original schedule to the first scan of the original schedule, it could happen that there is not enough slew time. The script will add the maximum available time between these two scans. However, you have to check if this is enough (either using `VieSched++` or `sked`). If it is not enough, you have to manually delete a scan. Have a look at the log output to see where the wrapping of the schedule end to the schedule start occurs.  

# installation

    git clone https://github.com/TUW-VieVS/change_date_skd.git
    cd change_date_skd
    python -m venv venv
    pip install -r requirements.txt 
    
# usage 

have a look at `python main.py -h` for a full list of options

Example:

    python main.py -s path/to/skd/file -t yyyy-mm-dd -a gmst
    python main.py -s path/to/skd/file -t yyyy-mm-ddThh:mm:ss -a sky
    python main.py -s path/to/skd/file -t yyyy-mm-ddThh:mm:ss -a rotate
