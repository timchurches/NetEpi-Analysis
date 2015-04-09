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
# $Id: make_icd9cm_fmt.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/loaders/make_icd9cm_fmt.py,v $

# Standard Python Libraries
import zipfile
import os

# Project modules
import urlfetch
import rtfparse

srcfiles = [
    'ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD9-CM/2002/Ptab03.ZIP',
    'ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD9-CM/2002/Dtab03.ZIP',
]


def fetch(datadir, url):
    dstfile = os.path.join(datadir, os.path.basename(url))
    print 'Fetching %s from %s' % (dstfile, url)
    urlfetch.fetch(url, dstfile)
    return dstfile


def extract(icd9_map, node):
    """
    Find groups containing a bookmark, and extract first two text
    nodes.  This relies on the structure of the source RTF files
    being stable - good enough for now.
    """

    def child_has_bookmark(node):
        if node.token == rtfparse.GROUP:
            for child in node.children:
                if (child.token == rtfparse.CWORD 
                    and child.args[0] == 'bkmkstart'):
                    return True
        return False

    # States
    SEEKING, FOUND, NEXT = range(3)
    state = SEEKING
    for child in node.children:
        if child.token == rtfparse.TEXT:
            text = child.args.strip()
        if state == SEEKING and child_has_bookmark(child):
            state = FOUND
        elif state == FOUND and child.token == rtfparse.TEXT and text:
            code = text
            state = NEXT
        elif state == NEXT and child.token == rtfparse.TEXT and text:
            icd9_map[code] = '%s - %s' % (code, text)
            state = SEEKING
        if child.token == rtfparse.GROUP:
            extract(icd9_map, child)


def make_icd9cm_fmt(datadir, verbose = False):
    icd9cm_fmt = {}
    for url in srcfiles:
        fn = fetch(datadir, url)

        if verbose: print 'Decompressing %s' % fn
        zf = zipfile.ZipFile(fn)
        try:
            first_member = zf.namelist()[0]
            data = zf.read(first_member)
        finally:
            zf.close()

        if verbose: print 'Parsing %s' % fn
        root = rtfparse.parse(data)
        del data

        if verbose: print 'Extracting %s' % fn
        extract(icd9cm_fmt, root)
    return icd9cm_fmt

if __name__ == '__main__':
    import optparse
    import cPickle

    p = optparse.OptionParser()
    p.add_option('-d', '--dl-dir', dest='datadir',
                 help='download directory', default='.')
    p.add_option('-v', '--verbose', dest='verbose', action='store_true',
                 help='verbose', default=False)
    options, args = p.parse_args()
    try:
        outfile, = args
    except ValueError:
        p.error('specify output filename')
    icd9cm = make_icd9cm_fmt(options.datadir, options.verbose)

    if options.verbose: print 'Writing %s' % outfile
    f = open(outfile, 'wb')
    try:
        cPickle.dump(icd9cm, f, -1)
    finally:
        f.close()
