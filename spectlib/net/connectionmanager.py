import dbus
import urllib2

class CallbackRunner(object):
    def __init__(self):
        self.callbacks = {}
    
    def add_callback(self, callback, *args, **kwargs):
        self.callbacks[callback] = (args, kwargs)

    def _run_callbacks(self):
        # We can't delete items from a dict we're iterating over
        # so we must make a copy first
        cb = dict(self.callbacks)
        for fn, (args, kwargs) in cb.iteritems():
            fn(*args, **kwargs)
            del self.callbacks[fn]
    

class NMListener(CallbackRunner):
    statusTable = {0: u'Unknown',
                   1: u'Asleep',
                   2: u'Connecting',
                   3: u'Connected',
                   4: u'Disconnected' }
    
    def __init__(self, bus):
        super(NMListener, self).__init__()
        nmProxy = bus.get_object('org.freedesktop.NetworkManager',
                                      '/org/freedesktop/NetworkManager')
        self.nmIface = dbus.Interface(nmProxy,
                                      'org.freedesktop.NetworkManager')
        self.nmIface.connect_to_signal('DeviceNoLongerActive', self.on_nm_event,
                                       self.nmIface)
        self.nmIface.connect_to_signal('DeviceNowActive', self.on_nm_event,
                                       self.nmIface)
        self.lastStatus = self.nmIface.state()

    def on_nm_event(self) :
        wasConnected = self.connected()
        self.lastStatus = self.nmIface.state()
        if (not wasConnected) and self.connected() :
            self._run_callbacks()            

    def connected(self):
        return self.lastStatus == 3

    def has_networkmanager(self):
        ### It seems that the only way of being sure the service exists
        ### is to actually try to use it!      
        try:
            self.nmIface.state()
        except dbus.dbus_bindings.DBusException:
            return False
        return True

class FallbackListener(CallbackRunner) :
    def connected(self):
        try:
            # try if google can be reached, i.e. connection to internet is up
            ping = urllib2.urlopen('http://www.google.com')
            ping.close()
            return True
        except IOError:
            return False
