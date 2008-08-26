# -*- coding: UTF8 -*-

# Specto , Unobtrusive event notifier
#
#       watch_web_static.py
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

from spectlib.watch import Watch
import spectlib.gtkconfig
import spectlib.util

import StringIO, gzip
import os, md5, urllib2, difflib, pprint
from httplib import HTTPMessage, BadStatusLine
from math import fabs
from re import compile #this is the regex compile module to parse some stuff such as <link> tags in feeds
from spectlib.i18n import _
import  time
import socket #to add a timeout to the global process

    
type = "Watch_web_static"
type_desc = "Webpage/feed"
open_command = ""
icon = 'applications-internet'

class Watch_web_static(Watch):
    """ 
    Watch class that will check if http or rss pages are changed. 
    """
    type_desc = type_desc
    url_ = ""
    info_ = None
    content_ = None
    lastModified_ = None
    digest_ = None
    refresh_ = None
    infoB_ = None
    cached = 0
    url2_ = ""

    def __init__(self, specto, id, values):
        watch_values = [ 
                        ( "uri", spectlib.config.String(True) ),
                        ( "error_margin", spectlib.config.Dec(True) ),
                        ( "redirect", spectlib.config.Boolean(False) )
                       ]
        
        self.standard_open_command = spectlib.util.return_webpage(values['uri']) 
                       
        Watch.__init__(self, specto, id, values, watch_values)
        
        self.cacheSubDir__ = specto.CACHE_DIR
        self.use_network = True
        self.filesize_difference = 0.0
        self.icon = icon
        
#        self.error_margin = self.error_margin       
        self.open_command = self.open_command.replace("&","\&")    
        self.url_ = self.uri
        self.diff = ""
        
    def update(self):
        """ See if a http or rss page changed. """
        # Create a unique name for each url.
        if self.uri[:7] != "http://" and self.uri[:8] != "https://" and self.uri[:6] != "ftp://":
            self.uri = "http://" + self.uri
        self.url_ = self.uri
        digest = md5.new(self.url_).digest()
        cacheFileName = "".join(["%02x" % (ord(c),) for c in digest])
        self.cacheFullPath_ = os.path.join(self.cacheSubDir__, cacheFileName)
        self.cacheFullPath2_ = os.path.join(self.cacheSubDir__, cacheFileName + "size")
        socket.setdefaulttimeout(10)# set globally the timeout to 10 seconds
        request = urllib2.Request(self.uri, None, {"Accept-encoding" : "gzip"})
        cache_res = ""
        if (self.cached == 1) or (os.path.exists(self.cacheFullPath_)):
            self.cached = 1
            try:
                f = file(self.cacheFullPath_, "r")# Load up the cached version
                cache_res = f.read()
                f.close()
            except:
                cache_res = ""
        try:
            response = urllib2.urlopen(request)
        except (urllib2.URLError, BadStatusLine), e:
            self.error = True
            self.specto.logger.log(_("Watch: \"%s\" has error: ") % self.name + str(e), "error", self.__class__)
        else:
            self.info_ = response.info()
            self.url2_ = response.geturl()
            self.content_ = self._writeContent(response)
            self.info_['Url'] = self.uri
            self.digest_ = md5.new(self.content_).digest()
            self.digest_ = "".join(["%02x" % (ord(c),) for c in self.digest_])
            self.info_['md5sum'] = self.digest_

            # This uncompresses the gzipped contents, if you need to parse the page. This is used to check if it is a feed for example, a few lines later.
            self.compressedstream = StringIO.StringIO(self.content_)
            try:
                self.page_source = gzip.GzipFile(fileobj=self.compressedstream).read() #try uncompressing
            except:
                self.page_source = self.content_ #the page was not compressed
            
            self.page_source = self.escape(self.page_source)
            self.diff = textDiff(cache_res, self.page_source)
            try:
                out_file = file(self.cacheFullPath_, "w")
                out_file.write(str(self.page_source))
                out_file.close()
            except:
                pass
                
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
                #change the uri_real attribute
                if self.open_command == self.standard_open_command:
                    self.standard_open_command = spectlib.util.return_webpage(self.rss_links)
                    self.open_command = self.standard_open_command 
            else:
                #the file is not a recognized feed. We will not parse it for the <link> tag.
                pass


            # Here is stuff for filesize comparison, 
            # just in case there is annoying advertising on the page,
            # rendering the md5sum a false indicator.
            self.new_filesize = len(str(self.content_))#size in bytes?... will be used for the error_margin in case of annoying advertising in the page
            #if self.specto.DEBUG:  "\tPerceived filesize is", self.new_filesize, "bytes ("+str(self.new_filesize/1024)+"KB)"#useful for adjusting your error_margin
            
            if int(self.new_filesize)==4:
                #FIXME: temporary hack, not sure the etag is ALWAYS 4bytes
                #4 bytes means it's actually an etag reply, so there is no change. We don't care about filesize checks then.
                self.filesize_difference = 0
            else:
                self.old_filesize = self.read_filesize()
                if self.old_filesize!=0:#if 0, that would mean that read_option could not find the filesize in watches.list
                #if there is a previous filesize
                    #calculate the % changed filesize
                    self.filesize_difference = (fabs(int(self.new_filesize) - int(self.old_filesize)) / int(self.old_filesize))*100
                    #if self.specto.DEBUG: print "\tCached filesize: ", self.old_filesize, "\tFilesize difference percentage:", str(self.filesize_difference)[:5], "%"
                    #self.specto.logger.log(_("Difference percentage:%s (Watch: \"%s\")") % (str(self.filesize_difference)[:5], self.name), "info", self.__class__)
                    if self.cached and self.diff and (self.filesize_difference  >= float(self.error_margin)*100) and (self.filesize_difference != 0.0): #and (self.infoB_['md5sum'] == self.info_['md5sum']):
                        self.to_be_stored_filesize = self.new_filesize
                        self.actually_updated = True
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

            if (self.url2_ != self.url_) and self.redirect == True:
                self.write_uri()#it's uri, not url.
            self.write_filesize()
            
        Watch.timer_update(self)

    def content(self):
        """Get the content as a single string."""
        return self.content_
        
    def info(self):
        """ Returns an HTTPMessage for manipulating headers.
    
        Note that you can use this to read headers but not
        to add or change headers. Use the 'add_headers()' for
        adding/changing header values permanently in the cache."""
        return self.info_
    
    def write_filesize(self):
        """ Write the filesize in the watch list. """
        try:
            f = open(self.cacheFullPath2_, "w")
        except:
            self.specto.logger.log(_("There was an error opening the file %s") % self.cacheFullPath2_, "critical", self.__class__)
        else:
            f.write(str(self.to_be_stored_filesize))
            
        finally:
            f.close()
            
    def read_filesize(self):
        if os.path.exists(self.cacheFullPath2_):
            try:
                f = open(self.cacheFullPath2_, "r")
            except:
                self.specto.logger.log(_("There was an error reader the file %s") % self.cacheFullPath2_, "critical", self.__class__)
            else:
                size = f.read()
                if size != "":
                    return size
                else:
                    return 0
            finally:
                f.close()
        else:
            return 0
        
        
    def write_uri(self):
        """ Write the uri in the watch list. """
        self.specto.watch_io.write_option(self.name, 'uri', self.url2_)
        self.url_ = self.url2_

    def remove_cache_files(self):
        os.unlink(self.cacheFullPath_)
        os.unlink(self.cacheFullPath2_)        
        
    def _writeContent(self, response):
        content = ""
        content = response.read()
        return content

    def escape(self, text, quotes=True):
        """Create a Markup instance from a string and escape special characters
        it may contain (<, >, & and ").

        If the `quotes` parameter is set to `False`, the " character is left as
        is. Escaping quotes is generally only required for strings that are to
        be used in attribute values.
        """
        text = str(text).replace('&', '&amp;') \
                        .replace('<', '&lt;') \
                        .replace('>', '&gt;')
        if quotes:
            text = text.replace('"', '&#34;')
        return text
            
    def get_balloon_text(self):
        """ create the text for the balloon """  
        text = ("The website, <b>%s</b>, has been updated.\nDifference percentage: %s percent") % (self.name, str(self.filesize_difference)[:5])
        return text
    
    def get_extra_information(self):
        text = ""
        if self.diff:
            text = self.diff
        return text
            
    def get_gui_info(self):
        return [
                ('Name', self.name),
                ('Last updated', self.last_updated),
                ('Url', self.url_),
                ("Error margin", str(self.error_margin) + "%")
                ]

