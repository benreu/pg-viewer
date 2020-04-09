# sql_window.py
#
# Copyright (C) 2019 - reuben
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

from gi.repository import Gtk, GtkSource, GObject, Gdk
from widgets import SetupSourceView
import constants

UI_FILE = "src/sql_window.ui"

class SQLWindowGUI :
	def __init__(self, db):
		
		self.builder = Gtk.Builder()
		GObject.type_register(GtkSource.View)
		self.builder.add_from_file(UI_FILE)
		self.builder.connect_signals(self)
		self.db = db

		source_view = self.builder.get_object('gtksourceview1')
		SetupSourceView (source_view)
		self.source_buffer = source_view.get_buffer()

		self.window = self.builder.get_object('window1')
		self.window.show_all()

		self.sqlite_cursor = constants.sqlite_cursor
		self.sqlite_cursor.execute("SELECT command FROM sql_commands "
									"WHERE current = 'true'")
		for row in self.sqlite_cursor.fetchall():
			self.source_buffer.set_text(row[0])
		self.populate_sql_commands()
		

	def sql_combo_changed (self, combobox):
		if self.builder.get_object('comboboxtext-entry').has_focus():
			return #user is typing new values
		name = combobox.get_active_text()
		self.sqlite_cursor.execute("SELECT command FROM sql_commands "
									"WHERE descriptor = ?", (name,))
		for row in self.sqlite_cursor.fetchall():
			command = row[0]
			self.source_buffer.set_text(command)

	def sql_combo_populate_popup (self, combo, menu):
		separator = Gtk.SeparatorMenuItem()
		separator.show()
		menu.prepend(separator)
		save = Gtk.MenuItem.new_with_mnemonic("_Delete")
		save.show()
		save.connect("activate", self.delete_activated)
		menu.prepend(save)

	def populate_sql_commands (self):
		combo = self.builder.get_object('comboboxtext1')
		combo.remove_all()
		self.sqlite_cursor.execute("SELECT descriptor FROM sql_commands "
									"WHERE current IS NOT 'true' "
									"ORDER BY descriptor")
		for row in self.sqlite_cursor.fetchall():
			combo.append(row[0], row[0])

	def delete_activated (self, menuitem):
		name = self.builder.get_object('comboboxtext-entry').get_text()
		self.sqlite_cursor.execute("DELETE FROM sql_commands "
									"WHERE descriptor = ?", (name,))
		self.populate_sql_commands()

	def save_clicked (self, button):
		name = self.builder.get_object('comboboxtext-entry').get_text()
		if name == '':
			return
		start = self.source_buffer.get_start_iter()
		end = self.source_buffer.get_end_iter()
		command = self.source_buffer.get_text(start, end, True)
		self.sqlite_cursor.execute("INSERT OR REPLACE INTO sql_commands "
									"(descriptor, command, current) "
									"VALUES (?, ?, 'false') ", 
									(name, command))
		self.populate_sql_commands()

	def run_sql_clicked (self, button):
		treeview = self.builder.get_object('treeview1')
		for column in treeview.get_columns():
			treeview.remove_column(column)
		start_iter = self.source_buffer.get_start_iter ()
		end_iter = self.source_buffer.get_end_iter ()
		string = self.source_buffer.get_text(start_iter, end_iter, True)
		cursor = self.db.cursor()
		try:
			cursor.execute(string)
		except Exception as e:
			self.builder.get_object('sql_error_buffer').set_text(str(e))
			self.builder.get_object('textview2').set_visible(True)
			self.builder.get_object('scrolledwindow2').set_visible(False)
			self.db.rollback()
			return
		#create treeview columns and a liststore to store the info
		if cursor.description == None: #probably an UPDATE, report rows affected
			result = "%s row(s) affected" % cursor.rowcount
			self.builder.get_object('sql_error_buffer').set_text(result)
			self.builder.get_object('textview2').set_visible(True)
			self.builder.get_object('scrolledwindow2').set_visible(False)
			self.db.rollback()
			return
		self.builder.get_object('textview2').set_visible(False)
		self.builder.get_object('scrolledwindow2').set_visible(True)
		type_list = list()
		for index, row in enumerate(cursor.description):
			column_name = row.name
			type_ = row.type_code
			if type_ == 23:
				type_list.append(int)
				renderer = Gtk.CellRendererText()
				column = Gtk.TreeViewColumn(column_name, renderer, text=index)
				treeview.append_column(column)
				column.set_sort_column_id(index)
			elif type_ == 16:
				type_list.append(bool)
				renderer = Gtk.CellRendererToggle()
				column = Gtk.TreeViewColumn(column_name, renderer, active=index)
				treeview.append_column(column)
				column.set_sort_column_id(index)
			else:
				type_list.append(str)
				renderer = Gtk.CellRendererText()
				column = Gtk.TreeViewColumn(column_name, renderer, text=index)
				treeview.append_column(column)
				column.set_sort_column_id(index)
		store = Gtk.ListStore()
		store.set_column_types(type_list)
		treeview.set_model(store)
		for row in cursor.fetchall():
			# do a convert, cell by cell, to make sure types are correct
			store_row = list()
			for index, element in enumerate(row):
				store_row.append(type_list[index](element or 0))
			store.append (store_row)
		self.db.rollback()
		cursor.close()
		self.save_current_sql(string)

	def save_current_sql(self, command):
		self.sqlite_cursor.execute("UPDATE sql_commands SET command = ? "
									"WHERE current = 'true';"
									"SELECT command FROM sql_commands "
									"WHERE current = 'true'", (command,))
		if self.sqlite_cursor.fetchone() == None:
			self.sqlite_cursor.execute("INSERT INTO sql_commands "
							"(descriptor, command, current) VALUES "
							"('Current', ?, 'true')", (command,))
		

	
