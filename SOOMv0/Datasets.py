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
# $Id: Datasets.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Datasets.py,v $

import os
import cPickle
import errno
from SOOMv0.Soom import soom
from SOOMv0.Dataset import Dataset
from SOOMv0.common import *

class Datasets:
    """
    A container for loaded datasets
    """

    def __init__(self):
        self.datasets = {}

    def _dsload(self, dsname, path):
        try:
            return self.datasets[dsname.lower()]
        except KeyError:
            pass
        metadata_file = os.path.join(dsname, soom.metadata_filename)
        path = soom.object_path(metadata_file, path)
        if not path:
            raise DatasetNotFound('Unknown dataset %r' % dsname)
        f = open(os.path.join(path, metadata_file), 'rb')
        try:
            ds = cPickle.load(f)
        finally:
            f.close()
        soom.info('Dataset %r loaded.' % dsname)
        if (hasattr(ds, 'soom_version_info') 
            and ds.soom_version_info[:2] != version_info[:2]):
            soom.warning('Dataset created by SOOM %s, this is SOOM %s' %\
                         (ds.soom_version, version))
        ds.load_notify(path)
        self.datasets[dsname.lower()] = ds
        return ds

    def dsload(self, dsname, path=None):
        """
        Function to load a stored data set definition (but not all
        its data) from disc. The data is loaded column by column only
        as required. The function returns a DataSet object instance.
        """
        ds = self._dsload(dsname, path)
        # now load all the columns if soom.lazy_column_loading is turned off
        if not soom.lazy_column_loading:
            soom.info('Loading columns for dataset %r' % ds.name)
            for col in ds.get_columns():
                col.load('data')
                col.load('inverted')
        return ds

    def dsunload(self, dsname):
        """Unloads datasets"""
        if isinstance(dsname, Dataset):
            dsname = dsname.name
        try:
            ds = self.datasets.pop(dsname.lower())
        except KeyError:
            pass
        else:
            ds.unload()
            soom.info('Dataset %r unloaded.' % dsname)

    def makedataset(self, dsname, path=None, **kwargs):
        """
        Factory function to create a new DataSet instance (inheriting
        metadata from any existing dataset with the same name). The
        returned dataset is locked for update.
        """
        kwargs['backed'] = True
        try:
            ds = self._dsload(dsname, path)
        except DatasetNotFound:
            ds = Dataset(dsname, **kwargs)
            ds.lock()
            soom.info('Dataset %r created.' % dsname)
        else:
            ds.lock()
            ds.new_generation()
        self.datasets[dsname.lower()] = ds
        return ds

    def subset(self, ds, subsetname, label=None, **kwargs):
        subset = ds.subset(subsetname, label=label, **kwargs)
        self.datasets[subset.name.lower()] = subset
        return subset

    def __str__(self):
        """Prints information about current loaded SOOM datasets/objects"""
        # To-do: print information about unloaded SOOM datasets present in the
        # default_object_path
        rep = ['SOOM datasets currently loaded:']
        if self.datasets:
            for ds in self.datasets.values():
                rep.append('    %s (%s)' % (ds.name, ds.label))
        else:
            rep.append('    None')
        return '\n'.join(rep)

    def _display_hook(self):
        print str(self)