def get_add_gui_info():
    return [
            ("uri", spectlib.gtkconfig.Entry("Url")),
            ("error_margin", spectlib.gtkconfig.Scale("Error margin (%)",value=2.0,upper=50,step_incr=0.1,page_incr=1.0))
            ]

"""HTML Diff: http://www.aaronsw.com/2002/diff
Rough code, badly documented. Send me comments and patches."""

__author__ = 'Aaron Swartz <me@aaronsw.com>'
__copyright__ = '(C) 2003 Aaron Swartz. GNU GPL 2.'
__version__ = '0.22'

import difflib, string

def isTag(x): return x[0] == "<" and x[-1] == ">"

def textDiff(a, b):
	"""Takes in strings a and b and returns a human-readable HTML diff."""

	out = []
	a, b = html2list(a), html2list(b)
	s = difflib.SequenceMatcher(None, a, b)
	for e in s.get_opcodes():
		if e[0] == "replace":
			# @@ need to do something more complicated here
			# call textDiff but not for html, but for some html... ugh
			# gonna cop-out for now
			out.append('<span foreground=\"red\">'+''.join(a[e[1]:e[2]]) + '</span><span foreground=\"green\">'+''.join(b[e[3]:e[4]])+"</span>\n")
		elif e[0] == "delete":
			out.append('<span foreground=\"red\">'+ ''.join(a[e[1]:e[2]]) + "</span>\n")
		elif e[0] == "insert":
			out.append('<span foreground=\"green\">'+''.join(b[e[3]:e[4]]) + "</span>\n")
	return ''.join(out)

def html2list(x, b=1):
	mode = 'char'
	cur = ''
	out = []
	for c in x:
		if mode == 'tag':
			if c == '>': 
				if b: cur += ']'
				else: cur += c
				out.append("");cur = ''; mode = 'char'
			else: cur += c
		elif mode == 'char':
			if c == '<': 
				out.append(cur)
				if b: cur = '['
				else: cur = c
				mode = 'tag'
			elif c in string.whitespace: out.append(cur+c); cur = ''
			else: cur += c
	out.append(cur)
    
	return filter(lambda x: x is not '', out)
	
