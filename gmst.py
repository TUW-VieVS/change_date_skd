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
from pathlib import Path

from astropy.time import Time

from util import logger, find_start_time, update_skd_times


def update_based_on_gmst(path_skd, date):
    """
    change date in .skd file and adjust start time in a way that GMST of first scan stays the same
    new .skd file will be stored in same folder as the input .skd file with "_gmst" suffix (code_gmst.skd)

    :param path_skd: path to skd file that should be manipulated
    :param date: new session start date
    :return: None
    """

    logger.info(f"finding perfect start time for {date} that matches GMST")
    skd = Path(path_skd)
    if not skd.is_file():
        logger.critical(f'The following skd file {skd.absolute()} was not found')
        raise FileNotFoundError(f'The following skd file {skd.absolute()} was not found')

    # read original .skd
    skd = []
    with open(path_skd) as f:
        skd = f.readlines()

    # get original session start time and GMST
    original_start_time = find_start_time(skd)
    apy_time = Time(original_start_time, scale='utc')
    sidereal_start_time = apy_time.sidereal_time('mean', 'greenwich')

    logger.info(f"session start time in skd file {original_start_time} (GMST {sidereal_start_time:.4f})")

    new_start_time = find_time_equal_gmst(date, sidereal_start_time)

    # update .skd file with new times
    update_skd_times(skd, new_start_time)

    # write new .skd file
    out = path_skd.parent / f"{path_skd.stem}_gmst.skd"
    logger.info(f"output new .skd file to {out.absolute()}")
    with open(out, 'w') as f:
        f.write("".join(skd))


def find_time_equal_gmst(target_date, target_gmst):
    """
    brute force find for a time of target_date that has the required target_gmst

    not very elegant but simple, easy to code, and fast enough in execution :-)

    :param target_date: date for which time with equal GMST should be found
    :param target_gmst: target GMST
    :return: time with date target_date and GMST target_gmst
    """
    target_time = datetime.datetime.combine(target_date, datetime.datetime.min.time())
    logger.info("brute force find new time with equal GMST")
    # find hour
    for h in range(0, 24):
        tmp = target_time + datetime.timedelta(hours=h)
        tmp_apy_time = Time(tmp, scale='utc')
        sidereal_time = tmp_apy_time.sidereal_time('mean', 'greenwich')
        delta_angle = (sidereal_time - target_gmst).value
        if 0 < delta_angle < 1.1:
            target_time = target_time + datetime.timedelta(hours=(h - 1))
            break
    else:
        target_time = target_time + datetime.timedelta(hours=23)

    # find minute
    for m in range(-5, 65):
        tmp = target_time + datetime.timedelta(minutes=m)
        tmp_apy_time = Time(tmp, scale='utc')
        sidereal_time = tmp_apy_time.sidereal_time('mean', 'greenwich')
        delta_angle = (sidereal_time - target_gmst).value
        if 0 < delta_angle < 1.1 / 60:
            target_time = target_time + datetime.timedelta(minutes=(m - 1))
            break

    # find second
    start_time = None
    offset = float('inf')
    for s in range(-5, 65):
        tmp = target_time + datetime.timedelta(seconds=s)
        tmp_apy_time = Time(tmp, scale='utc')
        sidereal_time = tmp_apy_time.sidereal_time('mean', 'greenwich')
        delta_angle = abs((sidereal_time - target_gmst).value)
        if delta_angle < offset:
            start_time = tmp
            offset = delta_angle

    logger.info(
        f"best match for {start_time.date()} is {start_time.time()} with GMST offset of {offset * 3600:.4f} arcsec")
    return start_time


if __name__ == "__main__":
    from util import initialize_logging

    initialize_logging()
    update_based_on_gmst(Path('test/vt1176.skd'), datetime.datetime(2021, 6, 22))
