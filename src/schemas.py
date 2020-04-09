# schemas.py
#
# Copyright (C) 2019 - house
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
import functions, sequences, tables, views

class Schemas :
	def __init__ (self, main, conn, parent_box):

		self.main = main
		self.conn = conn
		self.schema_store = Gtk.ListStore(str, str)
		count = 0 
		label = Gtk.Label(halign = Gtk.Align.START)
		parent_box.pack_start(label, False, False, 0)
		c = conn.cursor()
		c.execute("SELECT schema_name "
					"FROM information_schema.schemata "
					"WHERE schema_name NOT LIKE 'pg_toast%' "
					"AND schema_name NOT LIKE 'pg_temp%' "
					"AND schema_name NOT LIKE 'pg_catalog' "
					"AND schema_name NOT LIKE 'information_schema' "
					"ORDER BY schema_name")
		for row in c.fetchall():
			schema_name = row[0]
			self.schema_store.append([schema_name, schema_name])
			count += 1
			toggle = Gtk.CheckButton(label = schema_name, halign = Gtk.Align.START)
			parent_box.pack_start(toggle, False, False, 0)
			revealer = Gtk.Revealer()
			parent_box.pack_start(revealer, False, False, 0)
			box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
			box.set_margin_start(10)
			revealer.add(box)
			menu = self.create_menu(schema_name, box)
			toggle.connect('toggled', self.toggled, revealer, box, schema_name)
			toggle.connect('button-release-event', self.button, menu)
		c.close()
		label.set_label("Schemas (%d)" % count)
		parent_box.show_all()

	def create_menu(self, schema_name, box):
		menu = Gtk.Menu()
		populate_menu = Gtk.MenuItem("Refresh")
		populate_menu.connect('activate', self.refresh, schema_name, box)
		menu.append(populate_menu)
		divider = Gtk.SeparatorMenuItem()
		menu.append(divider)
		create_table_menu = Gtk.MenuItem("Create Table")
		create_table_menu.connect('activate', self.create_table, schema_name)
		menu.append(create_table_menu)
		menu.show_all()
		return menu

	def create_table(self, menuitem, schema_name):
		import table_tool_new
		table_tool_new.TableNewGUI(self.main, self.conn, schema_name, self.schema_store)

	def button (self, toggle, event, menu):
		self.main.set_highlight(toggle)
		if event.button == 3:
			menu.popup_at_pointer()

	def refresh (self, menuitem, schema_name, box):
		self.populate(box, schema_name)

	def toggled (self, toggle, revealer, box, schema_name):
		active = toggle.get_active()
		revealer.set_reveal_child(active)
		schemas = len(revealer.get_child().get_children())
		if active == True and schemas < 1:
			self.populate(box, schema_name)
			populated = True

	def populate (self, box, schema_name):
		for child in box.get_children():
			box.remove(child)
		functions.Functions(self.main, self.conn, box, schema_name, self.schema_store)
		sequences.Sequences (self.main, self.conn, box, schema_name)
		tables.Tables (self.main, self.conn, box, schema_name, self.schema_store)
		views.Views(self.main, self.conn, box, schema_name, self.schema_store)



