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
import os
import sys
import errno
import tempfile
import urllib2

def fetch(url, filename):
    if os.path.exists(filename):
        print ' %s: using existing file' % filename
        return

    dirname = os.path.dirname(filename)
    if dirname:
        try:
            os.makedirs(dirname, 0755)
        except OSError, (eno, estr):
            if eno != errno.EEXIST:
                raise
    try:
        u = urllib2.urlopen(url)
        try:
            url_len = None
            info = u.info()
            if info.has_key('content-length'):
                url_len = long(info['content-length'])
            f, fn = tempfile.mkstemp('.tmp', '.', os.path.dirname(filename))
            try:
                cnt = 0
                while 1:
                    buf = u.read(16384)
                    if not buf:
                        break
                    os.write(f, buf)
                    cnt += len(buf)
                    if url_len:
                        sys.stderr.write(' %s %.2fMB %d%%\r' %\
                            (filename, float(cnt) / 1024 / 1024,
                            cnt * 100 / url_len))
                    else:
                        sys.stderr.write(' %s %.2fMB\r' %\
                            (filename, float(cnt) / 1024 / 1024))
                os.rename(fn, filename)
                sys.stderr.write(' %s %.2fMB     \n' %\
                        (filename, float(cnt) / 1024 / 1024))
                return cnt
            finally:
                try:
                    os.unlink(fn)
                except OSError:
                    pass
        finally:
            try:
                u.close()
            except:
                pass

    except urllib2.URLError, e:
        print '\n %s: %s' % (url, e)
        sys.exit(1)
    except (IOError, OSError), e:
        print '\n %s: %s' % (filename, e)
        sys.exit(1)
