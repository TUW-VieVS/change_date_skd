# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Copyright (c) 2021.
#  This program is free software: you can redistribute it and/or it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#  FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import datetime
import sys
from argparse import ArgumentParser
from pathlib import Path

from gmst import update_based_on_gmst
from rotate import rotate_schedule
from sky import rotate_sky
from util import logger, initialize_logging

if __name__ == "__main__":
    doc = "change the start date of a given .skd file while maintaining the same azimuth/elevation angles. " \
          "There are three options to use:" \
          "'gmst': change date but keep GMST (start time changes);" \
          "'sky' change date and time (change source location);" \
          "'rotate' change date and time and rotate schedule (change scan order);" \
          "new .skd file is stored in same folder as passed .skd file (code_gmst.skd, code_sky.skd or code_rot.skd)"

    parser = ArgumentParser(description=doc)
    parser.add_argument("-s", "--skd", required=True, help="path to .skd file")
    parser.add_argument("-t", "--time", required=True, help="target start time (format = 'yyyy-mm-dd' or "
                                                            "'yyyy-mm-ddThh:mm:ss' - all times are UTC")
    parser.add_argument("-a", "--approach", required=True, choices=["gmst", "sky", "rotate"],
                        help="chose an approach to use for changing the schedule. In case of 'gmst' only the date "
                             "date information is taken from '--time'; 'rotate' only works for 24-hour schedules")
    parser.add_argument("-l", "--log_file", default=False, help="save log to file (default = False)")
    args = parser.parse_args()
    initialize_logging("Info", args.log_file)

    if len(args.time) == 19:
        start = datetime.datetime.strptime(args.time, "%Y-%m-%dT%H:%M:%S")
    elif len(args.time) == 10:
        start = datetime.datetime.strptime(args.time, "%Y-%m-%d")
    else:
        logger.critical("unknown datetime format - use 'yyyy-mm-ddThh:mm:ss' or 'yyyy-mm-dd'")
        sys.exit()

    skd_path = Path(args.skd)
    if args.approach.lower() == "gmst":
        update_based_on_gmst(skd_path, start.date())
    elif args.approach.lower() == "sky":
        rotate_sky(skd_path, start)
    elif args.approach.lower() == "rotate":
        rotate_schedule(skd_path, start)
    else:
        logger.critical("approach not supported")
