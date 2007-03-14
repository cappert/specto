#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       add_watch.py
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

import sys
from spectlib.i18n import _

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import gtk.glade
except:
    pass

class Add_watch:
    """
    Class to create the add watch dialog.
    """
    #Please do not use confusing widget names such as 'lbl' and 'tbl', use full names like 'label' and 'table'.
    def __init__(self, specto):
        self.specto = specto
        #create tree
        gladefile= self.specto.PATH + 'glade/add_watch.glade' 
        windowname= "add_watch"
        self.wTree=gtk.glade.XML(gladefile,windowname, self.specto.glade_gettext)
        
        #save the option for hiding the table
        self.option_visible = -1

        #catch some events
        dic= { "on_button_cancel_clicked": self.cancel_clicked,
        "on_button_add_clicked": self.add_clicked,
        "on_button_help_clicked": self.help_clicked,
        "on_name_changed": self.name_changed,
        "on_add_watch_delete_event": self.delete_event,
        "on_type_changed": self.change_options,
        "on_refresh_unit_changed": self.set_refresh_values }

        #attach the events
        self.wTree.signal_autoconnect(dic)

        self.add_watch=self.wTree.get_widget("add_watch")
        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_window_icon.png' )
        self.add_watch.set_icon(icon)
        self.add_watch.set_resizable( False )
        
        self.name = self.wTree.get_widget("name")
        self.type = self.wTree.get_widget("type")
        self.refresh = self.wTree.get_widget("refresh")
        self.refresh_unit = self.wTree.get_widget("refresh_unit")
        
        #create the gui
        self.create_add_gui()

    def name_changed(self, widget):
        """ Show the watch name in the window. """
        new_name = "<b>" + self.name.get_text() + "</b>"
        self.wTree.get_widget("label7").set_label(new_name)

    def show_mail_options(self, *args):
        """
        Check if we have to show the host and ssl fields or not.
        """
        if self.chkGmail.get_active() == True:
            self.labelHost.hide()
            self.txtHost.hide()
            self.labelSsl.hide()
            self.chkSsl.hide()
        else:
            self.labelHost.show()
            self.txtHost.show()
            self.labelSsl.show()
            self.chkSsl.show()
                       
    def change_file_type(self, *args):
        """ Check if a file watch or a folder watch has to be used. """
        if self.chkFolder.get_active() == True:
            self.btnFile.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        else:
            self.btnFile.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
            
    def create_watch(self):
        """
        Add the watch to the watches repository.
        """
        values = {}
        #get the standard options from a watch
        values['name'] = self.name.get_text()#FIXME: cfgparse cannot have single quotes (') it seems. We must watch out for the watch name or arguments not to have them.
        
        #check if the watch is unique
        if not self.specto.check_unique_watch(values['name']):
            unique_dialog = Unique_Dialog()
            result = unique_dialog.run()
            
            if result ==1:
                self.name.grab_focus()
            else: #edit the existing watch
                self.add_watch.hide_all()
                name = values['name']
                self.specto.show_edit_watch(-1, name)
            
        else:
            self.add_watch.hide_all()#FIXME: this is just an illusion to make the user believe that it was done instantaneously, instead of waiting for (sometimes slow) ressources to destroy the window. Note that I used hide_all instead of hide, otherwise the window refuses to hide itself and its contents.
            values['type'] = self.type.get_active()
            values['refresh_value'] = self.refresh.get_value_as_int()
            values['refresh_unit'] = self.refresh_unit.get_active()
    
            #get the watch dependant options
            watch_options = {}
    
            if values['type'] == 0: #add a website
                values['url'] = self.txtUrl.get_text()
                if values['url'][:7] != "http://" and values['url'][:8] != "https://" and values['url'][:6] != "ftp://":
                    values['url'] = "http://" + values['url']
                    
                values['error_margin'] = (self.adjustment.get_value() / 100)
                    
            elif values['type'] == 1: #add an email
                #check if the watch uses pop3, imap or gmail
                if self.chkPop3.get_active() == True:
                    prot = 0
                    values.update({'host': self.txtHost.get_text()})
                    values.update({'ssl':self.chkSsl.get_active()})
                elif self.chkImap.get_active() == True:
                    prot = 1
                    values.update({'host': self.txtHost.get_text()})
                    values.update({'ssl':self.chkSsl.get_active()})
                else:
                    prot = 2
    
                values.update(
                {
                'username': self.txtUsername.get_text(),
                'password': self.txtPassword.get_text(),
                'prot': prot
                }
                )
            elif values['type'] == 2: #add a file
                values['file'] = self.btnFile.get_filename()
                if self.chkFile.get_active() == True:
                    values['mode'] = _("file")
                else:
                    values['mode'] = _("folder")
                    
            elif values['type'] == 3: #add a system process
                values['process'] = self.txtProcess.get_text()

            elif values['type'] == 4: #add a port
                values['port'] = self.txtPort.get_text()
                    
            self.add_watch.destroy()
            self.specto.add_watch(values) #write the options in the configuration file
            #"del self" would be useful here I think.

    def change_options(self, widget):
        """ Show the table with the right watch options. """
        selected_type = self.type.get_active()

        #hide the previous table
        if self.option_visible != -1:
            if self.option_visible == 0:
                self.tblWeb.hide()
            elif self.option_visible == 1:
                self.tblMail.hide()
            elif self.option_visible == 2:
                self.tblFile.hide()
            elif self.option_visible == 3:
                self.tblProcess.hide()
            elif self.option_visible == 4:
                self.tblPort.hide()
                
        if selected_type == 0: #website
            self.tblWeb.show()

        if selected_type == 1: #email
            self.tblMail.show()

        if selected_type == 2: #add a file
            self.tblFile.show()
            
        if selected_type == 3: #add a process
            self.tblProcess.show()

        if selected_type == 4: #add a port
            self.tblPort.show()

        self.option_visible = selected_type
                    
    def set_refresh_values(self, widget):
        """ Set the max and min values for the refresh unit. """
        digits = 0
        climb_rate = 1.0
        refresh_unit = self.refresh_unit.get_active()
        
        if refresh_unit == 0 or refresh_unit == 1:
            adjustment = gtk.Adjustment(value=1, lower=1, upper=60, step_incr=1, page_incr=10, page_size=0)
        if refresh_unit == 2:
            adjustment = gtk.Adjustment(value=1, lower=1, upper=24, step_incr=1, page_incr=10, page_size=0)
        if refresh_unit == 3:
            adjustment = gtk.Adjustment(value=1, lower=1, upper=365, step_incr=1, page_incr=30, page_size=0)

        self.refresh.configure(adjustment, climb_rate, digits)

    def add_clicked(self,widget):
        """
        Check that everything is properly filled in before calling create_watch.
        """          
        error = False
        selected_type = self.type.get_active()
        if selected_type == 0:
            if self.txtUrl.get_text() == "":
                self.txtUrl.grab_focus()
                self.txtUrl.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(65535, 0, 0))
                error = True
            else:
                self.txtUrl.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(0xFFFF, 0xFFFF, 0xFFFF))
        elif selected_type == 1:
            if not self.chkGmail.get_active():
                if self.txtHost.get_text() == "":
                    self.txtHost.grab_focus()
                    self.txtHost.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(65535, 0, 0))
                    error = True
                else:
                    self.txtHost.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(0xFFFF, 0xFFFF, 0xFFFF))
            if self.txtPassword.get_text() == "":
                self.txtPassword.grab_focus()
                self.txtPassword.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(65535, 0, 0))
                error = True
            else:
                self.txtPassword.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(0xFFFF, 0xFFFF, 0xFFFF))
            if self.txtUsername.get_text() == "":
                self.txtUsername.grab_focus()
                self.txtUsername.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(65535, 0, 0))
                error = True
            else:
                self.txtUsername.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(0xFFFF, 0xFFFF, 0xFFFF))
        elif selected_type == 3:
            if self.txtProcess.get_text() == "":
                self.txtProcess.grab_focus()
                self.txtProcess.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(65535, 0, 0))
                error = True
            else:
                self.txtProcess.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(0xFFFF, 0xFFFF, 0xFFFF))
        elif selected_type == 4:
            if self.txtPort.get_text() == "":
                self.txtPort.grab_focus()
                self.txtPort.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(65535, 0, 0))
                error = True
            else:
                self.txtPort.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(0xFFFF, 0xFFFF, 0xFFFF))

        if self.name.get_text() == "":
            self.name.grab_focus()
            self.name.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(65535, 0, 0))
            error = True
        else:
            self.name.modify_base( gtk.STATE_NORMAL, gtk.gdk.Color(0xFFFF, 0xFFFF, 0xFFFF))
        if error == False:
            self.create_watch()
            
    def help_clicked(self,widget):
        """ Call the show help function. """
        self.specto.util.show_webpage("http://specto.ecchi.ca/Manual/AddingWatches")
    
    def cancel_clicked(self,widget):
        """ Destroy the add watch window. """
        self.add_watch.destroy()

    def delete_event(self, widget, event, data=None):
        """ Destroy the window. """
        self.add_watch.destroy()
        return True
    
    def create_add_gui(self):
        """ Create the gui for the different kinds of watches. """
        ###create the web options gui
        self.tblWeb = gtk.Table(rows=2, columns=2, homogeneous=False)
        self.tblWeb.set_row_spacings(6)
        self.tblWeb.set_col_spacings(6)

        #set the default values
        self.type.set_active(0)
        self.refresh_unit.set_active(2)
        self.refresh.set_value(1.0)

        #url
        labelUrl = gtk.Label(_("URL:"))
        labelUrl.set_alignment(xalign=0.0, yalign=0.5)
        labelUrl.show()
        self.tblWeb.attach(labelUrl, 0, 1, 0, 1)

        self.txtUrl = gtk.Entry()
        self.txtUrl.show()
        self.tblWeb.attach(self.txtUrl, 1, 2, 0, 1)

        tblError_margin = gtk.Table(rows=2, columns=1, homogeneous=False)
        tblError_margin.show()
        self.tblWeb.attach(tblError_margin, 0, 2, 2, 3)
        
        #error margin
        labelSlider = gtk.Label(_("Error Margin (%):"))
        labelSlider.set_alignment(xalign=0.0, yalign=0.5)
        labelSlider.show()
        #self.tblWeb.attach(labelSlider, 0, 1, 2, 3)
        tblError_margin.attach(labelSlider, 0, 1, 0, 1)

        self.adjustment = gtk.Adjustment(value=2.0, lower=0, upper=50, step_incr=0.1, page_incr=1.0, page_size=10)
        self.margin_scale = gtk.HScale(adjustment=self.adjustment)
        self.margin_scale.set_digits(1)
        self.margin_scale.set_value_pos(gtk.POS_RIGHT)
        self.margin_scale.show()
        #self.tblWeb.attach(self.margin_scale, 1, 2, 2, 3)
        tblError_margin.attach(self.margin_scale, 0, 1, 1, 2)


        ###create the mail options gui
        self.tblMail = gtk.Table(rows=5, columns=2, homogeneous=False)
        self.tblMail.set_row_spacings(6)
        self.tblMail.set_col_spacings(6)

        #protocol
        labelProtocol = gtk.Label(_("Protocol:"))
        labelProtocol.set_alignment(xalign=0.0, yalign=0.5)
        labelProtocol.show()
        self.tblMail.attach(labelProtocol, 0, 1, 0, 1)

        vbox_prot = gtk.HBox(False, 10)
        vbox_prot.show()
        self.tblMail.attach(vbox_prot, 1, 2, 0, 1)

        self.chkPop3 = gtk.RadioButton(None, _("POP3"))
        self.chkPop3.set_active(True)
        self.chkPop3.connect("toggled", self.show_mail_options)
        vbox_prot.pack_start(self.chkPop3, True, True, 0)
        self.chkPop3.show()

        self.chkImap = gtk.RadioButton(self.chkPop3, _("IMAP"))
        self.chkImap.connect("toggled", self.show_mail_options)
        vbox_prot.pack_start(self.chkImap, True, True, 0)
        self.chkImap.show()

        self.chkGmail = gtk.RadioButton(self.chkPop3, _("Gmail"))
        self.chkGmail.connect("toggled", self.show_mail_options)
        vbox_prot.pack_start(self.chkGmail, True, True, 0)
        self.chkGmail.show()

        #username
        labelUsername = gtk.Label(_("User:"))
        labelUsername.set_alignment(xalign=0.0, yalign=0.5)
        labelUsername.show()
        self.tblMail.attach(labelUsername, 0, 1, 1, 2)

        self.txtUsername = gtk.Entry()
        self.txtUsername.show()
        self.tblMail.attach(self.txtUsername, 1, 2, 1, 2)

        #password
        labelPassword = gtk.Label(_("Password:"))
        labelPassword.set_alignment(xalign=0.0, yalign=0.5)
        labelPassword.show()
        self.tblMail.attach(labelPassword, 0, 1, 2, 3)

        self.txtPassword = gtk.Entry()
        self.txtPassword.set_visibility(False)
        self.txtPassword.show()
        self.tblMail.attach(self.txtPassword, 1, 2, 2, 3)

        #host
        self.labelHost = gtk.Label(_("Host:"))
        self.labelHost.set_alignment(xalign=0.0, yalign=0.5)
        self.labelHost.show()
        self.tblMail.attach(self.labelHost, 0, 1, 3, 4)

        self.txtHost = gtk.Entry()
        self.txtHost.show()
        self.tblMail.attach(self.txtHost, 1, 2, 3, 4)
        
        #ssl
        self.labelSsl = gtk.Label(_("Use SSL:"))
        self.labelSsl.set_alignment(xalign=0.0, yalign=0.5)
        self.labelSsl.show()
        self.tblMail.attach(self.labelSsl, 0, 1, 4, 5)
        
        self.chkSsl = gtk.CheckButton(None, True)
        self.chkSsl.show()
        self.tblMail.attach(self.chkSsl, 1, 2, 4, 5)        
        
        ###create the file options gui
        self.tblFile = gtk.Table(rows=2, columns=2, homogeneous=False)
        self.tblFile.set_row_spacings(6)
        self.tblFile.set_col_spacings(6)
        
        #file/folder
        self.labelFile = gtk.Label(_("File/folder:"))
        self.labelFile.set_alignment(xalign=0.0, yalign=0.5)
        self.labelFile.show()
        self.tblFile.attach(self.labelFile, 0, 1, 0, 1)

        #option file/folder
        vbox_file = gtk.HBox(False, 10)
        vbox_file.show()
        self.tblFile.attach(vbox_file, 1, 2, 0, 1)

        self.chkFile = gtk.RadioButton(None, _("File"))
        self.chkFile.set_active(True)
        self.chkFile.connect("toggled", self.change_file_type)
        vbox_file.pack_start(self.chkFile, True, True, 0)
        self.chkFile.show()

        self.chkFolder = gtk.RadioButton(self.chkFile, _("Folder"))
        self.chkFolder.connect("toggled", self.change_file_type)
        vbox_file.pack_start(self.chkFolder, True, True, 0)
        self.chkFolder.show()

        #file selection
        self.btnFile = gtk.FileChooserButton(_("Choose a file or folder"))
        self.btnFile.show()
        self.tblFile.attach(self.btnFile, 0, 2, 1, 2)
        
        ###create the process gui
        self.tblProcess = gtk.Table(rows=2, columns=1, homogeneous=False)
        self.tblProcess.set_row_spacings(6)
        self.tblProcess.set_col_spacings(6)
        
        self.labelProcess = gtk.Label(_("Process:"))
        self.labelProcess.set_alignment(xalign=0.0, yalign=0.5)
        self.labelProcess.show()
        self.tblProcess.attach(self.labelProcess, 0, 1, 0, 1)
        
        self.txtProcess = gtk.Entry()
        self.txtProcess.show()
        self.tblProcess.attach(self.txtProcess, 1, 2, 0, 1)


        ###create the port gui
        self.tblPort = gtk.Table(rows=2, columns=1, homogeneous=False)
        self.tblPort.set_row_spacings(6)
        self.tblPort.set_col_spacings(6)
        
        self.labelPort = gtk.Label(_("Port:"))
        self.labelPort.set_alignment(xalign=0.0, yalign=0.5)
        self.labelPort.show()
        self.tblPort.attach(self.labelPort, 0, 1, 0, 1)
        
        self.txtPort = gtk.Entry()
        self.txtPort.show()
        self.tblPort.attach(self.txtPort, 1, 2, 0, 1)


        vbox = self.wTree.get_widget("vbox_watch_options")
        vbox.pack_start(self.tblWeb, False, False, 0)
        vbox.pack_start(self.tblMail, False, False, 0)
        vbox.pack_start(self.tblFile, False, False, 0)
        vbox.pack_start(self.tblProcess, False, False, 0)
        vbox.pack_start(self.tblPort, False, False, 0)
        
    
class Unique_Dialog:
    """
    Class to create a message when you add a watch with an existing name.
    """
    
    def __init__(self):
        self.gladefile= self.specto.PATH + 'glade/add_watch.glade' 
        self.dialogname = "dialog"    
        
    def run(self):
        """ Show the unique dialog. """  
        self.wTree=gtk.glade.XML(self.gladefile, self.dialogname) 
        self.unique_dialog=self.wTree.get_widget("dialog")

        icon = gtk.gdk.pixbuf_new_from_file(self.specto.PATH + 'icons/specto_window_icon.png' )
        self.unique_dialog.set_icon(icon)
        self.unique_dialog.set_resizable( False )
        self.result = self.unique_dialog.run()
        
        self.unique_dialog.destroy()
        
        return self.result
   
if __name__ == "__main__":
    #run the gui
    app=add_watch()
    gtk.main()
