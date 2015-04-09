#
#   The contents of this file are subject to the HACOS License Version 1.2
#   (the "License"); you may not use this file except in compliance with
#   the License.  Software distributed under the License is distributed
#   on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
#   implied. See the LICENSE file for the specific language governing
#   rights and limitations under the License.  The Original Software
#   is "NetEpi Analysis". The Initial Developer of the Original
#   Software is the Health Administration Corporation, incorporated in
#   the State of New South Wales, Australia.
#
#   Copyright (C) 2004,2005 Health Administration Corporation. 
#   All Rights Reserved.
#
#
# $Id: setup.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/soomext/setup.py,v $

# To use:
#       python setup.py install
#

import distutils, os
from distutils.core import setup, Extension

setup(
    name = "NetEpi-Analysis-SOOM",
    version = "0.11",
    maintainer = "NSW Department of Health",
    maintainer_email = "Tim CHURCHES <TCHUR@doh.health.nsw.gov.au>",
    description = "NetEpi-Analysis SOOM Numpy Utilities",
    py_modules=["soomarray"],
    ext_modules = [Extension('soomfunc',
                             ['soomfunc.c']),
                   Extension('mmaparray',
                             ['mmaparray.c']),
                   Extension('blobstore',
                             ['blobstore.c', 'blob.c', 'storage.c'])
                   ],
    url = "http://netepi.info/",
    license = 'Health Administration Corporation Open Source License Version 1.2',
    )

