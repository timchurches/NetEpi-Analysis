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
"""
Classes to define DataSets and their columns. Each Dataset instance
contains a number of DatasetColumn instances, which hold both
metadata about themselves (no separate metadata class for columns
any more) as well as their actual data and inverted indexes on it.
"""
# $Id: Dataset.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Dataset.py,v $

import sys
import os
import cPickle
import time
import tempfile
import fcntl
import errno
import shutil
from mx import DateTime
from MA import Numeric
from SOOMv0.Soom import soom
from SOOMv0 import Utils
from SOOMv0.BaseDataset import BaseDataset
from SOOMv0.DatasetSummary import Summarise
from SOOMv0.DatasetColumn import get_dataset_col
from SOOMv0.Filter import DatasetFilters, sliced_ds
from SOOMv0.ChunkingLoader import ChunkingLoader
from soomarray import ArrayDict
from SOOMv0.SummaryStats import stat_method_help
from SOOMv0.common import *


__all__ = 'Dataset',

class Dataset(BaseDataset):
    def __init__(self, name, 
                 label=None, desc=None, path=None,
                 backed = False, 
                 rowsas = 'dict', 
                 generations = 24, **kwargs):
        self.generation = 0
        self.locked = False
        self.generations = generations
        self.path = path
        BaseDataset.__init__(self, name, label, desc, **kwargs)
        self.backed = backed
        self.rowsas = rowsas
        self.filters = DatasetFilters(self)

    def __getstate__(self):
        odict = self.__dict__.copy() # copy the dict since we may be changing it
        odict['locked'] = False
        odict['filters'] = None
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.filters = DatasetFilters(self)

    def load_notify(self, path):
        self.path = path
        self.filters.load_metadata()

    def object_path(self, object_name, mkdirs=False, gen=False, *names):
        if gen:
            path = os.path.join(self.path, self.name, 
                                str(self.generation), object_name)
        else:
            path = os.path.join(self.path, self.name, object_name)
        if mkdirs:
            Utils.helpful_mkdir(os.path.dirname(path))
        return path

    def lock(self):
        if not soom.writepath:
            raise Error('soom.writepath not set, cannot lock dataset')
        if not self.locked:
            self.path = soom.writepath
            Utils.helpful_mkdir(os.path.join(self.path, self.name))
            lock_file_name = os.path.join(self.path, self.name, '.update_lck')
            fd = os.open(lock_file_name, os.O_WRONLY|os.O_CREAT, 0666)
            try:
                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError, (eno, estr):
                os.close(fd)
                if eno in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK):
                    raise Error('Dataset already locked')
                raise
            self.locked, self._lock_fd = True, fd

    def unlock(self):
        if self.locked:
            os.close(self._lock_fd)
            self.locked = False
            del self._lock_fd

    def assert_locked(self):
        if self.backed and not self.locked:
            raise Error('dataset must be locked for this operation')

    def new_generation(self):
        if self.backed:
            self.assert_locked()
        BaseDataset.clear(self)
        self.date_created = DateTime.now()
        self.generation += 1
        if self.backed:
            if self.generation - self.generations >= 0:
                gendir = os.path.join(self.path, self.name,
                                    str(self.generation - self.generations))
                shutil.rmtree(gendir, ignore_errors=True)

    def rename_dataset(self, newname):
        self.assert_locked()
        BaseDataset.rename_dataset(newname)
        os.rename(os.path.join(self.path, self.name),
                  os.path.join(self.path, newname))
        self.save()

    def delete_dataset(self):
        # XXX Future work
        raise NotImplementedError

    def save(self):
        if self.locked and soom.writepath:
            self.date_updated = DateTime.now()
            self.path = soom.writepath
            Utils.helpful_mkdir(os.path.join(self.path, self.name))
            fd, filename = tempfile.mkstemp('', '.soom', self.path)
            try:
                # We could use dumps() and os.write, but cPickle.dumps()
                # uses cStringIO, which seems like a waste.
                f = os.fdopen(fd, 'w+b')
                try:
                    cPickle.dump(self, f, -1)
                finally:
                    f.close()
                real_filename = self.object_path(soom.metadata_filename)
                os.chmod(filename, 0444)
                os.rename(filename, real_filename)
                soom.info('Dataset %r saved to filename %s' %\
                          (self.name, real_filename))
            finally:
                try:
                    os.close(fd)
                except OSError:
                    pass
                try:
                    os.unlink(filename)
                except OSError:
                    pass
        else:
            raise Error("No lock on dataset %r or no soom.writepath - not saved." % self.name)

    def derivedcolumn(self, dername, 
                      dercols=None, derargs=None, derfunc=None, **kwargs):
        """
        Method to create a new, derived (calculated) column, using
        a supplied function and other columns as arguments.
        """
        st = time.time()
        data = derfunc(*[self.get_column(name).data for name in dercols])
        dt = time.time()
        if isinstance(data, tuple) and len(data) == 2:
            data, mask = data
        else:
            mask = None
        col = self.addcolumnfromseq(dername, data, mask, **kwargs)
        for name in dercols:
            # Contain memory usage
            self.get_column(name).unload()
        et = time.time()
        if (dt - st) < 0.001:
            soom.info('Creating and storing derived column %s in dataset %s took %.3f' %\
                      (dername, self.name, et - st))
        else:
            soom.info('Creating derived column %s in dataset %s took %.3f, store took %.3f' %\
                    (dername, self.name, dt - st, et - dt))
        soom.mem_report()
        return col

    def describe(self, detail=ALL_DETAIL, date_fmt=None):
        d = BaseDataset.describe(self, detail, date_fmt=date_fmt)
        d.add('ds', SOME_DETAIL, 'Disc backed', yesno(self.backed))
        if self.backed and hasattr(self, 'path'):
            d.add('ds', SOME_DETAIL, 'Path', self.path)
        d.add('ds', SOME_DETAIL, 'Generation', self.generation)
        d.add('ds', SOME_DETAIL, 'Generations retained', self.generations)
        d.add('ds', SOME_DETAIL, 'Created by SOOM version', self.soom_version)
        return d

    def __getitem__(self, index):
        if type(index) is int:
            return dict([(col.name, col.do_outtrans(col[index]))
                         for col in self.get_print_columns()])
        elif type(index) is slice:
            return sliced_ds(self, index)
        else:
            try:
                return self._column_dict[index]
            except KeyError:
                raise KeyError(index)

    def unload(self):
        """Unload data and inverted forks for all columns."""
        for col in self.get_columns():
            col.unload()

    def filter(self, expr=None, **kwargs):
        """Create a new (optionally named) dataset filter"""
        return self.filters.filter(expr=expr, **kwargs)

    def makefilter(self, name, expr, **kwargs):
        """Legacy filter interface - use ds.filter(...) instead"""
        return self.filters.filter(name=name, expr=expr, **kwargs)

    def delfilter(self, filtername):
        """
        Method to remove a filter's metadata and record_ids from
        a DataSet.
        """
        self.filters.delete(filtername)

    def load_filter(self,filtername):
        """
        Function to load a filter vector for a data set.
        """
        try:
            self.filters[filtername]
        except KeyError:
            raise Error('load_filter(): no filter %r' % filtername)

    def initialise(self):
        """
        Method to initialise a DataSet's chunking loader before
        loading data into it.
        """
        if not self.locked:
            raise Error('dataset must be locked for this operation')
        if self.length > 0:
            raise Error('dataset must be empty for this operation')
        chunkdir = self.object_path('chunks', mkdirs=True)
        Utils.helpful_mkdir(chunkdir)
        self._chunking_loader = ChunkingLoader(self.get_columns(), chunkdir)

    def finalise(self):
        """
        Method to finalise the loading of a DataSet - it re-processes
        all the chunks on a column-by-column basis into their final
        form as Numpy arrays.
        """
        starttime = time.time() # a slowish operation so lets time it
        self.length = self._chunking_loader.rownum
        nproc = soom.nproc
        if nproc < 2:
            for col, data in self._chunking_loader.unchunk_columns():
                try:
                    col.store_column(data)
                except:
                    print >> sys.stderr, 'While processing column %r:' % col.name
                    raise
        else:
            running = 0
            for col, data in self._chunking_loader.unchunk_columns():
                if running == nproc:
                    pid, status = os.wait()
                    if not os.WIFEXITED(status) or os.WEXITSTATUS(status):
                        sys.exit(1)
                    running -= 1
                pid = os.fork()
                if not pid:
                    try:
                        try:
                            col.store_column(data)
                            os._exit(0)
                        except:
                            print >> sys.stderr, 'While processing column %r:' % col.name
                            raise
                    finally:
                        os._exit(1)
                else:
                    running += 1
                    col.unload()
            while 1:
                try:
                    pid, status = os.wait()
                except OSError, (eno, estr):
                    if eno == errno.ECHILD:
                        break
                    raise

        del self._chunking_loader
        stoptime = time.time() # how long did that take?
        elapsed = stoptime - starttime

    def loaddata(self,datasource,initialise=0,finalise=0,
                 rowlimit=None,chunkrows=0):
        """
        Method to load rows of data into a DataSet instance - calls
        initialise(), then iterates across rows, then calls finalise.
        """
        if initialise: # if we should initialise the DataSet object, then do so
            self.initialise()
        datasource.register_dataset_types(self.get_columns())
        self.length = self._chunking_loader.loadrows(datasource, 
                                                    chunkrows, rowlimit)
        if finalise: # this is the last data source to be added to this DataSet
            self.finalise() # invoke finalise method
        # yup TO DO: parallelisation of data set loading


    # AM - Subsetting is currently not functional. Filtered Datasets should
    # largely replace them. At some future point, the ability to deep copy 
    # datasets will be added (but first we need per-user workspaces).
