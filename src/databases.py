# databases.py
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
import psycopg2
import schemas, sql_window

class Database:
	def __init__ (self, server_obj, main, parent_box):

		self.main = main
		count = 0 
		label = Gtk.Label(halign = Gtk.Align.START)
		parent_box.pack_start(label, False, False, 0)
		c = server_obj.conn.cursor()
		c.execute("SELECT b.datname FROM pg_catalog.pg_database b "
					"WHERE b.datname != 'template0' "
					"AND b.datname != 'template1' "
					"ORDER BY b.datname;")
		for row in c.fetchall():
			name = row[0]
			conn = psycopg2.connect(database = name, 
									host = server_obj.host, 
									port = server_obj.port, 
									user = server_obj.user, 
									password = server_obj.password)
			count += 1
			toggle = Gtk.CheckButton(label = name, halign = Gtk.Align.START)
			parent_box.pack_start(toggle, False, False, 0)
			revealer = Gtk.Revealer()
			parent_box.pack_start(revealer, False, False, 0)
			box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
			box.set_margin_start(10)
			revealer.add(box)
			menu = Gtk.Menu()
			populate_menu = Gtk.MenuItem("Refresh")
			populate_menu.connect('activate', self.refresh, conn, box)
			menu.append(populate_menu)
			sql_menu = Gtk.MenuItem("SQL Window")
			sql_menu.connect('activate', self.sql_window, conn, box)
			menu.append(sql_menu)
			menu.show_all()
			toggle.connect('toggled', self.toggled, revealer, conn, box)
			toggle.connect('button-release-event', self.button, menu)
		c.close()
		label.set_label("Databases (%d)" % count)
		parent_box.show_all()

	def button (self, toggle, event, menu):
		self.main.set_highlight(toggle)
		if event.button == 3:
			menu.popup_at_pointer()

	def sql_window (self, menuitem, conn, box):
		sql_window.SQLWindowGUI(conn)

	def refresh (self, menuitem, conn, box):
		self.populate(conn, box)

	def toggled (self, toggle, revealer, conn, box):
		active = toggle.get_active()
		revealer.set_reveal_child(active)
		databases = len(revealer.get_child().get_children())
		if active == True and databases < 1:
			self.populate(conn, box)
			populated = True

	def populate (self, conn, box):
		for child in box.get_children():
			box.remove(child)
		schemas.Schemas (self.main, conn, box)




