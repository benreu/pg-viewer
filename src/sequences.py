# sequences.py
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


class Sequences :
	def __init__ (self, main, conn, parent_box, schema_name):

		self.main = main
		self.conn = conn
		self.schema_name = schema_name
		revealer = Gtk.Revealer()
		self.checkbutton = Gtk.CheckButton(halign = Gtk.Align.START)
		self.checkbutton.connect('toggled', self.checkbutton_toggled, revealer)
		self.checkbutton.connect('button-release-event', self.checkbutton_release)
		parent_box.pack_start(self.checkbutton, False, False, 0)
		parent_box.pack_start(revealer, False, False, 0)
		self.box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
		self.box.set_margin_start(10)
		revealer.add(self.box)
		self.populate_sequences ()
		parent_box.show_all()

	def checkbutton_release (self, checkbutton, event):
		if event.button == 3:
			menu = Gtk.Menu()
			populate_menu = Gtk.MenuItem("Refresh")
			populate_menu.connect('activate', self.populate_sequences )
			menu.append(populate_menu)
			menu.show_all()
			menu.popup_at_pointer()

	def populate_sequences (self, menuitem = None):
		for child in self.box.get_children():
			self.box.remove(child)
		count = 0 
		c = self.conn.cursor()
		c.execute("SELECT sequence_name FROM information_schema.sequences "
					"WHERE sequence_schema = %s;", (self.schema_name,))
		for row in c.fetchall():
			sequence_name = row[0]
			count += 1
			button = ClickableLabel(label = sequence_name)
			self.box.pack_start(button, False, False, 0)
			menu = Gtk.Menu()
			populate_menu = Gtk.MenuItem("Sequence")
			populate_menu.connect('activate', self.sequence_dialog, sequence_name)
			menu.append(populate_menu)
			button.connect('button-release-event', self.button_released, menu)
		c.close()
		self.checkbutton.set_label("Sequences (%d)" % count)
		self.box.show_all()

	def checkbutton_toggled (self, toggle, revealer):
		revealer.set_reveal_child(toggle.get_active())
		self.main.set_highlight(toggle)

	def sequence_dialog (self, menuitem, sequence_name):
		c = self.conn.cursor()
		dialog = Gtk.Dialog("Sequence value",
								self.main.window,
								Gtk.DialogFlags.MODAL,
								("_Cancel",
								Gtk.ResponseType.REJECT,
								"_Apply",
								Gtk.ResponseType.ACCEPT))
		label = Gtk.Label("Use this value next for %s:" % sequence_name)
		entry = Gtk.Entry()
		c.execute("SELECT nextval('%s.%s'::regclass)::text" % 
							(self.schema_name, sequence_name))
		entry.set_text(c.fetchone()[0])
		box = dialog.get_content_area()
		box.add(label)
		box.add(entry)
		box.show_all()
		result = dialog.run()
		text = entry.get_text()
		dialog.destroy()
		if result == Gtk.ResponseType.ACCEPT:
			try:
				c.execute("ALTER SEQUENCE %s.%s RESTART WITH %s" %
						(self.schema_name, sequence_name, text))
			except Exception as e:
				self.conn.rollback()
				self.show_message(str(e))
		c.close()
		self.conn.commit()

	def button_released (self, toggle, event, menu):
		if event.button == 3:
			menu.show_all()
			menu.popup_at_pointer()

	def clicked (self, button):
		pass

	def show_message (self, message):
		dialog = Gtk.MessageDialog( self.window,
									0,
									Gtk.MessageType.ERROR,
									Gtk.ButtonsType.CLOSE,
									message)
		dialog.run()
		dialog.destroy()
