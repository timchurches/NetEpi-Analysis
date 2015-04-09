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
# $Id: ChunkingLoader.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/ChunkingLoader.py,v $

import os
import zlib
import cPickle
import time
from SOOMv0.Soom import soom

class ChunkingLoader:
    """
    "Rotate" row-wise data to column-wise.

    Do rotation on disk if number of rows is excessive
    """
    compress_chunk = True

    def __init__(self, columns, basepath):
        self.basepath = basepath
        self.columns = []
        self.numchunks = 0
        self.rownum = 0
        for col in columns:
            if col.name != 'row_ordinal':               # XXX
                self.columns.append((col, []))

    def _chunk_filename(self, colname, chunknum):
        return os.path.join(self.basepath, 
                            '%s_chunk_%s.SOOMchunk' % (colname, chunknum))

    def flush(self):
        starttime = time.time()
        for col, data in self.columns:
            fn = self._chunk_filename(col.name, self.numchunks)
            f = open(fn, 'wb')
            try:
                if self.compress_chunk:
                    f.write(zlib.compress(cPickle.dumps(data, -1)))
                else:
                    cPickle.dump(data, f, -1)
            finally:
                f.close()
            del data[:]
        soom.mem_report()
        soom.info('chunk flush took %.3f seconds' % (time.time() - starttime))
        self.numchunks += 1

    def get_chunk(self, colname, chunknum):
        filename = self._chunk_filename(colname, chunknum)
        f = open(filename, 'rb')
        try:
            if self.compress_chunk:
                return cPickle.loads(zlib.decompress(f.read()))
            else:
                return cPickle.load(f)
        finally:
            f.close()
            os.remove(filename)

    def loadrows(self, datasource, chunkrows = 0, rowlimit = 0):
        source_rownum = 0
        starttime = time.time()
        if not rowlimit:
            rowlimit = -1
        for row in datasource:
            source_rownum += 1
            for col, data in self.columns:
                data.append(row.get(col.name, None))
            self.rownum += 1
            if source_rownum == rowlimit:
                break
            if chunkrows and source_rownum and source_rownum % chunkrows == 0:
                self.flush()
            if source_rownum and source_rownum % 1000 == 0:
                soom.info('%s (%d total) rows read from source %s (%.1f per sec)' %\
                          (source_rownum, self.rownum, datasource.name, 
                           source_rownum / (time.time() - starttime)))
        self.flush()
        soom.info('%s rows read from DataSource %s, in %.3f seconds (%d rows total)' % (source_rownum, datasource.name, time.time() - starttime, self.rownum))
        return source_rownum

    def unchunk_columns(self):
        def _col_generator(self, col):
            for chunknum in xrange(self.numchunks):
                for v in self.get_chunk(col.name, chunknum):
                    yield v

        for col, data in self.columns:
            yield col, _col_generator(self, col)
