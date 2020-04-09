# pg_viewer.py
# Copyright (C) 2019 Reuben Rissler <pygtk.posting@gmail.com>
# 
# pg_viewer is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# pg_viewer is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, Gdk, GLib
import sys, psycopg2, logging, traceback
import servers, table_view


UI_FILE = "src/pg_viewer.ui"

class PGViewerGUI (Gtk.Builder):
	widget = None
	def __init__(self):

		Gtk.Builder.__init__(self)
		self.add_from_file(UI_FILE)
		self.connect_signals(self)
		image = self.get_object('menu_image')
		self.get_object('menu_button').set_image(image)
		self.window = self.get_object('window')
		self.window.show_all()
		self.spinner = self.get_object('spinner')
		sys.excepthook = self.exception_handler
		self.server_gui = servers.ServersGUI(self)
		self.server_gui.load_servers()
		self.logger = logging.getLogger("PG Viewer")
		c_handler = logging.StreamHandler()
		c_handler.setLevel(logging.WARNING)
		f_handler = logging.FileHandler('file.log')
		f_handler.setLevel(logging.DEBUG)
		c_handler.setFormatter(logging.Formatter('%(message)s'))
		f_handler.setFormatter(logging.Formatter('%(message)s'))
		self.logger.addHandler(c_handler)
		self.logger.addHandler(f_handler)

	def clear_and_close_clicked (self, button):
		self.get_object('tb_buffer').set_text('')
		self.get_object('tb_window').hide()

	def close_clicked (self, button):
		self.get_object('tb_window').hide()

	def exception_handler (self, type_, value, tb):
		"Catch uncaught exceptions and show them with Glib's idle_add"
		GLib.idle_add(self.show_traceback, type_, value, tb)
	
	def show_traceback (self, type_, value, tb):
		buf = self.get_object('tb_buffer')
		for text in traceback.format_exception(type_, value, tb):
			buf.insert(buf.get_end_iter(), text)
			self.logger.error(text.strip("\n"))
		window = self.get_object('tb_window')
		window.show_all()
		window.present()
	
	def traceback_viewer_clicked (self, button):
		self.get_object('menu_popover').popdown()
		window = self.get_object('tb_window')
		window.present()

	def traceback_viewer_delete_event (self, window, event):
		window.hide()
		return True

	def set_highlight (self, widget, table = False, conn = None):
		if table:
			self.get_object('view_table_button').set_sensitive(True)
			self.schema_table_name = table
			self.conn = conn
		else:
			self.get_object('view_table_button').set_sensitive(False)
		if self.widget: # set widget background to normal
			self.widget.override_background_color(Gtk.StateFlags.NORMAL, None)
		widget.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1,1,1))
		self.widget = widget

	def view_table_clicked (self, button):
		table_view.View(self.conn, self.schema_table_name)

	def servers_clicked (self, button):
		self.server_gui.show_servers_dialog()

	def on_window_destroy(self, window):
		Gtk.main_quit()

	def about_clicked (self, button):
		self.get_object('menu_popover').popdown()
		import about
		about.show_about_dialog (self.window)

