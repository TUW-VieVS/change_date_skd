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

from util import logger, find_start_time, find_end_time, update_skd_times, REGEX_SKED


class SessionTooShortException(Exception):
    pass


def rotate_schedule(path_skd, target_start):
    """
    rotate order of scans to match GSMT of new start time
    new .skd file will be stored in same folder as the input .skd file with "_rot" suffix (code_rot.skd)

    :param path_skd: path to skd file that should be manipulated
    :param target_start: new session start day and time
    :return:
    """
    logger.info(f"rotating schedule to match new start time {target_start}")
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
    original_end_time = find_end_time(skd)

    hours = (original_end_time - original_start_time).total_seconds() / 3600
    if hours != 24:
        logger.critical(f'rotating schedule only works for 24-hour sessions')
        raise SessionTooShortException()

    apy_time_start = Time(target_start, scale='utc')
    sidereal_new_start_time = apy_time_start.sidereal_time('mean', 'greenwich')
    logger.info(f"new start time start at  GMST {sidereal_new_start_time:.6f}")

    original_start_scan_time = find_best_scan_to_start(sidereal_new_start_time, skd)
    logger.info(f"new schedule starts with scan {original_start_scan_time}")
    rotate_sked(skd, target_start, original_start_scan_time)

    # write new .skd file
    out = path_skd.parent / f"{path_skd.stem}_rot.skd"
    logger.info(f"output new .skd file to {out.absolute()}")
    with open(out, 'w') as f:
        f.write("".join(skd))


def rotate_sked(skd, target_start, original_start_scan_time):
    """
    rotate sked block to match GMST

    :param skd: original skd file
    :param target_start: new start time
    :param original_start_scan_time: original start time
    :return:
    """
    start_idx = None
    end_idx = len(skd)

    # split sked block in two parts, one before new start scan and one after new start scan
    sked_block = False
    for idx, l in enumerate(skd):
        if l.strip().startswith("$"):
            if l.startswith("$SKED"):
                sked_block = True
                start_idx = idx + 1
            else:
                if sked_block:
                    end_idx = idx
                    break
    sked_block = skd[start_idx:end_idx]

    # this is sked block of scans from new start scan until session end

    # define dummy start time to be able to call update_skd_times
    new_sked_1 = []
    # this is sked block of scans from session start until new start scan
    new_sked_2 = []
    logger.info("splitting original $SKED block into two parts")
    for idx, l in enumerate(sked_block):
        if sked_block and REGEX_SKED.search(l):
            match = REGEX_SKED.search(l)
            tmp_time = datetime.datetime.strptime(match.group(1), '%y%j%H%M%S')
            if tmp_time == original_start_scan_time:
                new_sked_1 = sked_block[idx:]
                new_sked_2 = sked_block[:idx]
                logger.info(f"first block is from {tmp_time} until session end ({len(new_sked_1)} scans)")
                logger.info(f"second block is from session start until {tmp_time} ({len(new_sked_2)} scans)")
                break

    if new_sked_1:
        # define dummy start time and $sked block to be able to call update_skd_times for first sked block
        new_sked_1 = [f"START {original_start_scan_time.strftime('%y%j%H%M%S')}", "$SKED"] + new_sked_1
        update_skd_times(new_sked_1, target_start)
        logger.info(f"first block is now put to {target_start} onwards")
        new_sked_1 = new_sked_1[2:]

    # do the same for 2nd sked block
    # here, you have to align the schedule to the new end time
    if new_sked_2:
        original_first_scan_time = None
        new_last_scan_original_end_time = None
        for l in new_sked_2:
            if sked_block and REGEX_SKED.search(l):
                match = REGEX_SKED.search(l)
                original_first_scan_time = datetime.datetime.strptime(match.group(1), '%y%j%H%M%S')
                break
        for l in new_sked_2[::-1]:
            if sked_block and REGEX_SKED.search(l):
                match = REGEX_SKED.search(l)
                new_last_scan_original_start_time = datetime.datetime.strptime(match.group(1), '%y%j%H%M%S')
                tmp = l.split()
                dur = float(tmp[5])
                new_last_scan_original_end_time = new_last_scan_original_start_time + datetime.timedelta(seconds=dur)
                break
        delta_time = (new_last_scan_original_end_time - original_first_scan_time).total_seconds()
        new_sked_2 = [f"START {original_first_scan_time.strftime('%y%j%H%M%S')}", "$SKED"] + new_sked_2
        start_of_2nd_block = target_start + datetime.timedelta(1) - datetime.timedelta(seconds=delta_time)
        logger.info(f"second block is now put to {start_of_2nd_block} onwards")
        logger.info(f"check if there is enough slew time between first and second block")
        update_skd_times(new_sked_2, start_of_2nd_block)
        new_sked_2 = new_sked_2[2:]

    new_sked_block = new_sked_1 + new_sked_2
    skd[start_idx:end_idx] = new_sked_block

    update_skd_times(skd, target_start, sked=False)
    pass


def find_best_scan_to_start(target_sidereal_time, skd):
    """
    find a scan in original skd file that matches sidereal time best

    :param target_sidereal_time: target sidereal time
    :param skd: sked file
    :return:
    """
    offset = float('inf')
    new_start = None
    sked_block = False
    for l in skd:
        if l.strip().startswith("$"):
            if l.startswith("$SKED"):
                sked_block = True
            else:
                sked_block = False

        if sked_block and REGEX_SKED.search(l):
            match = REGEX_SKED.search(l)
            tmp_time = datetime.datetime.strptime(match.group(1), '%y%j%H%M%S')
            apy_time = Time(tmp_time, scale='utc')
            tmp_sidereal_time = apy_time.sidereal_time('mean', 'greenwich')

            delta = abs((tmp_sidereal_time - target_sidereal_time).value)
            if delta < offset:
                offset = delta
                new_start = tmp_time
    logger.info(f"scan at {new_start} matches new start GMST best (offset = {offset * 3600:.2f} sec)")
    return new_start


if __name__ == "__main__":
    from util import initialize_logging

    initialize_logging()
    rotate_schedule(Path('test/vo1189.skd'), datetime.datetime(2021, 7, 9, 18, 0, 0))
