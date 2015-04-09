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
# $Id: Describe.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Describe.py,v $

from SOOMv0.common import *

class Describe:
    """
    Generate a structured string description of some object
    """

    def __init__(self, detail, *sections):
        self.detail = detail
        self.sections_order = sections
        self.sections = {}
        for name in sections:
            self.new_section(name)

    def new_section(self, name):
        self.sections.setdefault(name, [])

    def add(self, section, prio, label, text):
        if self.detail >= prio and text is not None:
            # Add some minimal pretty-printing of common types
            if callable(text):
                text = '%s.%s()' % (text.__module__, text.__name__)
            elif hasattr(text, 'items'):
                if text:
                    limit = 40
                    trans = text.items()
                    trans.sort()
                    trans = ['%s -> %s' % kv for kv in trans[:limit]]
                    if len(trans) < len(text):
                        trans.append('... and %d more values' %
                                    (len(text) - len(trans)))
                    text = ', '.join(trans)
                else:
                    text = '<empty map>'
            self.sections[section].append((label, text))

    def describe_tuples(self):
        lines = []
        for section_name in self.sections_order:
            lines.extend(self.sections[section_name])
        return lines

    def describe_str(self):
        return '\n'.join(['%s: %s' % kv for kv in self.describe_tuples()])

    def __str__(self):
        return self.describe_str()
