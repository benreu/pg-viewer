# table_view.py
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


from gi.repository import Gtk, GLib, Pango
import re

UI_FILE = "src/table_view.ui"

class View (Gtk.Builder):
	edit_path = -1
	edited = False
	edit_row_id = -1
	sort_sql = None
	def __init__ (self, conn, schema_table_name):

		Gtk.Builder.__init__(self)
		self.add_from_file(UI_FILE)
		self.connect_signals(self)
		
		self.conn = conn
		self.schema_table_name = schema_table_name
		self.window = self.get_object("main_window")
		self.window.set_title(self.schema_table_name)
		p = self.conn.get_dsn_parameters()
		subtitle = " / ".join([p['host'], p['dbname'], self.schema_table_name])
		self.get_object("header").set_subtitle(subtitle)
		self.treeview = self.get_object("view_treeview")
		self.edit_box = self.get_object("edit_box")
		self.combo_model = Gtk.ListStore(str)
		self.combo_model.append(["true"])
		self.combo_model.append(["false"])
		self.combo_model.append([None])
		self.sort_sql = ''
		GLib.idle_add(self.load_table_data )
		self.window.show_all()

	def load_table_data (self):
		for column in self.treeview.get_columns():
			self.treeview.remove_column(column)
		c = self.conn.cursor()
		c.execute("SELECT  "
						"pg_attribute.attname, atttypid::regtype " 
					"FROM pg_index, pg_class, pg_attribute, pg_namespace "
					"WHERE "
						"pg_class.oid = %s::regclass AND " 
						"indrelid = pg_class.oid AND "
						"pg_class.relnamespace = pg_namespace.oid AND " 
						"pg_attribute.attrelid = pg_class.oid AND "
						"pg_attribute.attnum = any(pg_index.indkey) "
						"AND indisprimary", (self.schema_table_name,))
		try:
			result = c.fetchone()
			self.pk_column_name, column_type = result[0], result[1]
			self.editable = True
			if self.sort_sql == '':
				self.sort_sql = " ORDER BY %s::%s" % (self.pk_column_name, column_type)
		except Exception as e:
			self.editable = False
		c.execute("SELECT * FROM %s LIMIT 1" % self.schema_table_name)
		select_sql = "SELECT "
		self.update_sql = "UPDATE %s SET (" % self.schema_table_name
		self.update_index_list = list()
		type_list = list()
		int_sort_list = list()
		self.renderer_list = list()
		for index, row in enumerate(c.description):
			column_name = row.name
			column_view_name = re.sub("_", "__", row.name) # disable mnemonics in the treeviewcolumn
			type_ = row.type_code
			if type_ != 17: # only non-binary data
				self.update_sql += " %s," % column_name 
				self.update_index_list.append(index)
			if self.editable and column_name == self.pk_column_name:
				self.pk_column = index
			type_list.append(str)
			if type_ == 17: #binary data
				renderer = Gtk.CellRendererText()
				self.renderer_list.append(renderer)
				column = Gtk.TreeViewColumn(column_view_name, renderer, text=index)
				self.treeview.append_column(column)
				select_sql += " '<binary data>'," 
			elif type_ == 20 or type_ == 21 or type_ == 23:
				renderer = Gtk.CellRendererText()
				self.renderer_list.append(renderer)
				renderer.set_property('editable', self.editable)
				renderer.connect('edited', self.text_renderer_edited, index)
				column = Gtk.TreeViewColumn(column_view_name, renderer, text=index)
				self.treeview.append_column(column)
				column.set_clickable(True)
				column.connect('clicked', self.column_clicked, column_name, 'integer')
				int_sort_list.append(index)
				select_sql += " CASE WHEN %s::text='' THEN '''''' ELSE %s::text END," % (column_name, column_name)
			elif type_ == 16: #boolean
				renderer = Gtk.CellRendererCombo()
				self.renderer_list.append(renderer)
				renderer.set_property('has-entry', False)
				renderer.set_property('editable', self.editable)
				renderer.set_property('model', self.combo_model)
				renderer.set_property('text-column', 0)
				renderer.connect('changed', self.combo_renderer_changed, index)
				column = Gtk.TreeViewColumn(column_view_name, renderer, text = index)
				self.treeview.append_column(column)
				column.set_clickable(True)
				column.connect('clicked', self.column_clicked, column_name, 'bool')
				select_sql += " CASE WHEN %s::text='' THEN '''''' ELSE %s::text END," % (column_name, column_name)
			else:
				renderer = Gtk.CellRendererText()
				self.renderer_list.append(renderer)
				renderer.set_property('editable', self.editable)
				renderer.connect('edited', self.text_renderer_edited, index)
				column = Gtk.TreeViewColumn(column_view_name, renderer, text = index)
				self.treeview.append_column(column)
				column.set_clickable(True)
				column.connect('clicked', self.column_clicked, column_name, 'text')
				select_sql += " CASE WHEN %s::text='' THEN '''''' ELSE %s::text END," % (column_name, column_name)
			column.set_reorderable(True)
			column.set_resizable(True)
			column.set_fixed_width(100)
		select_sql = select_sql[:-1] + " FROM %s" % self.schema_table_name
		self.update_sql = self.update_sql[:-1] + ") = " # remove trailing comma and add paren
		self.select_sql = select_sql
		self.store = Gtk.ListStore ()
		self.store.set_column_types(type_list)
		num_rows = 0
		c.execute(select_sql + self.sort_sql)
		for row in c.fetchall():
			num_rows += 1
			self.store.append (row)
		c.close()
		self.treeview.set_model(self.store)
		if self.editable == False:
			self.show_message ("No Primary Key for this table!\n"
								"This table will not be editable.")
		elif num_rows != 0:
			self.edit_row_id = self.store[0][self.pk_column]
			self.edit_path = 0
		self.set_renderer_ellipsize()

	def set_renderer_ellipsize (self):
		for renderer in self.renderer_list:
			renderer.set_property('ellipsize', Pango.EllipsizeMode.END)

	def refresh_clicked (self, button):
		self.load_table_data()

	def column_clicked (self, column, column_name, column_type):
		store = self.get_object("sort_order_store")
		for path, row in enumerate(store):
			if row[0] == column_name:
				iter_ = store.get_iter(path)
				store.remove(iter_)
		store.append([column_name, column_type, 'ASC'])
		window = self.get_object("sort_window")
		window.show_all()
		window.present()

	def sort_by_window_delete (self, window, event):
		window.hide()
		return True

	def revert_current_row (self, widget = None):
		model, path = self.get_object('view_selection').get_selected_rows()
		if path == []:
			return
		c = self.conn.cursor()
		row_id = model[path][0]
		c.execute("SELECT * FROM %s WHERE id = '%s'" % (self.schema_table_name, row_id))
		row = (str(col) if col is not None else None for col in c.fetchone())
		for column, value in enumerate(row):
			model[path][column] = value
		self.edit_box.set_sensitive(False)
		c.close()
		self.edited = False

	def save_current_row (self, widget = None):
		update_values = "("
		for column in self.update_index_list:
			value = self.store[self.edit_path][column]
			if value == None:
				value = "NULL"
			elif value != "''":
				value = "'%s'" % value
			update_values += " %s," % value
		update_values = update_values[:-1] + ")" # remove trailing comma and add parenthese
		where = " WHERE %s = '%s'" % (self.pk_column_name, self.edit_row_id)
		c = self.conn.cursor()
		try:
			c.execute(self.update_sql + update_values + where)
		except Exception as e:
			self.conn.rollback()
			self.show_message(str(e))
		self.edit_box.set_sensitive(False)
		self.edited = False

	def selection_changed (self, selection):
		model, path = selection.get_selected_rows()
		if path == []:
			return
		if self.edited == True:
			self.save_current_row()
		if self.editable:
			self.edit_row_id = model[path][self.pk_column]

	def combo_renderer_changed (self, renderer, path, _iter, index):
		self.store[path][index] = self.combo_model[_iter][0]
		self.edit_path = path
		self.edit_box.set_sensitive(True)
		self.edited = True

	def text_renderer_edited (self, renderer, path, text, index):
		if text == '':
			text = None
		self.store[path][index] = text
		self.edit_path = path
		self.edit_box.set_sensitive(True)
		self.edited = True

	def optimize_column_widths_clicked (self, button):
		for renderer in self.renderer_list:
			renderer.set_property('ellipsize', Pango.EllipsizeMode.NONE)
		treeview = self.get_object("view_treeview")
		for index, column in enumerate(treeview.get_columns()):
			column.set_fixed_width(-1)
			column.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
			column.set_resizable(True)

	def delete_clicked (self, button):
		selection = self.get_object("sort_order_selection")
		model, path = selection.get_selected_rows()
		if path == []:
			return
		model.remove(model.get_iter(path))

	def reload_using_sort_clicked (self, button):
		self.sort_sql = " ORDER BY"
		for row in self.get_object("sort_order_store"):
			self.sort_sql += " %s::%s %s," % (row[0], row[1], row[2])
		if self.sort_sql == " ORDER BY":
			self.sort_sql = ''
		self.sort_sql = self.sort_sql[:-1] # remove trailing comma
		self.load_table_data ()

	def sort_type_changed (self, cellrenderercombo, path, treeiter):
		model = cellrenderercombo.get_property('model')
		sort_type = model[treeiter][0]
		self.get_object("sort_order_store")[path][2] = sort_type

	def clear_all_clicked (self, button):
		self.get_object("sort_order_store").clear()

	def show_message (self, message):
		dialog = Gtk.MessageDialog( self.window,
									0,
									Gtk.MessageType.ERROR,
									Gtk.ButtonsType.CLOSE,
									message)
		dialog.run()
		dialog.destroy()



		