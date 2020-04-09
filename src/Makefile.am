## Process this file with automake to produce Makefile.in
## Created by Anjuta




## Directory where .class files will be installed
pg_viewerdir = $(pythondir)/pg_viewer


pg_viewer_PYTHON = \
	servers.py \
	databases.py \
	sql_window.py \
	sql_window.ui \
	tables.py \
	schemas.py \
	table_view.py \
	columns.py \
	sequences.py \
	widgets.py \
	table_view.ui \
	views.py \
	table_tool_edit.py \
	table_tool_new.py \
	table_tool_window.ui \
	functions.py \
	about.py \
	pg_viewer.py \
	pg_viewer.ui \
	main.py \
	constants.py


EXTRA_DIST = $(ui_DATA)


# Remove ui directory on uninstall
uninstall-local:

	-rm -r $(uidir)

	-rm -r $(pkgdatadir)
