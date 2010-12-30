==================================
Specto, unobtrusive event notifier
==================================

:Authors:
	Jean-François Fortin Tam

	Wout Clymans

:Date: Sat Nov 13 11:26:14 2010

:Homepage: http://specto.sourceforge.net/

.. raw:: pdf

   PageBreak

.. contents::

.. raw:: pdf

   PageBreak

Terminology
===========

Generic terms
-------------

- Watch: This is the "object" that checks a target for updates at a regular
  time interval. In the case of a "mail watch", for example, a watch could
  check for new emails every hour.
- Refresh Interval: Time span between each watch checks. For example, a refresh
  interval of 3600 (60 minutes) means that the watch will check the content for
  updates, wait 60 minutes, and check again. It is recommended that you set a
  reasonable amount of time between watch checks, in order to save bandwidth
  and prevent content providers from saying nasty words.
- Error Margin: The maximum filesize difference (in percent) that a webpage can
  have until it is considered as "updated"
- URL: A Uniform Resource Locator (URL) is a string of characters conforming to
  a standardized format, which refers to a resource on the Internet (such as a
  document or an image) by its location. For example, the URL of this page is
  Terminology. An HTTP URL, commonly called a web address, is usually shown in
  the address bar of a web browser. In the notifier window's watch information
  pane, we refer to it as location.
- Notifier: Specto's main window, that is, the one that contains the list of the
  watches and allows managing them.
- Debug Mode: A special operation mode of Specto that allows getting more
  information in order to help detecting bugs.
- Bug: A software bug is an error, flaw, mistake, failure, or fault in a
  computer program that prevents it from working as intended, or produces an
  incorrect result. As a user, if you experience weird behavior from Specto,
  it may be that you found a bug. You should report it so that we know of its
  existence, if it has not already been reported by someone else.
- Notification icon: the icon that shows in the panel's notification area. This
  is not called a "tray icon".
- Balloons: the notification bubbles/toasts that appear, attached to the
  notification icon in the panel's notification area

Watch statuses
--------------

- idle: the watch is not marked as having unread items, and is not doing
  anything (translator hint synonyms: idle/sleep/ready)
- checking: the watch is busy checking for updates (translator hint synonyms:
  checking/refreshing). This was previously called "updating".
- changed: the watch has new unread items that have not yet been "marked as
  read" by the user.
- error: the watch encountered an error?

Additional notes
................

"Checking" was previously called "updating", and "changed" was previously called
"updated". These previous terms were terribly confusing, because they ended up
creating messages where you are not 100% sure if it means the watch has
"finished checking" or if it means that it "finished checking and has detected
changes". It also made the code much harder to understand, since you're never
entirely sure that the ones who wrote it were not drunk that day :)

When a watch goes through the checking process successfully (status != "error")
but does not have new unread items (status != "changed"), do NOT use the wording
"updated" or "finished updating" or anything like that, because it induces
confusion. Instead, say that the watch is now "idle". Basically, these are the
possible paths a watch can take:

- idle --> checking --> idle.
- idle --> checking --> changed --> marks the watch as read --> idle.


Guidelines
==========

Contributing
------------

Specto is a project based on volunteering. That means that when contributing,
you must be willing to make that will be readable by others, by following
these few guidelines to keep things smooth.

Communicating
.............

There are some ways you can use to communicate.
The primary means of communicating is by the mailing list:
http://groups.google.com/group/specto

The importance of knowing what each other does
..............................................

As a project progresses, things can get pretty sticky. Kind of like the random
(/b/) board on 4chan, without the sauce. In order to minimize confusion,
everytime you wish to start hacking on a specific part of Specto, assign it to
yourself if it's a bug or feature request. This way, everyone knows what you
are up to, and can avoid touching a particular module if the changes are too
significant, or, if you request help, may come over and help.
We recommend a rainy Saturday night and good music.

In addition to assigning the task to yourself, you should ask the other
developpers on jabber or in the google group.

Ways of contributing
--------------------

- Hacking code
- Filing bug reports ("issues")
- Writing documentation and keeping this wiki up to date for developers
- Translating Specto into your language
- Suggesting brilliant cracktastic ideas

How to contribute code with a patch
...................................

You can use bazaar if you have a local branch of Specto::

    bzr commit -m "short description of the changes"

For translators a commit message could be::

    bzr commit -m "$LANG: Updated translation"

Now to create a patch out of the latest change::

    bzr send lp:specto -o short_description.patch

Otherwise you can send the patch, or the whole file in case of
translations, to the address: nekohayo _at_ gmail.com

Tools of the Trade
------------------

Of course, you are absolutely free to use whatever you want to help Specto,
but here are just a few hints of software we recommend if you have no idea
what you should use.

