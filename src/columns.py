# columns.py
#
# Copyright (C) 2018 - house
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

from gi.repository import Gtk
from widgets import ClickableLabel


class Populate ():
	def __init__ (self, main, conn, parent_box, schema_name, table_name):

		self.main = main
		self.conn = conn
		count = 0 
		column_label = Gtk.Label(halign = Gtk.Align.START)
		parent_box.pack_start(column_label, False, False, 0)
		c = conn.cursor()
		c.execute("SELECT column_name "
					"FROM information_schema.columns "
					"WHERE table_schema = %s "
					"AND table_name = %s", (schema_name, table_name))
		for row in c.fetchall():
			column_name = row[0]
			count += 1
			label = ClickableLabel(label = column_name)
			parent_box.pack_start(label, False, False, 0)
			revealer = Gtk.Revealer()
			parent_box.pack_start(revealer, False, False, 0)
			box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
			box.set_margin_start(10)
			revealer.add(box)
			menu = Gtk.Menu()
			populate_menu = Gtk.MenuItem("Properties")
			populate_menu.connect('activate', self.properties, column_name)
			menu.append(populate_menu)
			menu.show_all()
			label.connect('button-release-event', self.button_release, menu)
		c.close()
		column_label.set_label("Columns (%d)" % count)
		parent_box.show_all()

	def properties (self, menuitem, column_name):
		print (column_name)

	def button_release (self, button, event, menu):
		self.main.set_highlight(button)
		if event.button == 3:
			menu.popup_at_pointer()



