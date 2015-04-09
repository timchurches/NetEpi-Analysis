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
# $Id: BaseDataset.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/BaseDataset.py,v $

from mx import DateTime

from SOOMv0.common import *
from SOOMv0.Soom import soom
from SOOMv0.DatasetColumn import is_dataset_col, get_dataset_col, RowOrdinalColumn
from SOOMv0.Describe import Describe
from SOOMv0.PrintDataset import DSFormatter

class BaseDataset(object):
    """
    Base class for data set definition

    Keyword arguments include:
        name, label, desc, path, backed, rowsas, printcols, nonprintcols,
        weightcol, generations, date_created, date_updated.

    Attributes:
        name            data set name
        label           Longer descriptive label for this dataset
        desc            Full description of this dataset
        path            Path to saved datasets
        backed          if true, dataset backed by disk files,
                        otherwise kept in memory.
        summary         dataset is summarised
        rowsas          return rows as a dict or list or tuple? 
                        'dict' is used by default.
        printcols       column names to return in each row when 
                        printing
        nonprintcols    column names not to be returned in each 
                        row when printing
        weightcol       default weighting column
        generations     The number of past dataset generations to keep.
        generation      Update generation count
        date_created    When the dataset was first created (mx.DateTime)
        date_updated    When the dataset was last updated
        length          Number of records in the dataset (use len(ds) instead)

    """
    filter_label = None

    def __init__(self, name, label=None, desc=None,
                 weightcol=None,
                 summary=False,
                 printcols=None, nonprintcols=None,
                 date_created=None, date_updated=None):
        soom.check_name_ok(name, 'Dataset')
        self.name = name
        self.label = label
        self.desc = desc
        self.backed = False
        self.summary = summary
        self.weightcol = weightcol
        self.printcols = printcols
        self.nonprintcols = nonprintcols
        if date_created is None:
            date_created = DateTime.now()
        self.date_created = date_created
        if date_updated is None:
            date_updated = DateTime.now()
        self.date_updated = date_updated
        self.clear()

    attrs = (
        'name', 'label', 'desc', 'weightcol', 'printcols', 'nonprintcols',
        'date_created', 'date_updated',
    )
    def get_metadata(self):
        m = {}
        for attr in self.attrs:
            m[attr] = getattr(self, attr)
        return m

    def is_summarised(self):
        return bool(getattr(self, 'summary', False))

    def clear(self):
        """
        Clear columns without erasing metadata - also called to
        initialise new dataset objects.
        """
        self.soom_version = version
        self.soom_version_info = version_info
        self._column_ord = []
        self._column_dict = {}
        self.length = 0
        # add the row_ordinal column as the very first column
        self.addcolumn(RowOrdinalColumn(self))

    def rename_dataset(self, newname):
        """
        Rename the dataset
        """
        soom.check_name_ok(name, 'Dataset')
        self.name = newname

    def delete_dataset(self):
        pass

    def rename_column(self, oldname, newname):
        try:
            col = self._column_dict.pop(oldname)
        except KeyError:
            raise Error('Unknown column %r' % (oldname,))
        col.rename_column(newname)
        self._column_dict[col.name] = col

    def delete_column(self, name):
        """
        Remove a column from a Dataset
        """
        try:
            col = self._column_dict.pop(name)
        except KeyError:
            raise Error('Unknown column %r' % (name,))
        self._column_ord.remove(col)
        col.delete_column()

    def addcolumn(self, name, **kwargs):
        if is_dataset_col(name):
            col = name
        else:
            col = get_dataset_col(self, name, **kwargs)
        try:
            self.delete_column(col.name)
        except Error:
            pass
        self._column_ord.append(col)
        self._column_dict[col.name] = col
        return col

    def addcolumnfromseq(self, name, data, mask=None, **kwargs):
        """
        Creates a new column from a supplied vector (sequence)
        or iterable.
        """
        # now create the DatasetColumn instance to hold the actual data
        # create the instance for the new column
        col = get_dataset_col(self, name, **kwargs)
        try:
            col_len = len(data)
        except TypeError:
            # because data vector may be an iterable, rather than a list
            pass
        else:
            if self.length == 0:
                self.length = col_len
            else:
                if self.length != col_len:
                    raise Error('The length (%d) of the data vector '
                                'supplied for column %r does not equal '
                                'the length of other columns in the '
                                'dataset (%d).' % 
                                            (col_len, name, self.length))
        col.store_column(data, mask)
        return self.addcolumn(col)


    def get_column(self, name):
        try:
            return self._column_dict[name]
        except KeyError:
            raise ColumnNotFound('Unknown column %r' % (name,))

    def has_column(self, name):
        return name in self._column_dict

    def get_columns(self, names = None):
        if names is not None:
            return [self.get_column(n) for n in names]
        else:
            return list(self._column_ord)

    def get_column_names(self):
        return [col.name for col in self._column_ord]

    def get_print_columns(self):
        cols = self.get_columns(self.printcols)
        if self.nonprintcols:
            cols = [col for col in cols if col.name not in self.nonprintcols]
        return cols

    def get_print_column_names(self):
        return [col.name for col in self.get_print_columns()]

    def __len__(self):
        return self.length


    def __getitem__(self, index_or_slice):
        if isinstance(index_or_slice, basestring):
            try:
                return self._column_dict[index_or_slice]
            except KeyError:
                raise KeyError(index_or_slice)
        if isinstance(index_or_slice, slice):
            from SOOMv0.Filter import sliced_ds
            return sliced_ds(self, index_or_slice)
        return dict([(col.name, col.do_outtrans(col[index_or_slice]))
                     for col in self.get_print_columns()])

    def describe(self, detail=ALL_DETAIL, date_fmt=None):
        """
        Return a description of the dataset as a Description object.

        "detail" controls what is included, and should take one of
        the following values:

            NO_DETAIL           dataset label, date and active filter 
            SOME_DETAIL         metadata for naive users
            ALL_DETAIL          metadata for expert users/dataset admins
        """

        if date_fmt is None:
            date_fmt = '%Y-%m-%d %H:%M:%S'
        d = Describe(detail, 'name', 'prov', 'ds', 'cols')
        if detail < SOME_DETAIL:
            d.add('name', NO_DETAIL, 'Dataset', self.label or self.name)
        else:
            d.add('name', NO_DETAIL, 'Name', self.name)
            d.add('name', NO_DETAIL, 'Label', self.label)
        d.add('ds', SOME_DETAIL, 'Description', self.desc)
        d.add('ds', SOME_DETAIL, 'Record Count', len(self))
        if self.weightcol:
            col = self.get_column(self.weightcol)
            desc = '%s (%s)' % (col.name, col.label)
            d.add('ds', SOME_DETAIL, 'Default weighting column', desc)
        if self.date_updated is not None:
            d.add('ds', SUB_DETAIL, 'Updated', 
                    self.date_updated.strftime(date_fmt))
        if self.date_created is not None:
            d.add('ds', SOME_DETAIL, 'Created', 
                    self.date_created.strftime(date_fmt))
        return d

    def short_description(self):
        return str(self.describe(NO_DETAIL))
    
    def describe_cols(self, sortby='label'):
        """
        Collect short-form column metadata as a list of lists.
        """
        colslabel = None
        colsmeta = None
        cols = [(getattr(col, sortby), col) for col in self.get_columns()]
        cols.sort()
        for sortbyval, col in cols:
            meta = col.describe(NO_DETAIL).describe_tuples()
            if colslabel is None:
                colslabel = [m[0] for m in meta]
                colsmeta = [[] for m in meta]
            for colmeta, (label, value) in zip(colsmeta, meta):
                colmeta.append(str(value))
        return colslabel, colsmeta

    def describe_with_cols(self):
        lines = ['%s: %s' % kv for kv in self.describe().describe_tuples()]
        lines.append("Containing the following columns:")
        colslabel, colsmeta = self.describe_cols(sortby = 'name')
        # Shove the column label at the top of the metadata columns
        for collabel, colmeta in zip(colslabel, colsmeta):
            colmeta.insert(0, collabel)
        # Determine maximum column width for each column
        colwidths = [max([len(v) for v in colmeta]) for colmeta in colsmeta]
        # Rotate data from list per column to tuple per row
        metabyrows = zip(*colsmeta)
        # Insert a ruler line
        metabyrows.insert(1, ['-' * w for w in colwidths])
        # Now format up the rows
        for rowvals in metabyrows:
            line = ' '.join([val.ljust(width)
                             for width, val in zip(colwidths, rowvals)])
            lines.append(line)
        return '\n'.join(lines)

    def _display_hook(self):
        if self.is_summarised():
            print self
        else:
            print self.describe_with_cols()

    def print_cols(self, *cols):
        if not cols:
            cols = None
        return '\n'.join(DSFormatter(self, cols))

    def __str__(self):
        """Prints a DataSet instance contents"""
        return self.print_cols()

    def show(self, *args):
        for line in DSFormatter(self, args):
            print line

    def summ(self, *args, **kwargs):
        from SOOMv0.DatasetSummary import summ
        return summ(self, *args, **kwargs)

    def filter(self, expr=None, **kwargs):
        from SOOMv0.Filter import filter_dataset
        return filter_dataset(self, expr=expr, **kwargs)

    def crosstab(self, shaped_like=None):
        from SOOMv0.CrossTab import CrossTab
        if not self.summary:
            raise Error('dataset must contain summary data')
        return CrossTab.from_summset(self, shaped_like)
