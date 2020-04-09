# widgets.py
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


from gi.repository import Gtk, GtkSource

class ClickableLabel (Gtk.EventBox):
	def __init__ (self, label):

		Gtk.EventBox.__init__(self)
		self.label = Gtk.Label(label = label, halign = Gtk.Align.START)
		self.set_size_request(20, -1)
		self.add(self.label)
		self.show_all()

	def set_label(self, label):
		self.label.set_label(label)

class SetupSourceView (GtkSource.Buffer):
	def __init__ (self, source_view):

		GtkSource.Buffer.__init__(self)
		language_manager = GtkSource.LanguageManager()
		self.set_language(language_manager.get_language('sql'))
		source_view.set_buffer(self)
		completion = source_view.get_completion()
		keyword_provider = GtkSource.CompletionWords.new('Keywords')
		keyword_provider.register(self)
		completion.add_provider(keyword_provider)



