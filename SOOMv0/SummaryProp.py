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
# $Id: SummaryProp.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/SummaryProp.py,v $

"""
Calculate proportions of summary sets
"""

import copy
from SOOMv0 import common, Utils

_colname_prefix = '_prop_of_all-'

def proportion_label(dataset, colnames, marginal_colnames = None):
    """
    Given a dataset, a list of conditioning column names, and a
    list of marginal column names, return proportion column name
    and label.
    """
    if marginal_colnames is None:
        marginal_colnames = colnames
    if 0:
        if len(marginal_colnames) == len(colnames):
            label_parts = ['All']
        else:
            label_parts = []
            for colname in colnames:
                label = dataset[colname].label
                if colname in marginal_colnames:
                    label_parts.append('all ' + Utils.pluralise(label))
                else:
                    label_parts.append('same ' + label)

    if 1:
        label_parts = []
        for colname in colnames:
            label = dataset[colname].label
            if colname in marginal_colnames:
                label_parts.append('all ' + Utils.pluralise(label))

    if 0:
        if len(marginal_colnames) == len(colnames):
            label_parts = ['All']
        else:
            label_parts = []
            for colname in colnames:
                label = dataset[colname].label
                if colname not in marginal_colnames:
                    label_parts.append('same ' + label)

    return (_colname_prefix + '-'.join(marginal_colnames),
            'Propn. of ' + ', '.join(label_parts))
            

def _yield_prop_combos(summaryset, colnames):
    colnames = tuple(colnames)
    for a in range(len(colnames)):
        for non_marginal_colnames in Utils.xcombinations(colnames,a):
            marginal_colnames = list(colnames)          # copy or cast
            for d in non_marginal_colnames:
                marginal_colnames.remove(d) 
            yield marginal_colnames

def extract_propn_cols(name):
    """
    Given a propn column name, extract the names of the "All" columns
    """
    if name.startswith(_colname_prefix):
        return name[len(_colname_prefix):].split('-')

def propn_names_and_labels(dataset, colnames):
    return [proportion_label(dataset, colnames, marginal_colnames)
            for marginal_colnames in _yield_prop_combos(dataset, colnames)]

def calc_props(summaryset, colnames, allvals, freqcol):
    """
    Add proportions columns to a summaryset

    If the conditioning columns are a, b, and c, the resulting proportions
    columns will be:
        '_prop_of_all-a-b-c', 
        '_prop_of_all-b-c', 
        '_prop_of_all-a-c', 
        '_prop_of_all-a-b', 
        '_prop_of_all-c', 
        '_prop_of_all-b', 
        '_prop_of_all-a'

    summaryset is a temporary summary dataset (still subtly
        different from a real dataset at this time).
    colnames is a list of the conditioning column names. 
    allvalues is a list containing the allvalues for the above columns
    freqcol is the frequency column, typically _freq_
    """

    allvals_dict = dict(zip(colnames, allvals))
    for marginal_colnames in _yield_prop_combos(summaryset, colnames):
        props = []
        for i, freq in enumerate(summaryset[freqcol].data):
            val_list = []
            for colname in colnames:
                if colname in marginal_colnames:
                    val_list.append(allvals_dict[colname])
                else:
                    val_list.append(summaryset[colname].data[i])
            mt = summaryset.marginal_total_idx[tuple(val_list)]
            den = summaryset[freqcol].data[mt]
            if den > 0:   
                prop = freq / float(den)
            else:
                prop = None
#            if marginal_colnames == ['race']:
#                print '%2d: %8d %8d %8d %8.4g %s' % (i, mt, freq, den, prop, val_list)
            props.append(prop)
        propname, proplabel = proportion_label(summaryset, colnames,
                                               marginal_colnames)
        col = summaryset.addcolumn(propname, proplabel)
        col.data = props
