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

def test_rotate_schedule():
    from rotate import rotate_schedule
    from pathlib import Path
    import datetime

    file = Path('test/vo1189.skd')

    # generate new skd file
    for month in range(1, 13):
        rotate_schedule(file, datetime.datetime(2021, month, 22, 18, 0, 0))
        new_file = file.parent / (file.stem + "_rot.skd")
        assert new_file.is_file()


def test_rotate_schedule_2():
    from rotate import rotate_schedule, SessionTooShortException
    from pathlib import Path
    import datetime
    import pytest

    file = Path('test/vt1176.skd')
    with pytest.raises(SessionTooShortException):
        rotate_schedule(file, datetime.datetime(2021, 1, 22, 18, 0, 0))
