# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       networkmanager.py
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

import dbus
import dbus.glib
import urllib2
import gobject
import time


def get_net_listener():
    """
    Try to connect to the DBus service for NetworkManager.
    If it fails, fallback to a prehistoric method of checking net connectivity.
    """
    try:
        listener = NMListener(dbus.SystemBus())
    except dbus.DBusException:
        listener = FallbackListener()
    return listener


class CallbackRunner(object):

    def __init__(self):
        self.callbacks = {}

    def add_callback(self, callback, *args, **kwargs):
        self.callbacks[callback] = (args, kwargs)

    def _run_callbacks(self):
        """
        Network is now up, allow Specto's watches to check for updates.
        """
        # We can't delete items from a dict we're iterating over
        # so we must make a copy first
        cb = dict(self.callbacks)
        for fn, (args, kwargs) in cb.iteritems():
            fn(*args, **kwargs)
            del self.callbacks[fn]


class NMListener(CallbackRunner):

    """
    A class to interact with NetworkManager, check the connection status,
    and listen for signals indicating changes in connectivity.
    """

    # Currently, the status tables below are not actually used in the code.
    # They simply make it easier to know what the status codes mean.
    statusTable_nm8 = {0: u'Unknown',
                        1: u'Asleep',
                        2: u'Connecting',
                        3: u'Connected',
                        4: u'Disconnected'}
    
    statusTable_nm9 = {0:  u'Unknown',
                        10: u'Asleep',
                        20: u'Disconnected',
                        30: u'Disconnecting',
                        40: u'Connecting',
                        50: u'Local connectivity',
                        60: u'Site connectivity',
                        70: u'Global connectivity'}

    def __init__(self, bus):
        """
        Set up the connection to DBus and NetworkManager
        """
        super(NMListener, self).__init__()
        nmProxy = bus.get_object('org.freedesktop.NetworkManager',
                                 '/org/freedesktop/NetworkManager')

        self.nmIface = dbus.Interface(nmProxy, "org.freedesktop.DBus.Properties")
        bus.add_signal_receiver(self.on_nm_event,
                                  'StateChanged',
                                  'org.freedesktop.NetworkManager',
                                  'org.freedesktop.NetworkManager',
                                  '/org/freedesktop/NetworkManager')

        # Now that we have DBus connected, the only way to truly ensure we have
        # NetworkManager is to try to use it.
        try:
            self.lastStatus = self.nmIface.Get("org.freedesktop.NetworkManager", "State")
        except dbus.DBusException:
            raise # tell get_new_listener() to use FallbackListener()

        try:
            # If the line below fails, we are using NM 0.8.x instead of 0.9.x
            if self.nmIface.Get("org.freedesktop.NetworkManager", "Version") > "0.8.9":
                self.nmConnectedStatus = 70
            else:
                self.nmConnectedStatus = 3
        except dbus.DBusException: # TODO: catch the exact exception for missing dbus props
            # We are running NM 0.8.x:
            self.nmConnectedStatus = 3

    def on_nm_event(self, *args, **kwargs):
        """
        When a NetworkManager event occurs, check if we were previously offline
        and are now online. If so, run the callbacks to update Specto's watches
        """
        wasConnected = self.connected()
        self.lastStatus = self.nmIface.Get("org.freedesktop.NetworkManager", "State")
        if (not wasConnected) and self.connected():
            self._run_callbacks()

    def connected(self):
        """
        Return whether or not NetworkManager was connected at the latest event
        """
        return self.lastStatus == self.nmConnectedStatus


class FallbackListener(CallbackRunner):

    """
    A primitive method of checking if an Internet connection is available.
    """

    def __init__(self):
        self.last_checked = 0
        self._lastConnected = self.connected()
        self._timer_id = gobject.timeout_add(int(10*60*1000), self._callback)

    def connected(self):
        if (time.time() - self.last_checked) > 10*60:
            self.last_checked = time.time()
            try:
                # try to see if google can be reached
                # i.e. connection to internet is up
                ping = urllib2.urlopen('http://www.google.com')
                ping.close()
                self._lastConnected = True
            except IOError:
                self._lastConnected = False

        return self._lastConnected

    def _callback(self):
        wasConnected = self._lastConnected
        self._lastConnected = self.connected()
        if (not wasConnected) and self._lastConnected:
            self._run_callbacks()
