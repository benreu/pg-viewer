# constants.py
#
# Copyright (C) 2019 - Reuben
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os, apsw

sqlite_cursor = None

home = os.path.expanduser('~')
preferences_path = os.path.join(home, '.pg_viewer')
if not os.path.exists(preferences_path):
	os.mkdir(preferences_path)
def get_apsw_cursor ():
	global sqlite_cursor
	apsw_file = os.path.join(preferences_path, 'pg_viewer_data')
	if not os.path.exists(apsw_file):
		con = apsw.Connection(apsw_file)
		sqlite_cursor = con.cursor()
		sqlite_cursor.execute("CREATE TABLE sql_commands "
								"(descriptor text UNIQUE NOT NULL, "
								"command text NOT NULL, "
								"current boolean NOT NULL)")
	else:
		con = apsw.Connection(apsw_file)
		sqlite_cursor = con.cursor()
	return sqlite_cursor

	