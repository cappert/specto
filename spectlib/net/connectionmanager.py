import dbus
import urllib2

class NMListener(object):
    statusTable = {0: u'Unknown',
                   1: u'Asleep',
                   2: u'Connecting',
                   3: u'Connected',
                   4: u'Disconnected' }
    
    def __init__(self, bus):
        self.nmProxy = bus.get_object('org.freedesktop.NetworkManager',
                                      '/org/freedesktop/NetworkManager')
        self.nmIface = dbus.Interface(self.nmProxy,
                                      'org.freedesktop.NetworkManager')
        self.callbacks = {}
        
    def connected(self):
        return self.nmIface.state() == 3

    def has_networkmanager(self):
        ### It seems that the only way of being sure the service exists
        ### is to actually try to use it!      
        try:
            self.connected()
        except dbus.dbus_bindings.DBusException:
            return False
        return True

    def add_callback(self, callback, *args, **kwargs):
        self.callbacks[callback] = (args, kwargs)

    def _run_callbacks(self):
        # We can't delete items from a dict we're iterating over
        # so we must make a copy first
        cb = dict(self.callbacks)
        for fn, (args, kwargs) in cb.iteritems():
            fn(*args, **kwargs)
            del self.callbacks[fn]

class FallbackListener(object) :
    def connected(self):
        try:
            # try if google can be reached, i.e. connection to internet is up
            ping = urllib2.urlopen('http://www.google.com')
            ping.close()
            return True
        except IOError:
            return False