A computer running Linux, with all the dependencies satisfied:

- bzr (Bazaar) for access to the latest version at any time
- A text editor for coding (emacs, vim, Gedit, Bluefish, SPE, whatever)
- Meld for viewing changes between files of different versions. Very useful,
  and has a feature to work with bzr.
- A Google account if you want to manage bugs in the issue tracker
- A Launchpad account if you want to host your own bazaar branch of the code on
  https://code.launchpad.net/specto

Coding style
------------

You must use four (4) spaces instead of tabs to indent the code.

PEP-8 style compliance
......................

All your patches and commits should be conforming to the Python PEP-8 style
guide: http://www.python.org/dev/peps/pep-0008/
The exception is for line lengths. We don't require lines to be wrapped at
79 columns. They are smoking crack. To check the code for compliance, you can
download http://svn.browsershots.org/trunk/devtools/pep8/pep8.py and run it
with the "--ignore=E501" parameter.

todo: suggest to use pylint as code static checker

Comments and documentation
..........................

Try to comment as much as possible, meaning that you should add comments for
anything that you feel might be confusing for others, to document special
workarounds, etc. Normal comments use the # symbol before the comment (see
also the PEP-8 guidelines on how to do spacing around it). When you feel some
feature needs to be added, add #TODO: before the comment. When you see or
predict a bug in a certain area, use the #FIXME: comment style instead.
Do not forget to actually file an issue about it.

See also: `Terminology`_



The code must remain anonymous
..............................

Do not sign your name or nickname at the top of the code or inside the code.
This is a community rule, for the following reasons:

- Signatures quickly become irrelevant (as an example here: a developer that no
  longer maintains any modules, and has not touched the code/project for over a
  year)
- They scare people off because they look like a territory mark; when someone
  is about to modify that code (be that a new contributor or a veteran), that
  contributor will certainly feel "am I stepping on somebody's toes? maybe
  I'm not supposed to touch this? what if I awaken the Mummy?"
- That signature gives no idea of the size of the contribution that person did,
  or the amount of code you need to (re)write to get your name on a file

Instead, your name can go in the AUTHORS file when you commit some significant
changes. If you don't have the means/will to make your own branch and are
providing a patch, we will be committing your patch and mentionning your name
using the "--author" feature of Bazaar.


Do not make modules talk to others directly
...........................................

In specto, everything is managed by main.py. As it is the central module,
you must use it if you need to communicate to other modules. Main.py is the
one who must do the job, NOT your specific module. For example, if we have
dish.py who feels it needs to be washed, it must not ask dishwasher.py to be
washed. It must ask main.py, which in turn will ask dishwasher.py to do the
washing.

Encoding
........

The default encoding for all documents is utf-8 (case is important).
In a Python file, this is done with a line like this at the top::

  # -*- coding: utf-8 -*-


Do not break Main
.................

The specto-main development branch is intended as a "stable" development branch.
Only small and carefully tested bug fixes should be committed directly to it.
Long-duration development is to be done in individual branches, which will be
merged periodically or on request when they have been heavily tested and found
to cause no regressions compared to Main. Thus, one can work on refactoring,
or a new incomplete feature, in a separate bazaar branch, without breaking the
stability of Specto's main development branch for the users who depend on it.
Also, in normal circumstances, you should start your individual branch by
"branching" off from specto-main, and merge only from main instead of other
individual branches.


Localization
============

Specto is translated using ``gettext`` and ``intltool``. Translation messages
are located in the ``po/`` directory.

Create a new translation
------------------------

Go into the directory ``po``:

1. Add the language code ``$LANG`` to the file ``LINGUAS``
2. Run ``intltool-update --pot`` and copy ``untitled.pot`` to ``$LANG.po``
3. Edit and check the whole file header:

   + Add yourself as author
   + Check ``plurals``

Fill in the charset used; Recommended encoding is utf-8.
When the header is filled-in, go to `Update or check an existing translation`_

Update or check an existing translation
---------------------------------------

Go to your Specto source directory.

Go to the translation directory ``po``::

   cd po/

To update and check the translation file, run::

   intltool-update $LANG

Now check and edit ``$LANG.po``.

Continue running ``intltool-update $LANG`` and check that you have 0 fuzzy and
0 untranslated, then you are finished.

You can send the translation to a repository, or as a patch, please
refer to `How to contribute code with a patch`_


Copyright
=========

The program Specto is released under the `GNU General Public Licence v2`:t:
(or at your option, any later version). Please see the main program file for
more information.

Specto © 2005-2010, Jean-François Fortin Tam and Wout Clymans

This documentation is released under the same terms as the main program.
The documentation sources are available inside the Specto source distribution.

.. View this document as PDF with::
      rst2pdf Manual.rst && xdg-open Manual.pdf
