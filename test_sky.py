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

def test_rotate_sky():
    from sky import rotate_sky, REGEX_SOURCE
    from pathlib import Path
    import datetime
    from astropy.time import Time
    from util import find_start_time

    # read original skd file and get start GMST
    file = Path('test/vt1176.skd')
    skd = []
    with open(file) as f:
        skd = f.readlines()
    start = find_start_time(skd)
    gmst = Time(start, scale='utc').sidereal_time('mean', 'greenwich')

    source_block = False
    orig_hms = None
    for l in skd:
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
            break

    # generate new skd file
    for month in range(1, 13):
        rotate_sky(file, datetime.datetime(2021, month, 22, 18, 0, 0))
        new_file = file.parent / (file.stem + "_sky.skd")
        assert new_file.is_file()

        # read new skd file and get start GMST
        new_skd = []
        with open(new_file) as f:
            new_skd = f.readlines()
        new_start = find_start_time(new_skd)
        new_gmst = Time(new_start, scale='utc').sidereal_time('mean', 'greenwich')

        new_hms = None
        for l in new_skd:
            if l.strip().startswith("$"):
                if l.startswith("$SOURCE"):
                    source_block = True
                else:
                    source_block = False

            if source_block and REGEX_SOURCE.search(l):
                match = REGEX_SOURCE.search(l)
                # get hour minute second of right ascension
                new_hour_grp = match.regs[1]
                new_hour = float(l[new_hour_grp[0]:new_hour_grp[1]])
                new_minute_grp = match.regs[2]
                new_minute = float(l[new_minute_grp[0]:new_minute_grp[1]])
                new_second_grp = match.regs[3]
                new_second = float(l[new_second_grp[0]:new_second_grp[1]])

                new_hms = new_hour + new_minute / 60 + new_second / 3600
                break

        # get difference in gmst
        diff_sidereal_time = (gmst - new_gmst).value

        # get difference in gmst
        diff_ra = orig_hms - new_hms

        diff = (diff_sidereal_time - diff_ra) % 24

        # angle below one minute or above 23h 59min
        assert abs(diff) * 3600 < 60 or abs(diff) * 3600 > 23 * 3600 - 60
