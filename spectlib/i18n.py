# -*- coding: utf-8 -*-

# Specto , Unobtrusive event notifier
#
#       il8n.py
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

import os
import gettext
import locale


MESSAGES_DIR = ''
if os.path.exists("/usr/share/locale") and os.path.isdir("/usr/share/locale"):
    MESSAGES_DIR = "/usr/share/locale"
elif os.path.exists("/usr/local/share/locale") and \
        os.path.isdir("/usr/local/share/locale"):
    MESSAGES_DIR = "/usr/local/share/locale"

def setup_locale_and_gettext():
    package_name = 'specto'
    # Install _() builtin for gettext; always returning unicode objects
    # also install ngettext()
    gettext.install(package_name, localedir=MESSAGES_DIR, unicode=True,
                    names=("ngettext",))
    locale.bindtextdomain(package_name, MESSAGES_DIR)
    locale.bind_textdomain_codeset(package_name, "UTF-8")

    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error, e:
        pass

setup_locale_and_gettext()
