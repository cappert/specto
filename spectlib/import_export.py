#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       import_export.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
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
from spectlib.i18n import _
import os
from spectlib.iniparser import ini_namespace

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import gtk.glade
    import gobject
except:
    pass

class Import_watch:
    """
    Class to create the import/export watch dialog.
    """
    
    def __init__(self, specto, action):
        self.specto = specto
        #create tree
        gladefile= self.specto.PATH + 'glade/import_export.glade' 
        windowname= "import_export"
        self.wTree=gtk.glade.XML(gladefile,windowname, self.specto.glade_gettext)
        self.model = gtk.ListStore(gobject.TYPE_BOOLEAN, gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_INT)
        self.action = action

        #catch some events
        dic= { "on_button_select_all_clicked": self.select_all,
            "on_button_deselect_all_clicked": self.deselect_all,
            "on_button_action_clicked": self.do_action,
            "on_button_close_clicked": self.delete_event}

        #attach the events
        self.wTree.signal_autoconnect(dic)

        self.import_watch=self.wTree.get_widget("import_export")
        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_window_icon.png' )
        self.import_watch.set_icon(icon)
        
        if action == True:
            self.save = Save_dialog(self.specto, True, None)
            self.import_watch.set_title(_("Import watches"))
            self.wTree.get_widget("button_action").set_label(_("Import watches"))
        else:
            self.import_watch.set_title(_("Export watches"))
            self.wTree.get_widget("button_action").set_label(_("Export watches"))
        
        self.treeview=self.wTree.get_widget("treeview")
        self.treeview.set_model(self.model)
        self.treeview.set_flags(gtk.TREE_MODEL_ITERS_PERSIST)
        self.iter = {}
        
        ### Checkbox
        self.renderer = gtk.CellRendererToggle()
        self.renderer.set_property("activatable", True)
        self.renderer.connect("toggled", self.check_clicked, self.model)
        self.columnCheck = gtk.TreeViewColumn(_("Active"), self.renderer, active=0)
        #self.columnCheck.connect("clicked", self.sort_column_active)
        #self.columnCheck.set_sort_column_id(0)
        #self.column.set_resizable(True)
        self.treeview.append_column(self.columnCheck)

        ### Icon
        self.renderer = gtk.CellRendererPixbuf()
        self.columnIcon = gtk.TreeViewColumn(_("Type"), self.renderer, pixbuf=1)
        #self.columnIcon.set_clickable(True)
        #self.columnIcon.connect("clicked", self.sort_column_type)
        self.treeview.append_column(self.columnIcon)

        ### Titre
        self.renderer = gtk.CellRendererText()
        #self.renderer.set_property("editable", True)
        #self.renderer.connect('edited', self.change_entry_name)
        self.columnTitel = gtk.TreeViewColumn(_("Name"), self.renderer, markup=2)
        #self.columnTitel.connect("clicked", self.sort_column_name)
        self.columnTitel.set_expand(True)
        self.columnTitel.set_resizable(True)
        #self.columnTitel.set_sort_column_id(2)
        self.treeview.append_column(self.columnTitel)
        
        ### ID
        self.renderer = gtk.CellRendererText()
        self.column = gtk.TreeViewColumn(_("ID"), self.renderer, markup=3)
        self.column.set_visible(False)
        #self.column.set_sort_column_id(3)
        self.treeview.append_column(self.column)
        
        ### type
        self.renderer = gtk.CellRendererText()
        self.columnType = gtk.TreeViewColumn(_("TYPE"), self.renderer, markup=4)
        self.columnType.set_visible(False)
        #self.columnType.set_sort_column_id(4)
        self.treeview.append_column(self.columnType)
        
        
        for i in self.specto.watch_db:
            watch = self.specto.watch_db[i]
            self.add_watch_entry(watch.name, watch.type, watch.id)

        
    def select_all(self, widget):
        for i in self.specto.watch_db:
            self.model.set_value(self.iter[i], 0, 1)
        
    def deselect_all(self, widget):
        for i in self.specto.watch_db:
            self.model.set_value(self.iter[i], 0, 0)
        
    def do_action(self, widget):
        if self.action == True:
            pass
        else:
            self.save = Save_dialog(self.specto, False, self.get_selected_watches())
        
    def delete_event(self, widget, *args):
        """ Destroy the window. """
        self.import_watch.destroy()
        return True
    
    def get_selected_watches(self):
        selected_watches_db = {}
        
        for i in self.specto.watch_db:
            if self.model.get_value(self.iter[i], 0) == True:
                id = len(selected_watches_db)
                selected_watches_db[id] = self.specto.watch_db[i]
        return selected_watches_db
       
    
    def add_watch_entry(self, name, type, id):
        """ Add an entry to the notifier list. """
        i = id#FIXME: those icons need to die when we figure out how to make cells' contents insensitive in notifier
        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/notifier/error.png' )
        if type == 0:
            icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/notifier/faded/web.png' )
        elif type == 1:
            icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/notifier/faded/mail.png' )
        elif type == 2:
            icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/notifier/faded/folder.png' )
        elif type == 3:
            icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/notifier/faded/process.png' )

        self.iter[i] = self.model.insert_before(None, None)
        self.model.set_value(self.iter[i], 0, 0)
        self.model.set_value(self.iter[i], 1, icon)
        self.model.set_value(self.iter[i], 2, name)
        self.model.set_value(self.iter[i], 3, id)
        self.model.set_value(self.iter[i], 4, type)
    
    def check_clicked(self, object, path, model):
        """ Call the main function to start/stop the selected watch. """
        sel = self.treeview.get_selection()
        sel.select_path(path)
            
        model, iter = self.treeview.get_selection().get_selected()
        i = int(model.get_value(iter, 3))
        
        if model.get_value(iter,0):
            model.set_value(iter, 0, 0)
        else:
            model.set_value(iter, 0, 1)
            
            
