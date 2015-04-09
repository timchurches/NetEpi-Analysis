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
# $Id: TransformFN.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/TransformFN.py,v $

import cPickle

from SOOMv0.Soom import soom

__all__ = 'maketransform', 'loadtransform'

def maketransform(name,code=None,path=soom.default_object_path):
    """
    Function to take Python code and compile and store it for use
    in transforming data eg coded values to fuller descriptions
    for presentation.

    TO DO: integrate the code which implements SAS-style PROC
    FORMAT syntax as well as supporting Python code. Also need to
    capture metadata about the transform function etc - needs to
    be a Transform class.

    Question: how else does one persistently store Python
    functions except by storing the source code and recompiling
    it when reloaded from disc. Functions are objects, but how to
    serialise them **and** re-instatntiate them into the global
    namespace???? ANSWER: use marshall, not pickle! TO-DO: chnage
    to using marshall.
    """
    try:
        exec code
        filename = os.path.join(path, "%s_transform.SOOMpickle" % name)
        f = open(filename, 'w+')
        f.write(cPickle.dumps(code, 1))
        f.close()
    except:
        raise ValueError, "Transform function code won't compile"
    return None

def loadtransform(name,path=soom.SOOM_object_path):
    """
    Function to load a predefined transform function from disc.
    """
    try:
        filename =   path + name + "_transform.SOOMpickle"
        f = open(filename, 'r')
        code = cPickle.loads(f.read())
        f.close()
        exec code
    except:
        raise ValueError, "Transform function code won't compile"
    return None
