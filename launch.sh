#!/bin/sh
cd `dirname $0`
PYTHONPATH=$PYTHONPATH:src ./specto $@
