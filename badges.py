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

import re

import anybadge


def coverage(path):
    r = re.compile(r"^TOTAL.+?(\d+%)$")

    with open(path) as f:
        for l in f:
            if r.search(l):
                res = r.match(l)
                cov = res.groups(1)[0]
                anybadge.Badge(label='coverage', value=cov, default_color='green', num_padding_chars=1) \
                    .write_badge("coverage.svg", overwrite=True)
                break

    anybadge.Badge(label="Developed at", value="SPACE@ETH", default_color="black") \
        .write_badge("developed.svg", overwrite=True)
    anybadge.Badge(label="License", value="GNU", default_color="purple").write_badge("license.svg", overwrite=True)
    anybadge.Badge(label="Python", value="3.8 | 3.9", default_color="blue").write_badge("python.svg", overwrite=True)


if __name__ == "__main__":
    coverage("report.txt")
