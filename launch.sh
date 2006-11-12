#!/bin/sh
cd `dirname $0`/src
exec python specto.py $@
