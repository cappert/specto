#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_web_static.py
#
# Copyright (c) 2005-2007, Jean-François Fortin Tam
# This module code is maintained by : Jean-François Fortin, Pascal Potvin and Wout Clymans

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

import StringIO, gzip
import os, md5, urllib2
from httplib import HTTPMessage
from math import fabs
from re import compile #this is the regex compile module to parse some stuff such as <link> tags in feeds
from spectlib.i18n import _
import thread
import gtk, time

cacheSubDir__ = os.environ['HOME'] + "/.specto/cache/"
if not os.path.exists(cacheSubDir__):
    os.mkdir(cacheSubDir__)

class Web_watch(Watch):
    """ 
    Watch class that will check if http or rss pages are changed. 
    """
    url_ = ""
    info_ = None
    content_ = None
    lastModified_ = None
    digest_ = None
    refresh_ = None
    infoB_ = None
    cached = 0
    url2_ = ""
    updated = False
    actually_updated = False
    type = 0

    def __init__(self, specto, name, refresh, url, id, error_margin):
        Watch.__init__(self, specto) #init superclass
        self.refresh = refresh
        self.id = id
        self.url_ = url
        if self.url_ == "":
            self.specto.logger.log(_("Watch: \"%s\" has error: empty url") % self.error, "error", self.__class__)
        self.name = name
        self.error_margin = error_margin#the amount in percent (as a float) of what the filesize must change to consider the page changed
        self.error = False
        
    def dict_values(self):
        return { 'name': self.name, 'refresh': self.refresh, 'uri': self.url_, 'error_margin':self.error_margin, 'type':0 }
    
        
    def start_watch(self):
        """ Start the watch. """
        self.thread_update()

    def _real_update(self):
        lock = thread.allocate_lock()
        lock.acquire()
        t=thread.start_new_thread(self.update,(lock,))
        while lock.locked():
            while gtk.events_pending():
                gtk.main_iteration()
            time.sleep(0.05)
        while gtk.events_pending():
            gtk.main_iteration()
        
    def thread_update(self):
        if not self.specto.connection_manager.connected():
            self.specto.logger.log(_("No network connection detected"),
                                   "info", self.__class__)
            self.specto.connection_manager.add_callback(self._real_update)
        else :
            self._real_update()

    def update(self, lock):
        """ See if a http or rss page changed. """
        self.error = False
        self.specto.mark_watch_busy(True, self.id)
        self.specto.logger.log(_("Updating watch: \"%s\"") % self.name, "info", self.__class__)
        
        # Create a unique name for each url.
        digest = md5.new(self.url_).digest()
        cacheFileName = "".join(["%02x" % (ord(c),) for c in digest])
        self.cacheFullPath_ = os.path.join(cacheSubDir__, cacheFileName)
        request = urllib2.Request(self.url_, None, {"Accept-encoding" : "gzip"})
        
        if (self.cached == 1) or (os.path.exists(self.cacheFullPath_)):
            self.cached = 1
            f = file(self.cacheFullPath_, "r")# Load up the cached version
            self.infoB_ = HTTPMessage(f)
            if self.infoB_.has_key('last-modified'):
                request.add_header("If-Modified-Since", self.infoB_['last-modified'])
            if self.infoB_.has_key('ETag'):
                request.add_header("If-None-Match", self.infoB_['ETag'])
        try:
            response = urllib2.urlopen(request)
        except urllib2.URLError, e:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has error: ") % self.name + str(e), "error", self.__class__)
        else:
            self.info_ = response.info()
            self.url2_ = response.geturl()
            self.content_ = self._writeContent(response)
            self.info_['Url'] = self.url_
            self.digest_ = md5.new(self.content_).digest()
            self.digest_ = "".join(["%02x" % (ord(c),) for c in self.digest_])
            self.info_['md5sum'] = self.digest_

            # This uncompresses the gzipped contents, if you need to parse the page. This is used to check if it is a feed for example, a few lines later.
            self.compressedstream = StringIO.StringIO(self.content_)
            try:
                self.page_source = gzip.GzipFile(fileobj=self.compressedstream).read() #try uncompressing
            except:
                self.page_source = self.content_ #the page was not compressed

            # This will check for the "real" website home URL when the website target is an xml feed.
            # First, check if the web page is actually a known feed type.
            # Here we look for three kinds of headers, where * is a wildcard:
                #RSS 1: <feed xmlns=*>
                #RSS 2: <rdf:RDF xmlns:rdf=*>
                #Atom : <feed xmlns=*>
            if not (    compile("<rdf:RDF xmlns:rdf=.*>").findall(self.page_source)==[]   ) or not(    compile("<rss version=.*>").findall(self.page_source)==[]   ) or not (    compile("<feed xmlns=.*>").findall(self.page_source)==[]   ):
                #it seems like it is a syndication feed. Let's see if we can extract the home URL from it.
                self.regexed_contents=compile("<link>.*</link>").findall(self.page_source) # Grabs anything inside <link> and </link>; .* means "any characters
                self.rss_links=""
                for m in self.regexed_contents: # Iterates through and takes off the tags
                    if self.rss_links=="":
                        m=m.strip("<link>").strip("</link>")
                        self.rss_links = m
                #Save the uri_real attribute to the watch list
                self.new_values = {}
                self.new_values['name'] = self.name
                self.new_values['uri_real'] = self.rss_links
                self.specto.watch_io.write_options(self.new_values)
                #TODO: the uri_real is now correctly saved into watches.list. Now, what is missing is someone who would implement quite easily that notifier.py reads watches.list, gets that uri_real and uses it when someone clicks "go to" to open the website. That's all.
            else:
                #the file is not a recognized feed. We will not parse it for the <link> tag.
                pass


            # Here is stuff for filesize comparison, 
            # just in case there is annoying advertising on the page,
            # rendering the md5sum a false indicator.
            self.new_filesize = len(str(self.content_))#size in bytes?... will be used for the error_margin in case of annoying advertising in the page
            #if self.specto.DEBUG: print "\tPerceived filesize is", self.new_filesize, "bytes ("+str(self.new_filesize/1024)+"KB)"#useful for adjusting your error_margin
            
            if int(self.new_filesize)==4:
                #FIXME: temporary hack, not sure the etag is ALWAYS 4bytes
                #4 bytes means it's actually an etag reply, so there is no change. We don't care about filesize checks then.
                self.filesize_difference = 0
            else:
                self.old_filesize = self.specto.watch_io.read_option(self.name, "filesize")
                if self.old_filesize!=0:#if 0, that would mean that read_option could not find the filesize in watches.list
                #if there is a previous filesize
                    #calculate the % changed filesize
                    self.filesize_difference = (fabs(int(self.new_filesize) - int(self.old_filesize)) / int(self.old_filesize))*100
                    #if self.specto.DEBUG: print "\tCached filesize: ", self.old_filesize, "\tFilesize difference percentage:", str(self.filesize_difference)[:5], "%"
                    self.specto.logger.log(_("Difference percentage:%s (Watch: \"%s\")") % (str(self.filesize_difference)[:5], self.name), "info", self.__class__)
                    if (self.filesize_difference  >= float(self.error_margin)*100) and (self.filesize_difference != 0.0):
                    #if the filesize differences exceed the error_margin
                        #if self.specto.DEBUG: print "\tMD5SUM and filesize exceeded the margin: the watch has been updated."
                        self.to_be_stored_filesize = self.new_filesize
                        #if self.specto.DEBUG: print "\tSaved filesize: ", self.to_be_stored_filesize
                        self.updated = True
                        self.actually_updated = True
                        #this means that no matter what, the webpage is updated
                    else:
                    #if there is no important changes in filesize. Call the MD5Sum.
                        #MD5summing analysis
                        if self.cached and (self.infoB_['md5sum'] == self.info_['md5sum']):
                            self.to_be_stored_filesize = self.new_filesize
                            #if self.specto.DEBUG: print "\tSaved filesize: ", self.to_be_stored_filesize
                            self.updated = True
                            self.actually_updated = True
                            self._writeHeaders()
                        else:
                            #we don't want to juggle with all the possible filesizes, 
                            #we want to stay close to the original, because replacing the filesize each time
                            #if the watch is not updated would create a lot of fluctuations
                            self.to_be_stored_filesize = self.old_filesize
                            #if self.specto.DEBUG: print "\tSaved filesize: ", self.to_be_stored_filesize
                            self.actually_updated = False
                else:
                #if there is NO previously stored filesize
                    self.to_be_stored_filesize = self.new_filesize
                    #if self.specto.DEBUG: print "\tSaved filesize: ", self.to_be_stored_filesize

            if (self.url2_ != self.url_):
                #print 'Not the same url ' + self.url2_
                self.write_uri()#it's uri, not url.
            self.write_filesize()
            
        self.specto.mark_watch_busy(False, self.id)
        Watch.update(self, lock)

    def content(self):
        """Get the content as a single string."""
        return self.content_
        
    def info(self):
        """ Returns an HTTPMessage for manipulating headers.
    
        Note that you can use this to read headers but not
        to add or change headers. Use the 'add_headers()' for
        adding/changing header values permanently in the cache."""
        return self.info_
    
    def add_headers(self, headers):
        """Add/change header values in the cache.
        
        Note that if the key/value pair you change is used
        by HTTP then you risk the possibility that the value
        will be over-written the next time content is retrieved
        from that URL.
        """
        for key in headers.keys():
            self.info_[key] = headers[key]
        f = file(self.cacheFullPath_, "w")
        f.write(str(self.info_))
        f.close()
           
    def _writeHeaders(self):
        """ Write the full header in the cache. """
        f = file(self.cacheFullPath_, "w")
        f.write(str(self.info_))
        f.close()

    def write_filesize(self):
        """ Write the filesize in the cache. """
        self.new_values = {}
        self.new_values['name'] = self.name
        self.new_values['filesize'] = self.to_be_stored_filesize
        self.specto.watch_io.write_options(self.new_values)

    def write_uri(self):
        """ Write the uri in the cache. """
        self.new_values = {}
        self.new_values['name'] = self.name
        self.new_values['uri'] = self.url2_
        self.specto.watch_io.write_options(self.new_values)
        self.url_ = self.url2_

    def clearCache(self):
        """ Clear the cache file. """
        [os.unlink(os.path.join(cacheSubDir__, name)) for name in os.listdir(cacheSubDir__)]
        
    def _writeContent(self, response):
        content = ""
        content = response.read()
        return content
    
    def set_url(self, url):
        """ Set the url for the watch. """
        self.url_ = url
        
    def set_error_margin(self, error_margin):
        """ Set the error margin for the watch. """
        self.error_margin = error_margin
