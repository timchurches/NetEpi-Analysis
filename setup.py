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
# To use:
#       python setup.py install
#
# $Id: setup.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/setup.py,v $

from SOOMv0.common import version
from distutils.core import setup

import sys
if 'sdist' in sys.argv:
    sys.argv.append('--force-manifest')

if 'bdist_rpm' in sys.argv:
    version = version.replace('-', '_')

setup(name = "NetEpi-Analysis",
    version = version,
    maintainer = "NSW Department of Health",
    maintainer_email = "Tim CHURCHES <TCHUR@doh.health.nsw.gov.au>",
    description = "Network-enabled tools for epidemiology and public health practice",
    url = "http://netepi.info/",
    packages = ['SOOMv0', 'SOOMv0.ColTypes', 'SOOMv0.Sources', 
                'SOOMv0.Plot', 'SOOMv0.Analysis'],
    license = 'Health Administration Corporation Open Source License Version 1.2',
)

