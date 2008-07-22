# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       notifier.py
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

class Console:
    
    def __init__(self, specto, args):
        self.specto = specto
        self.only_updates = False
        
        if args:
            if args == "--only-updates":
                self.only_updates = True
            elif args == "--help":
                print "\nSpecto console version\n\nUse \"specto --console --only-updates\" to show only updates.\n\n"
                sys.exit(0)
                
    def start_watches(self):
        self.specto.watch_db.restart_all_watches()
        
    def mark_watch_status(self,status, id):
        """ show the right icon for the status from the watch. """ 
        watch = self.specto.watch_db[id]

        if status == "updated":
            print "Watch \"" + watch.name + "\" is updated!"
            print watch.get_extra_information()
        elif self.only_updates:
            return
        elif status == "updating":
            print "Watch \"" + watch.name + "\" started updating."
        elif status == "idle":
            print "Watch \"" + watch.name + "\" has finished updating."                
        elif status == "no-network":
            print "The network connection has failed, network watches will not update."
        elif status == "network":
            print "Network connection detected."
        elif status == "error":
            print "Watch \"" + watch.name + "\" has an error."                
