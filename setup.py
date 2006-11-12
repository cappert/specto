#!/usr/bin/env python
import sys
import os
from distutils.core import setup

f=open('VERSION', 'r') # Open the VERSION file for reading.
version_string = f.readline()[:-1] # "[:-1]" means we omit the last character, which is "\n".
f.close

def give_files(dir, *extension):
    files=[]

    all_files=os.listdir(dir)

    for file in all_files:
        ext=(os.path.splitext(file))[1]
    
        if ext in extension:
            files.append(dir + file)

    return files

i18n_languages = "fr ro de"#list all the languages, separated by one whitespace
def give_mo_file(lang):
    return "po/" + str(lang) + "/specto.mo"

def give_mo_path(lang):
    return "share/locale/" + str(lang) + "/LC_MESSAGES/"

def give_mo_tuples(langs):
    mo_tuple_list=[]
    for lang in langs.split(' '):
        mo_tuple_list.append( (give_mo_path(lang),[give_mo_file(lang)]) )
    return mo_tuple_list

temp_files = [#The path are relatives to sys.prefix
    ('share/doc/specto', ['COPYING', 'VERSION', 'ChangeLog', 'README']),
    ('share/pixmaps', ['specto.png']),
    ('share/applications', ['specto.desktop']),
    ('share/specto/icons', give_files('icons/', '.png')),
    ('share/specto/icons/notifier', give_files('icons/notifier/', '.png')),
    ('share/specto/icons/notifier/faded', give_files('icons/notifier/faded/', '.png')),
    ('share/specto/icons/notifier/big', give_files('icons/notifier/big/', '.png', '.svg')),
    ('share/specto/glade', give_files('glade/', '.glade'))
    ]

for lang_tuple in give_mo_tuples(i18n_languages):
    temp_files.append(lang_tuple)

setup(name = "specto",
    version = version_string,
    description = "A program to notify the user of almost all events",
    author = "Jeff Fortin",
    author_email = "kiddokiddo@users.sourceforge.net",
    url = "http://specto.sourceforge.net",
    packages = ['specto'],
    package_dir = {'': 'src'},
    #package_data = {'specto': ['preferences.glade','notify.glade']},
    scripts = ['specto'],
    data_files = temp_files
    )
