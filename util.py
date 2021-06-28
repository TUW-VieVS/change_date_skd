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
import logging
import re
from pathlib import Path

logger = logging.getLogger('EOP_PCC')

# some helper regex
REGEX_START = re.compile(r"START\s+(\d{11})")
REGEX_END = re.compile(r"END\s+(\d{11})")
REGEX_SKED = re.compile(r"PREOB\s+(\d{11})")


def find_start_time(skd):
    """
    extract session start time

    :param skd: skd file
    :return:
    """
    original_start_time = None
    for l in skd:
        if REGEX_START.search(l):
            match = REGEX_START.search(l).group(1)
            original_start_time = datetime.datetime.strptime(match, '%y%j%H%M%S')
            break
    return original_start_time


def find_end_time(skd):
    """
    extract session end time

    :param skd: skd file
    :return:
    """
    original_end_time = None
    for l in skd:
        if REGEX_END.search(l):
            match = REGEX_END.search(l).group(1)
            original_end_time = datetime.datetime.strptime(match, '%y%j%H%M%S')
            break
    return original_end_time


def update_skd_times(skd, new_start_time, param=True, sked=True):
    """
    update times in .skd file

    :param skd: skd file
    :param new_start_time: new start time
    :param param: update $PARAM block (default = True)
    :param sked: update $SKED block (default = True)
    :return:
    """
    # first step: find original start time
    original_start_time = find_start_time(skd)

    # some helper flags
    start_changed = False
    end_changed = False
    sked_block = False

    # helper function that updates time in a string and returns this updated string
    def _update_time(regex, line):
        """
        helper funciton that changes time in string

        :param regex: regex (where first group is time that should be changed)
        :param line: string with time to be changed
        :return: string with updated time
        """
        match = regex.search(line)
        idx = match.regs[1]
        tmp_old_time = datetime.datetime.strptime(match.group(1), '%y%j%H%M%S')
        dt = (tmp_old_time - original_start_time).total_seconds()
        tmp_new_time = new_start_time + datetime.timedelta(seconds=dt)
        time_str = datetime.datetime.strftime(tmp_new_time, '%y%j%H%M%S')
        return line[:idx[0]] + time_str + line[idx[1]:]

    for idx, l in enumerate(skd):

        if param and not start_changed and REGEX_START.search(l):
            l = _update_time(REGEX_START, l)
            start_changed = True
            skd[idx] = l

        if param and not end_changed and REGEX_END.search(l):
            l = _update_time(REGEX_END, l)
            end_changed = True
            skd[idx] = l

        if l.strip().startswith("$"):
            if l.startswith("$SKED"):
                sked_block = True
            else:
                sked_block = False

        if sked and sked_block and REGEX_SKED.search(l):
            l = _update_time(REGEX_SKED, l)
            skd[idx] = l
    pass


def initialize_logging(severity_console="INFO", file=False, severity_file="DEBUG", outdir="logs", mode='w'):
    """
    initialize logging environment

    in case level_str cannot be interpreted it will default to "DEBUG"
    log file will be named: yyyy_mm_dd_hh_mm_ss.log

    :param severity_console: level [DEBUG, INFO, WARNING, ERROR, CRITICAL]
    :param file: write log to file (default = False)
    :param severity_file: level [DEBUG, INFO, WARNING, ERROR, CRITICAL]
    :param outdir: directory where logs will be stored
    :param mode: log file open mode
    :return: None
    """

    c_level_str = severity_console.lower()
    f_level_str = severity_file.lower()

    levels = {"debug": logging.DEBUG,
              "info": logging.INFO,
              "warning": logging.WARNING,
              "error": logging.ERROR,
              "critical": logging.CRITICAL,
              }

    def log_str2level(str):
        if str in levels:
            level = levels[str]
        else:
            level = logging.DEBUG
        return level

    c_level = log_str2level(c_level_str)
    f_level = log_str2level(f_level_str)

    today = str(datetime.datetime.now())

    logger.setLevel(min(c_level, f_level))

    formatter = logging.Formatter('[%(asctime)s]  [%(levelname)s] [%(module)s] %(message)s')

    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(c_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info(f"logging enabled (severity {c_level_str}+)")

    # create file handler
    if file:
        out = Path(outdir) / f"{today}.log"
        out.parent.mkdir(exist_ok=True, parents=True)
        fh = logging.FileHandler(out, mode=mode)
        fh.setLevel(f_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info(f"logs will be written to {out.absolute()} (severity: {f_level_str}+)")
