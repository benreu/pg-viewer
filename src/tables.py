# tables.py
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

from gi.repository import Gtk, Gdk
import table_view, columns, table_tool_edit


class Tables :
	def __init__ (self, main, conn, parent_box, schema_name, schema_store):

		self.main = main
		self.conn = conn
		self.schema_store = schema_store
		count = 0 
		revealer = Gtk.Revealer()
		checkbutton = Gtk.CheckButton(halign = Gtk.Align.START)
		checkbutton.connect('toggled', self.show_tables, revealer)
		parent_box.pack_start(checkbutton, False, False, 0)
		parent_box.pack_start(revealer, False, False, 0)
		box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
		box.set_margin_start(10)
		revealer.add(box)
		c = conn.cursor()
		c.execute("SELECT tablename FROM pg_tables "
					"WHERE schemaname = %s "
					"ORDER BY tablename;", (schema_name,))
		for row in c.fetchall():
			table_name = row[0]
			schema_table_name = "%s.%s" % (schema_name, table_name)
			count += 1
			toggle = Gtk.CheckButton(label = table_name, halign = Gtk.Align.START)
			box.pack_start(toggle, False, False, 0)
			revealer = Gtk.Revealer()
			box.pack_start(revealer, False, False, 0)
			child_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
			child_box.set_margin_start(10)
			revealer.add(child_box)
			menu = Gtk.Menu()
			populate_menu = Gtk.MenuItem("Refresh")
			populate_menu.connect('activate', self.refresh, schema_table_name, child_box)
			menu.append(populate_menu)
			properties_menu = Gtk.MenuItem("Properties")
			properties_menu.connect('activate', self.table_properties, schema_name, table_name)
			menu.append(properties_menu)
			view_menu = Gtk.MenuItem("View")
			view_menu.connect('activate', self.view, schema_table_name)
			menu.append(view_menu)
			menu.show_all()
			toggle.connect('toggled', self.toggled, revealer, child_box, schema_name, table_name)
			toggle.connect('button-release-event', self.button, menu, schema_table_name)
		c.close()
		checkbutton.set_label("Tables (%d)" % count)
		parent_box.show_all()

	def table_properties (self, menu, schema_name, table_name):
		table_tool_edit.TableEditGUI(self.main, self.conn, schema_name, table_name, self.schema_store)

	def show_tables (self, toggle, revealer):
		self.main.set_highlight(toggle)
		revealer.set_reveal_child(toggle.get_active())

	def button (self, toggle, event, menu, schema_table_name):
		self.main.set_highlight(toggle, schema_table_name, self.conn)
		if event.button == 3:
			menu.popup_at_pointer()
		elif event.button == 2:
			table_view.View(self.conn, schema_table_name)

	def refresh (self, menuitem, table_name, box):
		self.populate(box, schema_name)

	def view (self, menuitem, schema_table_name):
		table_view.View(self.conn, schema_table_name)

	def toggled (self, toggle, revealer, box, schema_name, table_name):
		active = toggle.get_active()
		revealer.set_reveal_child(active)
		tables = len(revealer.get_child().get_children())
		if active == True and tables < 1:
			self.populate(box, schema_name, table_name)

	def populate (self, box, schema_name, table_name):
		for child in box.get_children():
			box.remove(child)
		columns.Populate (self.main, self.conn, box, schema_name, table_name)


