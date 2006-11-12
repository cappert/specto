#!/bin/bash
#this script is for translators. It is used to regenerate the translations template file (po/specto.pot) when strings in specto have changed.

find ../src -type f | xargs ./pygettext.py
mv messages.pot specto.pot
