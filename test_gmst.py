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


def test_find_time_equal_gmst():
    from astropy.coordinates import Angle
    from astropy.time import Time
    import datetime
    from gmst import find_time_equal_gmst

    for dms in [(12, 0, 0), (6, 45, 0), (6, 43, 0)]:
        angle = Angle(dms, unit='hourangle')
        new_date = find_time_equal_gmst(datetime.date(2021, 1, 1), angle)
        tmp_apy_time = Time(new_date, scale='utc')
        new_angle = tmp_apy_time.sidereal_time('mean', 'greenwich')
        assert (angle - new_angle).value < 1 / 3600


def test_update_based_on_gmst():
    from gmst import update_based_on_gmst
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

    # generate new skd file
    for month in range(1, 13):
        update_based_on_gmst(file, datetime.datetime(2021, month, 22))
        new_file = file.parent / (file.stem + "_gmst.skd")
        assert new_file.is_file()

        # read new skd file and get start GMST
        new_skd = []
        with open(new_file) as f:
            new_skd = f.readlines()
        new_start = find_start_time(new_skd)
        new_gmst = Time(new_start, scale='utc').sidereal_time('mean', 'greenwich')

        # get difference in gmst
        diff = abs((gmst - new_gmst).value) * 3600

        assert diff < 1
