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
import re
from pathlib import Path

from astropy.time import Time

from util import logger, find_start_time, update_skd_times

REGEX_SOURCE = re.compile(r'\s*[^\s]*\s+[^\s]+\s+(\d+)\s+(\d+)\s+(\d+\.\d+)\s+[+\d-]*\s+\d+\s+\d+\.\d+')


def rotate_sky(path_skd, target_start):
    """
    rotate source right ascension to be able to do a dry-run of sessions at arbitrary starting times
    new .skd file will be stored in same folder as the input .skd file with "_sky" suffix (code_sky.skd)

    :param path_skd: path to skd file that should be manipulated
    :param target_start: new session start day and time
    :return:
    """
    logger.info(f"rotating sources to match new start time {target_start}")
    skd = Path(path_skd)
    if not skd.is_file():
        logger.critical(f'The following skd file {skd.absolute()} was not found')
        raise FileNotFoundError(f'The following skd file {skd.absolute()} was not found')

    # read original .skd
    skd = []
    with open(path_skd) as f:
        skd = f.readlines()

    # get GMST of original start and new start time
    original_start_time = find_start_time(skd)
    apy_time_start = Time(original_start_time, scale='utc')
    sidereal_original_start_time = apy_time_start.sidereal_time('mean', 'greenwich')

    apy_time_target = Time(target_start, scale='utc')
    sidereal_original_target_time = apy_time_target.sidereal_time('mean', 'greenwich')

    diff = (sidereal_original_target_time - sidereal_original_start_time).value

    logger.info(f"GMST difference is {diff} hours")
    rotate_sources(skd, diff)

    # update .skd file with new times
    update_skd_times(skd, target_start)

    # write new .skd file
    out = path_skd.parent / f"{path_skd.stem}_sky.skd"
    logger.info(f"output new .skd file to {out.absolute()}")
    with open(out, 'w') as f:
        f.write("".join(skd))


def rotate_sources(skd, diff):
    """
    change right ascension of sources

    :param skd: skd file
    :param diff: angle to rotate right ascension
    :return:
    """
    source_block = False
    for idx, l in enumerate(skd):
        if l.strip().startswith("$"):
            if l.startswith("$SOURCE"):
                source_block = True
            else:
                source_block = False

        if source_block and REGEX_SOURCE.search(l):
            match = REGEX_SOURCE.search(l)
            # get hour minute second of right ascension
            orig_hour_grp = match.regs[1]
            orig_hour = float(l[orig_hour_grp[0]:orig_hour_grp[1]])
            orig_minute_grp = match.regs[2]
            orig_minute = float(l[orig_minute_grp[0]:orig_minute_grp[1]])
            orig_second_grp = match.regs[3]
            orig_second = float(l[orig_second_grp[0]:orig_second_grp[1]])

            orig_hms = orig_hour + orig_minute / 60 + orig_second / 3600

            # rotate based on GMST difference
            target_hms = (orig_hms + diff) % 24

            # split into hour minute second
            target_hour_str = f"{int(target_hms):02d}"
            target_minute_str = f"{int(target_hms * 60 % 60):02d}"
            target_second_str = f"{target_hms * 3600 % 60:.5f}"

            # update entry
            skd[idx] = l[:orig_hour_grp[0]] + target_hour_str + l[orig_hour_grp[1]:orig_minute_grp[0]] + \
                       target_minute_str + l[orig_minute_grp[1]:orig_second_grp[0]] + target_second_str + \
                       l[orig_second_grp[1]:]

            pass


if __name__ == "__main__":
    from util import initialize_logging

    initialize_logging()
    rotate_sky(Path('test/vt1176.skd'), datetime.datetime(2021, 1, 25, 18, 30, 0))
