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
# $Id: Timers.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Timers.py,v $

import time

class Timers(object):
    __slots__ = 'label', 'start_time', 'cumulative'
    timers = {}

    def __new__(cls, label):
        try:
            return cls.timers[label]
        except KeyError:
            self = object.__new__(cls)
            self.label = label
            self.cumulative = 0.0
            cls.timers[label] = self
            return self

    def __init__(self, label):
        self.start_time = time.time()

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.cumulative += time.time() - self.start_time

    def reset(cls):
        for timer in cls.timers.values():
            timer.cumulative = 0.0
    reset = classmethod(reset)

    def report(cls):
        lines = []
        timers = cls.timers.items()
        timers.sort()
        total = 0.0
        for label, timer in timers:
            if timer.cumulative >= 0.001:
                lines.append('%8.3fs %s' % (timer.cumulative, label))
                total += timer.cumulative
        lines.append('%8.3fs TOTAL' % (total))
        return '\n'.join(lines)
    report = classmethod(report)
