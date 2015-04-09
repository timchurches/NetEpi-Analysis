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
# $Id: common.py 2633 2007-03-30 01:37:49Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/common.py,v $

version_info = 0, 8, 1
version = '-'.join([str(v) for v in version_info])
expert = False

class Error(Exception): pass

class ColumnNotFound(Error): pass
class DatasetNotFound(Error): pass
class ExpressionError(Error): pass
class PlotError(Error): pass

SUB_DETAIL, NO_DETAIL, SOME_DETAIL, ALL_DETAIL = range(4)

def yesno(var):
    if var:
        return 'Yes'
    else:
        return 'No'
