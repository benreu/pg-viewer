# table_tool_edit.py
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


from gi.repository import Gtk, GObject, GtkSource
from widgets import SetupSourceView

UI_FILE = "src/table_tool_window.ui"

class TableEditGUI :
	def __init__ (self, main, conn, schema_name, table_name, schema_store):

		self.main = main
		self.conn = conn
		self.schema_name = schema_name
		self.table_name = table_name
		self.builder = Gtk.Builder()
		GObject.type_register(GtkSource.View)
		self.builder.add_from_file(UI_FILE)
		self.builder.connect_signals(self)
		SetupSourceView (self.builder.get_object('sql_textview'))
		schema_combo = self.builder.get_object('schema_combo')
		schema_combo.set_model(schema_store)
		schema_combo.set_active_id(schema_name)
		self.builder.get_object('table_name_entry').set_text(table_name)
		self.populate_columns(schema_name, table_name)
		self.window = self.builder.get_object('table_tool_window')
		self.window.show_all()
		self.window.set_title("Table %s.%s" % (schema_name, table_name))

	def populate_columns (self, schema_name, table_name):
		store = self.builder.get_object('columns_store')
		store.clear()
		c = self.conn.cursor()
		c.execute(	"SELECT column_name, data_type, (is_nullable = 'NO') "
					"FROM information_schema.columns "
						"WHERE table_schema = %s "
						"AND table_name = %s", (schema_name, table_name))
		for row in c.fetchall():
			store.append(row)
		c.close()

	def remove_column_clicked (self, button):
		selection = self.builder.get_object('column_selection')
		model, path = selection.get_selection()
		if path == []:
			return
		column_name = model[path][0]
		self.builder.get_object('delete_label').set_label(column_name)
		dialog = self.builder.get_object('delete_column_dialog')
		result = dialog.run()
		dialog.hide()
		if result != Gtk.ResponseType.ACCEPT:
			return
		c = self.conn.cursor()
		try:
			c.execute("ALTER %s.%s DROP COLUMN %s" % (self.schema_name, self.table_name, column_name))
			self.conn.commit()
		except Exception as e:
			self.conn.rollback()
			self.show_message(str(e))
		c.close()
		self.populate_columns()

	def cancel_clicked (self, button):
		self.window.destroy()

	def show_message (self, message):
		dialog = Gtk.MessageDialog( self.window,
									0,
									Gtk.MessageType.ERROR,
									Gtk.ButtonsType.CLOSE,
									message)
		dialog.run()
		dialog.destroy()
	
