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
# $Id: undo.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/undo.py,v $

class _UMC(object):
    __slots__ = 'method', 'args', 'kwargs'

    def __init__(self, method, *args, **kwargs):
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def undo(self, obj):
        getattr(obj, self.method)(*self.args, **self.kwargs)

class UndoError(Exception): pass

class UndoMixin:
    def __init__(self):
        self.clear_undo()

    def undo(self):
        try:
            last_event = self.__undo.pop(-1)
        except IndexError:
            raise UndoError('nothing to undo')
        self.__redo, self.__undo, real_undo = [], self.__redo, self.__undo
        try:
            last_event.undo(self)
        finally:
            self.__redo, self.__undo = self.__undo, real_undo

    def redo(self):
        try:
            next_event = self.__redo.pop(-1)
        except IndexError:
            raise UndoError('nothing to redo')
        real_redo, self.__redo = self.__redo, []
        try:
            next_event.undo(self)
        finally:
            self.__redo = real_redo

    def _record_undo(self, method, *args, **kwargs):
        self.__undo.append(_UMC(method, *args, **kwargs))
        self.__redo = []

    def modified(self):
        return len(self.__undo) > 0

    def clear_undo(self):
        self.__undo = []
        self.__redo = []

if __name__ == '__main__':
    class A(UndoMixin):
        def __init__(self):
            UndoMixin.__init__(self)
            self.b = []

        def add(self, n):
            self._record_undo('remove', -1)
            self.b.append(n)

        def remove(self, i):
            v = self.b.pop(i)
            self._record_undo('add', v)

    a = A()
    a.add(4)
    a.add(5)
    print 'before', a.b, a.b == [4,5]
    a.undo()
    print 'undo one', a.b, a.b == [4]
    a.undo()
    print 'undo two', a.b, a.b == []
    a.redo()
    print 'redo', a.b, a.b == [4]
    a.undo()
    print 'undo redo', a.b, a.b == []
    a.redo()
    print 'redo one', a.b, a.b == [4]
    a.redo()
    print 'redo two', a.b, a.b == [4, 5]
