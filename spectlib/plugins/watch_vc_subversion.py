# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_vc_subversion.py
#
# See the AUTHORS file for copyright ownership information

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

from spectlib.watch import Watch
import spectlib.config
import spectlib.gtkconfig
import sys
import os

import pysvn

type = "Watch_vc_subversion"
type_desc = _("Subversion")
icon = 'subversion'
category = _("Version control")


def get_add_gui_info():
    return [("folder", spectlib.gtkconfig.FolderChooser(_("Folder")))]


class Watch_vc_subversion(Watch):
    """
    Watch class that will check if a subversion folder has been changed.
    """

    def __init__(self, specto, id, values):

        watch_values = [("folder", spectlib.config.String(True))]

        self.icon = icon
        self.standard_open_command = 'xdg-open %s' % values['folder']
        self.type_desc = type_desc

        #Init the superclass and set some specto values
        Watch.__init__(self, specto, id, values, watch_values)

        self.use_network = True
        self.repositoy_info = []
        self.remote_branch_label = ""
        self.local_changes = []
        self.remote_changes = []
        
        # Kind of changes to check for, and there are two copies
        # so it is possible to make different checks for local/remote
        self.local_check_kinds = [pysvn.wc_status_kind.modified,\
                                  pysvn.wc_status_kind.added,\
                                  pysvn.wc_status_kind.deleted,\
                                  pysvn.wc_status_kind.replaced,\
                                  pysvn.wc_status_kind.merged,\
                                 ]
        self.remote_check_kinds = [pysvn.wc_status_kind.modified,\
                                   pysvn.wc_status_kind.added,\
                                   pysvn.wc_status_kind.deleted,\
                                   pysvn.wc_status_kind.replaced,\
                                   pysvn.wc_status_kind.merged,\
                                  ]
        
        #Init the pysvn client, and error style
        self.svn_client = pysvn.Client()
        self.svn_client.exception_style = 0

    def check(self):
        """ See if a svn's content has been modified or created. """
        try:
            changes = self.svn_client.status(self.folder,update=True)
            
            #the first time will check for url
            if (self.remote_branch_label == ""):
                self.repositoy_info = self.svn_client.info(self.folder)
                self.remote_branch_label = self.repositoy_info.url
            
            self.remote_changes = []
            self.local_changes = []
            for change in changes:
                if (change.repos_text_status in self.remote_check_kinds):
                    self.remote_changes.append(change)
                    self.actually_changed = True
                if (change.text_status in self.local_check_kinds):
                    self.local_changes.append(change)
                    self.actually_changed = True
                if (self.actually_changed <> True):
                    self.mark_as_read()
        except pysvn.ClientError, e:
            self.set_error(str(e))
        except:
            self.set_error()

        Watch.timer_update(self)

    def get_balloon_text(self):
        """ create the text for the balloon """
        msg = ""
        if len(self.local_changes) <> 0:
            if len(self.local_changes) == 1:
                msg += _("One new local change has not yet been commited to the server.")
            else:
                msg += _("%d new local changes have not yet been commited to the server.") % len(self.local_changes)
        if len(self.remote_changes) <> 0:
            if len(msg) <> 0:
                msg += " "
            if len(self.remote_changes) == 1:
                msg += _("One new change on the server.")
            else:
                msg += _("%d new changes on the server.") % len(self.remote_changes)
        return msg

    def get_extra_information(self):
        repo_info = ""
        count = 3
        for change in self.remote_changes:
            if (change.entry <> None):
                revision = change.entry.commit_revision.number
                count -= 1
                repo_info += "<b> Rev " + str(revision) + " </b> <i>" + str(change.path) + "</i>\n"                
            if (count == 0):
                repo_info += _("and others...")
                break
        return repo_info

    def get_gui_info(self):
        return [(_('Name'), self.name),
                (_('Last changed'), self.last_changed),
                (_('Folder'), self.folder),
                (_('Svn Url'), self.remote_branch_label)]
