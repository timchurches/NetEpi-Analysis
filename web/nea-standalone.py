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
# $Id: nea-standalone.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/nea-standalone.py,v $

import os
import sys
import optparse
from albatross import httpdapp

from SOOMv0 import soom


appdir = os.path.abspath(os.path.dirname(__file__))
default_dynamic_dir = os.path.join(appdir, 'dynamic')
default_static_dir = os.path.join(appdir, 'static')
default_data_dir = appdir

if __name__ == '__main__':
    sys.path.append(appdir)

    opt_parse = optparse.OptionParser()
    opt_parse.add_option('-p', '--port', 
                         type='int', dest='port', default=8080,
                         help='listen on PORT (default: 8080)')
    opt_parse.add_option('-S', '--soompath', 
                         dest='soompath', 
                         default='SOOM_objects:../SOOM_objects',
                         help='SOOM search path')
    opt_parse.add_option('-N', '--appname',
                         dest='appname', default='nea',
                         help='application name (effects paths)')
    opt_parse.add_option('-T', '--apptitle',
                         dest='apptitle', 
                         default='NetEpi Analysis',
                         help='web application title')
    opt_parse.add_option('--session-secret',
                         dest='session_secret', 
                         help='Session signing secret')
    opt_parse.add_option('--datadir',
                         dest='data_dir', default=default_data_dir,
                         help='A writeable directory NOT published by '
                              'the web server (contains private data)')
    opt_parse.add_option('--dynamicdir',
                         dest='dynamic_target', default=default_dynamic_dir,
                         help='A writeable directory published by '
                              'the web server, contains files generated '
                              'by the application')
    opt_parse.add_option('--staticdir',
                         dest='static_target', default=default_static_dir,
                         help='A UNwritable directory published by '
                              'the web server, contains static content '
                              'used by the application (css, images)')
    options, args = opt_parse.parse_args()
    if not options.session_secret:
        import binascii
        f = open('/dev/urandom', 'rb')
        try:
            data = f.read(32)
        finally:
            f.close()
        options.session_secret = binascii.b2a_base64(data).rstrip()

    static_resources = [
        ('/nea/dynamic', options.dynamic_target),
        ('/nea', options.static_target),
    ]
    sys.modules['config'] = options             # XXX Dodgy - "import config"

    # Create the HTTP server and serve requests.
    from nea import app
    httpd = httpdapp.HTTPServer(app, options.port, 
                                static_resources = static_resources)
    httpd.serve_forever()
