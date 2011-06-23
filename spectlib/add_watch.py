# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       add_watch.py
#
# See the AUTHORS file for copyright ownership information

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import spectlib.gtkutil
except:
    pass


class Add_watch:
    """Class to create the add watch dialog."""
    # Please do not use confusing widget names such as 'lbl' and 'tbl',
    # Use full names like 'label' and 'table'.
    def __init__(self, specto, notifier, watch_type):
        self.specto = specto
        self.notifier = notifier
        #create tree
        uifile = os.path.join(self.specto.PATH, "uis/add_watch.ui")
        windowname = "add_watch"
        self.builder = gtk.Builder()
        self.builder.set_translation_domain("specto")
        self.builder.add_from_file(uifile)

        self.watch_type = watch_type
        #save the option for hiding the table
        self.option_visible = -1

        #catch some events
        dic = {"on_button_cancel_clicked": self.cancel_clicked,
        "on_button_add_clicked": self.add_clicked,
        "on_button_help_clicked": self.help_clicked,
        "on_add_watch_delete_event": self.delete_event,
        "check_command_toggled": self.command_toggled,
        "check_open_toggled": self.open_toggled,
        "on_refresh_unit_changed": self.set_refresh_values}

        #attach the events
        self.builder.connect_signals(dic)

        self.add_watch = self.builder.get_object("add_watch")
        self.add_watch.set_icon_from_file(self.specto.LOGO_PATH)
        self.add_watch.set_resizable(False)

        self.name = self.builder.get_object("name")
        self.refresh = self.builder.get_object("refresh")
        self.refresh_unit = self.builder.get_object("refresh_unit")

        #create the gui
        self.plugins_ = {}
        self.watch_options = {}

        self.set_options(watch_type)

        #set the default values
        self.refresh_unit.set_active(2)
        self.refresh.set_value(1.0)

        self.name.grab_focus()

    def set_options(self, watch_type):
        """ Show the table with the right watch options. """
        self.watch_options[watch_type] = []
        if hasattr(self.specto.watch_db.plugin_dict[watch_type], 'get_add_gui_info'):
            values = self.specto.watch_db.plugin_dict[watch_type].get_add_gui_info()
        else:
            values = []
        
        try:
            if self.specto.watch_db.plugin_dict[watch_type].dbus_watch == True:
                self.refresh.hide()
                self.refresh_unit.hide()
                self.builder.get_object("label_refresh1").hide()
        except:
            pass

        #create the options gui
        if len(values) > 0:
            self.table = gtk.Table(rows=len(values), columns=1, homogeneous=False)
            self.table.set_row_spacings(6)
            self.table.set_col_spacings(6)
            self.watch_options[watch_type] = {}

            i = 0
            for value, widget in values:
                table, _widget = widget.get_object()
                self.table.attach(table, 0, 1, i, i + 1)
                self.watch_options[watch_type].update({value: widget})
                i += 1

            self.table.show()
            vbox = self.builder.get_object("vbox_watch_options")
            vbox.pack_start(self.table, False, False, 0)

    def set_refresh_values(self, widget):
        """ Set the max and min values for the refresh unit. """
        digits = 0
        climb_rate = 1.0
        refresh_unit = self.refresh_unit.get_active()
        self.old_refresh_value = self.refresh.get_value_as_int()  # Grab the current value for reuse after the scale changes

        # Set the new ranges for the refresh value spinbutton
        if refresh_unit == 0 or refresh_unit == 1:
            adjustment = gtk.Adjustment(value=1, lower=1, upper=60, step_incr=1, page_incr=10, page_size=0)
        if refresh_unit == 2:
            adjustment = gtk.Adjustment(value=1, lower=1, upper=24, step_incr=1, page_incr=10, page_size=0)
        if refresh_unit == 3:
            adjustment = gtk.Adjustment(value=1, lower=1, upper=365, step_incr=1, page_incr=30, page_size=0)

        self.refresh.configure(adjustment, climb_rate, digits)
        self.refresh.set_value(self.old_refresh_value)  # Reuse the previous value, otherwise setting the new scales will reset it to 1

    def add_clicked(self, widget):
        """
        Add the watch to the watches repository.
        """
        values = {}
        #get the standard options from a watch
        values['name'] = self.name.get_text()

        # Check if there already is a watch with the same name
        if self.specto.watch_io.already_exists(values['name']):
            unique_dialog = Unique_Dialog(self.specto)
            result = unique_dialog.run()

            if result == 1:
                self.name.grab_focus()
            else: #edit the existing watch
                self.add_watch.hide_all()
                name = values['name']
                self.notifier.show_edit_watch(-1, name)

        else:
            values['refresh'] = self.specto.watch_db.set_interval(self.refresh.get_value_as_int(), self.refresh_unit.get_active())
            values['type'] = self.watch_type
            values['active'] = True
            values['last_changed'] = ""
            values['changed'] = False
            if self.builder.get_object("check_command").get_active() == True:
                values['command'] = self.builder.get_object("entry_changed_command").get_text()

            if self.builder.get_object("check_open").get_active() == True:
                values['open_command'] = self.builder.get_object("entry_open_command").get_text()
                use_standard_command = False
            else:
                values['open_command'] = ""
                use_standard_command = True
            
            if hasattr(self.specto.watch_db.plugin_dict[values['type']], 'get_add_gui_info'):
                gui_values = self.specto.watch_db.plugin_dict[values['type']].get_add_gui_info()
            window_options = self.watch_options[values['type']]

            for key in window_options:
                values[key] = window_options[key].get_value()
                window_options[key].set_color(0xFFFF, 0xFFFF, 0xFFFF)

            self.builder.get_object("name").modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(0xFFFF, 0xFFFF, 0xFFFF))

            try:
                id = self.specto.watch_db.create({0: values})[0] #write the options in the configuration file
            except AttributeError, error_fields:
                fields = str(error_fields).split(",")
                i = 1
                for field in fields:
                    if field == " name":
                        self.builder.get_object("name").modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(65535, 0, 0))
                        self.builder.get_object("name").grab_focus()
                    else:
                        field = window_options[field.strip()]
                        if i == 1:
                            field.grab_focus()
                            i = 0
                        field.set_color(65535, 0, 0)
            else:
                self.add_watch.destroy()
                if use_standard_command:
                    try:
                        self.specto.watch_db[id].open_command = self.specto.watch_db[id].standard_open_command
                    except:
                        self.specto.watch_db[id].open_command = ""
                self.specto.watch_io.write_watch(values)
                self.notifier.add_notifier_entry(id)
                self.specto.watch_db[id].start()

    def help_clicked(self, widget):
        """ Call the show help function. """
        self.specto.util.show_webpage("http://code.google.com/p/specto/wiki/AddingWatches")

    def cancel_clicked(self, widget):
        """ Destroy the add watch window. """
        self.add_watch.destroy()

    def delete_event(self, widget, event, data=None):
        """ Destroy the window. """
        self.add_watch.destroy()
        return True

    def command_toggled(self, widget):
        sensitive = self.builder.get_object("check_command").get_active()
        self.builder.get_object("entry_changed_command").set_sensitive(sensitive)

    def open_toggled(self, widget):
        sensitive = self.builder.get_object("check_open").get_active()
        self.builder.get_object("entry_open_command").set_sensitive(sensitive)


class Unique_Dialog:
    """
    Class to create a message when you add a watch with an existing name.
    """

    def __init__(self, specto):
        self.specto = specto
        self.uifile = os.path.join(self.specto.PATH, "uis/add_watch_conflict.ui")
        self.dialogname = "dialog"
        self.builder = gtk.Builder()
        self.builder.set_translation_domain("specto")
        self.builder.add_from_file(self.uifile)
        self.unique_dialog = self.builder.get_object("dialog")

    def run(self):
        """ Show the unique dialog. """
        self.unique_dialog.set_icon_from_file(self.specto.LOGO_PATH)
        self.unique_dialog.set_resizable(False)
        result = self.unique_dialog.run()

        self.unique_dialog.destroy()

        return result


if __name__ == "__main__":
    #run the gui
    app = Add_watch()
    gtk.main()
