import unittest
from spectlib.net.connectionmanager import (NMListener, FallbackListener,
                                            CallbackRunner)
import dbus
import urllib2

class MockNetworkManager(object):
    def __init__(self):
        self.status = 0

    def state(self):
        return self.status

    def setConnected(self):
        self.status = 3

    def setDisconnected(self):
        self.status = 4
        
class MockFailNetworkManager(object):
    excepitonMessage='The name org.freedesktop.NetworkManager was not provided\
    by any .service files'
    def state(self):
        raise dbus.dbus_bindings.DBusException(self.excepitonMessage)

class LogingCallback(object):
    def __init__(self):
        self.log = []

    def __call__(self, *args, **kwargs):
        self.log.append((args, kwargs))

class TestCallbackRunner(unittest.TestCase):
    def setUp(self):
        self.cbRunner = CallbackRunner()
        
    def test_addingCallback(self):
        """
        Add a callback and trigger it
        """
        callback = LogingCallback()
        self.cbRunner.add_callback(callback)
        self.cbRunner._run_callbacks()
        self.assertEqual([(tuple() , { })], callback.log)

    def test_callbackArgs(self):
        """
        Add a callback, with some args, and trigger it
        """
        callback = LogingCallback()
        self.cbRunner.add_callback(callback, 'foo', 'bar')
        self.cbRunner._run_callbacks()
        self.assertEqual([(('foo', 'bar') , { })], callback.log)

    def test_callbackKWArgs(self):
        """
        Add a callback, with some KWArgs, and trigger it
        """
        callback = LogingCallback()
        self.cbRunner.add_callback(callback, foo='bar')
        self.cbRunner._run_callbacks()
        self.assertEqual([(tuple() , {'foo' : 'bar'})], callback.log)
        
    def test_callbackArgsAndKWargs(self):
        """
        Add a callback, with both Args and KWArgs, and trigger it.
        """
        callback = LogingCallback()
        self.cbRunner.add_callback(callback, 'empathy', foo='bar')
        self.cbRunner._run_callbacks()
        self.assertEqual([(('empathy', ) , {'foo' : 'bar'})], callback.log)
        
    def test_multipleCallbacks(self):
        """
        Add two callbacks.  Each should be run with its specified arguments
        """
        cb1 = LogingCallback()
        cb2 = LogingCallback()
        self.cbRunner.add_callback(cb1, 'cb1 called')
        self.cbRunner.add_callback(cb2, 'cb2 called')
        self.cbRunner._run_callbacks()
        self.assertEqual([(('cb1 called',), {})], cb1.log)
        self.assertEqual([(('cb2 called',), {})], cb2.log)

    def test_registerCallbackMultipleTimes(self):
        """
        Registering a callback twice should update the args and kwargs, but
        NOT cause it to be called twice
        """
        callback = LogingCallback()
        self.cbRunner.add_callback(callback, 'foo')
        self.cbRunner.add_callback(callback, 'bar')
        self.cbRunner._run_callbacks()
        self.assertEqual([(('bar', ) , {})], callback.log)

    def test_callbackOnlyRunOnce(self):
        """
        Callbacks should be removed after they are run.  Each call to
        add_callback should trigger at most one callback
        """
        callback = LogingCallback()
        self.cbRunner.add_callback(callback, 'foo')
        self.cbRunner._run_callbacks()
        self.cbRunner._run_callbacks()
        self.assertEqual([(('foo', ) , {})], callback.log)


class TestNMConnectionListener(unittest.TestCase) :
    def setUp(self):
        bus = dbus.SystemBus()
        self.mockNM = MockNetworkManager()
        self.nmListener = NMListener(bus)
        self.nmListener.nmIface = self.mockNM
        
    def test_connected(self):
        self.mockNM.setConnected()
        self.assertTrue(self.nmListener.connected())

    def test_unconnected(self):
        self.mockNM.setDisconnected()
        self.assertFalse(self.nmListener.connected())

    def test_noNetworkManager(self):
        self.nmListener.nmIface = MockFailNetworkManager()
        self.assertFalse(self.nmListener.has_networkmanager())

    def test_hasNetworkManager(self):
        self.assertTrue(self.nmListener.has_networkmanager())



def mockFailingUrlOpen(url) :
    raise IOError('foo')

def mockWorkingUrlOpen(url) :
    class MockUrl(object) :
        def close(self) :
            pass
    return MockUrl()
    

class TestFallbackConnectionListener(unittest.TestCase) :
    def setUp(self):
        self.fbListener = FallbackListener()
        self.realUrlOpen = urllib2.urlopen

    def tearDown(self):
        urllib2.urlopen = self.realUrlOpen
    
    def test_connected(self):
        urllib2.urlopen = mockWorkingUrlOpen
        self.assertTrue(self.fbListener.connected())

    def test_disconnected(self):
        urllib2.urlopen = mockFailingUrlOpen
        self.assertFalse(self.fbListener.connected())


        
if __name__ == '__main__':
    unittest.main()