class Save_dialog:
    """ 
    Class for displaying the save as dialog.
    """
        
    def __init__(self, specto, action_type, watches_db):
        self.specto = specto
        #create tree
        gladefile= self.specto.PATH + 'glade/import_export.glade' 
        windowname= "filechooser"
        self.wTree=gtk.glade.XML(gladefile,windowname)        
        self.save_dialog = self.wTree.get_widget("filechooser")
        self.action_type = action_type
        
        if action_type == False: 
            self.save_dialog.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
            self.wTree.get_widget("button_save").set_label("gtk-save") 
            self.watches_db = watches_db   
            
        dic={
        "on_button_cancel_clicked": self.cancel,
        "on_button_save_clicked": self.save
        }
        #attach the events
        self.wTree.signal_autoconnect(dic)
            
        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_window_icon.png')
        self.save_dialog.set_icon(icon)
        self.save_dialog.set_filename(os.environ['HOME'] + "/ ")
        
    def cancel(self, *args):
        """ Close the save as dialog. """
        self.save_dialog.destroy()
        
    def save(self, *args):
        """ Save the file. """
        file_name = self.save_dialog.get_filename()
        
        if self.action_type == True:
            print "not implemented yet!"
        else:
            for i in self.watches_db:
                values =  self.watches_db[i].dict_values()
                self.write_options(file_name,values)
        
        self.save_dialog.destroy()
        
    def write_options(self, file_name, values):
        """
        Write or change the watch options in a configuration file.
        Values has to be a dictionary with the name from the options and the value. example: { 'name':'value', 'name':'value' }
        If the name is not found, a new watch will be added, else the excisting watch will be changed.
        """
        if not os.path.exists(file_name):
            f = open(file_name, "w")
            f.close()
        self.cfg = ini_namespace(file(file_name))
        name = values['name']

        if not self.cfg._sections.has_key(name):
            self.cfg.new_namespace(name) #add a new watch

        del values['name']
        for option, value  in values.iteritems():
            self.cfg[name][option] = value

        f = open(file_name, "w")
        f.write(str(self.cfg).strip()) #write the new configuration file
        f.close()
        
if __name__ == "__main__":
    #run the gui
    app=import_watch()
    gtk.main()
