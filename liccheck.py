#!/usr/bin/env python
#
# This tool checks that all .py and .html files contain the following license
# header text:

"""\
    The contents of this file are subject to the HACOS License Version 1.2
    (the "License"); you may not use this file except in compliance with
    the License.  Software distributed under the License is distributed
    on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
    implied. See the LICENSE file for the specific language governing
    rights and limitations under the License.  The Original Software
    is "NetEpi Analysis". The Initial Developer of the Original
    Software is the Health Administration Corporation, incorporated in
    the State of New South Wales, Australia.

    Copyright (C) 2004,2005 Health Administration Corporation.
    All Rights Reserved.
"""

import sys
import os
import re

# Check all files with these extensions
check_exts = '.py', '.pyx', '.html', '.c', '.h', '.tex', '.sas'
# Additional files to check
extras = [
    'TODO',
    'SOOMv0/soomparse.g',
]
# Ignore listed files
ignore = [
    'SOOMv0/yappsrt.py',                # YAPPS2 run-time
    'web/static/copyright.html',        # Contains the full LICENSE
    'SOOMv0/Cstats.pyx',                # Mixed LICENSE
]
ignore_dirs = [
    'build',
    'yapps2',
]

filt_re = re.compile(r'(^(%|#|--|[ \t]+\*)?[ \t]*)|([ \t\r;]+$)', re.MULTILINE)

exit_status = 0

def strip(buf):
    return filt_re.sub('', buf)

def check(filepath, want):
    f = open(filepath)
    try:
        head = f.read(2048)
    finally:
        f.close()
    if strip(head).find(want) < 0:
        global exit_status
        exit_status = 1
        print filepath


want = strip(__doc__)
for filepath in extras:
    check(filepath, want)
for dirpath, dirnames, filenames in os.walk('.'):
    dirnames[:] = [dirname 
                   for dirname in dirnames 
                   if dirname not in ignore_dirs]
    for filename in filenames:
        for ext in check_exts:
            if filename.endswith(ext):
                break
        else:
            continue
        filepath = os.path.normpath(os.path.join(dirpath, filename))
        if filepath in ignore:
            continue
        check(filepath, want)
sys.exit(exit_status)
