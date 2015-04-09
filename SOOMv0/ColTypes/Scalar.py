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
# $Id: Scalar.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/ColTypes/Scalar.py,v $

import Numeric, MA
import soomfunc
from SOOMv0.ColTypes.base import DatasetColumnBase

class _ScalarDatasetColumn(DatasetColumnBase):

    def is_scalar(self):
        return True

    def _op_general(self, op, value, filter_keys=[]):
        # handle the general case for an operator combining vectors of results
        # for each operator.
        #
        # NB: use of filled() in Numeric ops is a dangerous hack and may give
        # wrong answers if columns contains values <= 0
        if type(self.data) is MA.MaskedArray:
            numeric_fn = getattr(MA, op)
            resmap = numeric_fn(self.data, value).filled()
        else:
            numeric_fn = getattr(Numeric, op)
            resmap = numeric_fn(self.data, value)
        return Numeric.nonzero(resmap)

    def op_less_than(self, value, filter_keys):
        return self._op_general('less', value, filter_keys)

    def op_less_equal(self, value, filter_keys):
        return self._op_general('less_equal', value, filter_keys)

    def op_greater_than(self, value, filter_keys):
        return self._op_general('greater', value, filter_keys)

    def op_greater_equal(self, value, filter_keys):
        return self._op_general('greater_equal', value, filter_keys)

    def op_not_equal(self, value, filter_keys):
        return self._op_general('not_equal', value, filter_keys)

    def op_equal(self, value, filter_keys):
        return self._op_general('equal', value, filter_keys)

    def op_between(self, value, filter_keys):
        try:
            start, end = value
        except (ValueError, TypeError):
            raise ExpressionError('between(start, end)')
        if type(self.data) is MA.MaskedArray:
            resmap_ge = greater_equal(self.data, start).filled()
            resmap_lt = less(self.data, end).filled()
        else:
            resmap_ge = Numeric.greater_equal(self.data, start)
            resmap_lt = Numeric.less(self.data, end)
        vectors = soomfunc.intersect(Numeric.nonzero(resmap_ge), 
                                     NUmeric.nonzero(resmap_lt))
        return vectors


class ScalarDatasetColumn(_ScalarDatasetColumn):
    coltype = 'scalar'


class WeightingDatasetColumn(_ScalarDatasetColumn):
    coltype = 'weighting'

    def is_weighting(self):
        return True


