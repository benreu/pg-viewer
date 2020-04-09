# servers.py
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

from gi.repository import Gtk, GLib
from multiprocessing import Process
import psycopg2, os, threading
import databases

class Server:
	populated = False
	def __init__ (self, main, parent_box, server, comment):

		self.main = main
		_list = server.split(":") 
		self.host = _list[0]
		self.port = _list[1]
		self.user = _list[3]
		self.password = _list[4]
		toggle = Gtk.CheckButton(label = comment)
		toggle.set_halign(Gtk.Align.START)
		parent_box.pack_start(toggle, False, False, 0)
		revealer = Gtk.Revealer()
		parent_box.pack_start(revealer, False, False, 0)
		self.box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
		self.box.set_margin_start(10)
		revealer.add(self.box)
		toggle.connect('toggled', self.toggled, revealer)
		parent_box.show_all()
		menu = Gtk.Menu()
		populate_menu = Gtk.MenuItem("Refresh")
		populate_menu.connect('activate', self.refresh, server)
		menu.append(populate_menu)
		menu.show_all()
		toggle.connect('button-release-event', self.button_release, menu)

	def refresh (self, menuitem, server):
		self.main.spinner.start()
		if not self.populated:
			t = threading.Thread(target = self.get_connection)
			t.start()
		else:
			self.populate_databases()

	def button_release (self, button, event, menu):
		self.main.set_highlight(button)
		if event.button == 3:
			menu.popup_at_pointer()
			
	def toggled (self, toggle, revealer):
		self.main.set_highlight(toggle)
		active = toggle.get_active()
		revealer.set_reveal_child(active)
		databases = len(revealer.get_child().get_children())
		if active == True and databases < 1:
			self.main.spinner.start()
			t = threading.Thread(target = self.get_connection)
			t.start()

	def get_connection (self):
		try:
			self.conn = psycopg2.connect(	database = 'postgres', 
											host = self.host, 
											user = self.user, 
											password = self.password, 
											port = self.port)
		except psycopg2.OperationalError as e:
			#GLib.idle_add(toggle.set_active, False)
			GLib.idle_add(self.show_error, str(e))
			return
		GLib.idle_add(self.populate_databases)
		self.populated = True

	def populate_databases (self):
		for child in self.box.get_children():
			self.box.remove(child)
		databases.Database (self, self.main, self.box)
		self.box.show_all()
		self.main.spinner.stop()

	def show_error (self, error):
		self.main.spinner.stop()
		dialog = Gtk.MessageDialog( self.main.window,
									0,
									Gtk.MessageType.ERROR,
									Gtk.ButtonsType.CLOSE,
									error)
		dialog.run()
		dialog.destroy()

class ServersGUI(Gtk.Builder):
	def __init__ (self, main):

		Gtk.Builder.__init__(self)
		self.add_from_file("src/servers.ui")
		self.connect_signals(self)
		self.main = main
		self.server_store = self.get_object ('servers_store')
		self.load_servers()
		password_column = self.get_object ('pass_column')
		password_renderer = self.get_object ('pass_renderer')
		password_column.set_cell_data_func(password_renderer, self.password_func)

	def show_servers_dialog(self):
		self.server_store = self.get_object('servers_store')
		dialog = self.get_object('servers_dialog')
		dialog.set_transient_for(self.main.window)
		response = dialog.run()
		dialog.hide()
		string = ''
		for row in self.server_store:
			host = row[0]
			port = row[1]
			user = row[2]
			password = row[3]
			comment = row[4]
			string += "%s:%s:*:%s:%s\n" % (host, port, user, password)
		if response == Gtk.ResponseType.ACCEPT:
			with open (self.pgpass_file, 'w') as f:
				f.write(string)
			self.load_servers()
		elif response == Gtk.ResponseType.OK:
			with open (self.pgpass_file, 'w') as f:
				f.write(string)

	def load_servers (self):
		home = os.path.expanduser('~')
		self.pgpass_file = os.path.join(home, '.pgpass')
		box = self.main.get_object('tree_box')
		for child in box.get_children():
			box.remove(child)
		self.server_store.clear()
		if not os.path.exists(self.pgpass_file):
			dialog = Gtk.MessageDialog(self.main.window,
										0,
										Gtk.MessageType.ERROR,
										Gtk.ButtonsType.CLOSE,
										self.pgpass_file + ' does not exist!')
			dialog.run()
			dialog.destroy()
			return
		with open(self.pgpass_file, 'r') as f:
			for line in f.read().split('\n'):
				if line == '':
					continue
				line = line.split("#")
				server = line[0]
				l = server.split(':')
				if len(line) > 1:
					comment = line[1]
				else:
					comment = l[0]
				Server(self.main, box, server, comment)
				self.server_store.append([l[0], l[1], l[3], l[4], comment])

	def password_func(self, column, cellrenderer, model, iter_, data):
		cellrenderer.set_property("text" , "*******")

	def password_editing_started (self, cellrenderer, editable, path):
		password = self.server_store[path][3]
		editable.set_text(password)

	def new_server_clicked (self, button):
		it = self.server_store.append(["new_host", 
										"5432", 
										"postgres", 
										"password", 
										"comment"])
		selection = self.get_object('server_selection')
		selection.select_iter(it)

	def delete_server_clicked (self, button):
		selection = self.get_object('server_selection')
		model, path = selection.get_selected_rows()
		if path != []:
			model.remove(model.get_iter(path))

	def host_edited (self, cellrenderertext, path, text):
		self.server_store[path][0] = text

	def port_edited (self, cellrenderertext, path, text):
		self.server_store[path][1] = text

	def user_edited (self, cellrenderertext, path, text):
		self.server_store[path][2] = text

	def password_edited (self, cellrenderertext, path, text):
		self.server_store[path][3] = text

	def comment_edited (self, cellrenderertext, path, text):
		self.server_store[path][4] = text



