# table_tool_new.py
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

class TableNewGUI :
	def __init__ (self, main, conn, schema_name, schema_store):

		self.main = main
		self.conn = conn
		self.schema_name = schema_name
		self.table_name = None
		self.builder = Gtk.Builder()
		GObject.type_register(GtkSource.View)
		self.builder.add_from_file(UI_FILE)
		self.builder.connect_signals(self)
		SetupSourceView (self.builder.get_object('sql_textview'))
		schema_combo = self.builder.get_object('schema_combo')
		schema_combo.set_model(schema_store)
		schema_combo.set_active_id(schema_name)
		self.populate_tables()
		self.window = self.builder.get_object('table_tool_window')
		self.window.set_title('New Table')
		self.window.show_all()
		self.builder.get_object('like_table_box').set_visible(True)

	def generate_sql (self, widget = None):
		"This signal gets hooked up to all widgets that control sql generation"
		if self.builder.get_object('read_only_toggle').get_active() == False:
			if not self.ask_for_overwrite():
				return
		sql_buffer = self.builder.get_object('sql_textview').get_buffer()
		sql_buffer.set_text('')
		button = self.builder.get_object('ok_button')
		button.set_sensitive(False)
		schema = self.builder.get_object('schema_entry').get_text()
		table_name = self.builder.get_object('table_name_entry').get_text()
		if table_name == '':
			button.set_label("No table name")
			return
		sql = "CREATE TABLE %s.%s\n(" % (schema, table_name)
		store = self.builder.get_object('columns_store')
		columns_added = False
		for row in store:
			col_name = row[0]
			col_type = row[1]
			if row[2]: # NOT NULL column
				sql += "\n %s %s NOT NULL," % (col_name, col_type)
			else:
				sql += "\n %s %s," % (col_name, col_type)
			columns_added = True
		if columns_added:
			sql = sql[:-1] #remove unneeded trailing comma
		sql += "\n);\n"
		buf = self.builder.get_object('comment_buffer')
		comment = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
		if comment != '':
			sql += "COMMENT ON TABLE %s.%s \n    IS '%s';" % (schema, table_name, comment)
		sql_buffer.set_text(sql)
		button.set_sensitive(True)
		button.set_label("Ok")
		self.window.set_title("Table %s.%s" % (schema, table_name))

	def populate_tables(self):
		store = self.builder.get_object('like_table_store')
		store.clear()
		c = self.conn.cursor()
		c.execute(	"SELECT schemaname, tablename FROM pg_tables "
					"ORDER BY schemaname, tablename")
		for row in c.fetchall():
			store.append(row)
		c.close()

	def remove_column_clicked (self, button):
		selection = self.builder.get_object('column_selection')
		model, path = selection.get_selected_rows()
		if path == []:
			return
		model.remove(model.get_iter(path))

	def add_column_clicked (self, button):
		store = self.builder.get_object('columns_store')
		store.append(["new_column", "text", False])

	def column_name_edited (self, cellrenderertext, path, text):
		store = self.builder.get_object('columns_store')
		store[path][0] = text
		self.generate_sql()

	def column_type_changed (self, combo, path, treeiter):
		col_type = self.builder.get_object('type_store')[treeiter][0]
		store = self.builder.get_object('columns_store')
		store[path][1] = col_type
		self.generate_sql ()

	def column_not_null_toggled (self, cellrenderertoggle, path):
		store = self.builder.get_object('columns_store')
		store[path][2] = not store[path][2]
		self.generate_sql ()

	def cancel_clicked (self, button):
		self.window.destroy()

	def read_only_toggled (self, toggle):
		editable = not toggle.get_active()
		self.builder.get_object('sql_textview').set_editable(editable)

	def ok_clicked (self, button):
		buf = self.builder.get_object('sql_textview').get_buffer()
		sql = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
		c = self.conn.cursor()
		try:
			c.execute(sql)
		except Exception as e:
			self.conn.rollback()
			self.show_error (str(e))
		c.close()
		self.window.destroy()

	def ask_for_overwrite(self):
		label = Gtk.Label("Do you want to overwrite your SQL changes?")
		dialog = Gtk.Dialog("Confirmation required", 
								self.window,
								Gtk.DialogFlags.USE_HEADER_BAR,
								("Cancel", Gtk.ResponseType.CANCEL,
								"Overwrite", Gtk.ResponseType.ACCEPT))
		dialog.get_content_area().add(label)
		label.show()
		result = dialog.run()
		dialog.destroy()
		if result == Gtk.ResponseType.ACCEPT:
			self.builder.get_object('sql_textview').set_editable(False)
			self.builder.get_object('read_only_toggle').set_active(True)
			return True
		return False

	def show_error (self, error):
		dialog = Gtk.MessageDialog( self.window,
									0,
									Gtk.MessageType.ERROR,
									Gtk.ButtonsType.CLOSE,
									error)
		dialog.run()
		dialog.destroy()
	
