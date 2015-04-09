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
# $Id: interactive_hook.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/interactive_hook.py,v $

import sys
import types
from SOOMv0 import common

def helpful_exceptions(exc_type, exc_value, exc_traceback):
    if (not common.expert and hasattr(sys, 'ps1') 
        and isinstance(exc_value, common.Error)):
        # Interactive
        print >> sys.stderr, '%s error: %s' % (exc_type.__name__, exc_value)
    else:
        orig_exc_hook(exc_type, exc_value, exc_traceback)

orig_exc_hook, sys.excepthook = sys.excepthook, helpful_exceptions

def helpful_display(obj):
    # If the object has a display hook, and the display hook is a function
    # or a bound method...
    if (not common.expert and hasattr(obj, '_display_hook') 
        and (not hasattr(obj._display_hook, 'im_self')
             or obj._display_hook.im_self)):
        return obj._display_hook()
    orig_disp_hook(obj)

orig_disp_hook, sys.displayhook = sys.displayhook, helpful_display
