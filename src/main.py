#!/usr/bin/python3
# main.py
#
# Copyright (C) 2019 - house
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import gi
gi.require_version('GtkSource', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os, sys
import pg_viewer


def main():
	import constants
	constants.get_apsw_cursor()
	app = pg_viewer.PGViewerGUI()
	Gtk.main()
		
if __name__ == "__main__":
	sys.exit(main())