#    def subset(self, subsetname, label=None, keepcols=None, **kwargs):
#        """
#        This method creates a complete physical subset of a
#        DataSet, both row-wise using a filter and column-wise
#        if required.  It should really use a subclass of Dataset,
#        which incorporates extra metadata about where the Subset
#        was subsetted from.  The principle is that every data object
#        (including filters etc) should know where it came from, so
#        it can update itself if its parent(s) have updated themselves
#        (as well as for data documentation/audit trail purposes).
#        """
#        filterset = self.filters.filter_dataset(kwargs)
#        newsubset = Dataset(subsetname, label=label, **kwargs)
#        newsubset.all_record_ids = Numeric.arrayrange(len(filterset),
#                                                      typecode=Numeric.Int)
#        # This is bad - we should have a "make_column_from_column" method
#        # on the column class.
#        copy_attrs = ('label', 'all_value', 'all_label', 'datatype', 'coltype',
#                      'outtrans', 'use_outtrans', 'maxoutlen', 'missingvalues',
#                      'calculatedby' , 'calculatedargs')
#        for col in self.get_columns(keepcols):
#            try:
#                data = col.data.filled()
#                mask = col.data.mask()
#            except:
#                data = col.data
#                mask = None
#
#            colargs = dict([(attr, getattr(col, attr)) for attr in copy_attrs])
#            newsubset.addcolumnfromseq(col.name, data, mask, **colargs)
#        return newsubset


def load_filter(dataset,filtername):
    """
    Function to load a filter vector for a data set. Delegates to
    load_filter method of the DataSet class
    """
    return dataset.load_filter(filtername)


class SummarisedDataset(Dataset):
    """
    A Dataset with some additional info about how the summary
    was generated.
    """
    def __init__(self, name, summ_label=None, filter_label=None, **kwargs):
        Dataset.__init__(self, name, summary=True, **kwargs)
        self.summ_label = summ_label
        self.filter_label = filter_label
        self.stat_methods = None

    def get_method_statcolname(self, method):
        return self.stat_methods.get_method_statcolname(method)

    def describe(self, detail=ALL_DETAIL, date_fmt=None):
        d = Dataset.describe(self, detail, date_fmt)
        d.add('prov', SUB_DETAIL, 'Filter', self.filter_label)
        d.add('prov', SOME_DETAIL, 'Summarised', self.summ_label)
        return d

