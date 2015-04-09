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
# $Id: rtfparse.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/loaders/rtfparse.py,v $

import re

__all__ = ['parse']
# Tokens
for tok in 'TEXT,CWORD,CSYM,LBRACE,RBRACE,GROUP'.split(','):
    globals()[tok] = tok        # XXX shouldn't modify globals like this?
    __all__.append(tok)

cword_re = re.compile(r'''
    (?:\\([a-z]+)(-?\d+)?\ ?)           # control word
  |
    (\\[^a-zA-Z])                       # control symbol
  |
    ([{}])                              # group
''', re.VERBOSE | re.MULTILINE)

def tokenise(data):
    last = 0
    for match in cword_re.finditer(data):
        start, end = match.span()
        content = data[last:start]
        last = end
        cword, cwordarg, csym, group = match.groups()
        if content:
            yield TEXT, content
        if cword:
            yield CWORD, (cword, cwordarg)
        elif csym:
            yield CSYM, csym[1]
        elif group == '{':
            yield LBRACE, None
        elif group == '}':
            yield RBRACE, None
    if data[last:]:
        yield TEXT, data[last:]


class Node(object):
    __slots__ = 'token', 'args'

    def __init__(self, token, args):
        self.token = token
        self.args = args

    def dump(self, level):
        indent = '  ' * level
        if self.token == TEXT:
            print '%s%r' % (indent, self.args)
        elif self.token == CWORD:
            print '%s\\%s %r' % (indent, self.args[0], self.args[1])
        elif self.token == CSYM:
            print '%s\\%s' % (indent, self.args[0])
        else:
            print '%s%s %r' % (indent, self.token, self.args)


class Group(Node):
    __slots__ = 'token', 'args', 'children'

    def __init__(self):
        self.token = 'GROUP'
        self.children = []

    def add(self, node):
        self.children.append(node)

    def dump(self, level):
        indent = '  ' * level
        print indent + '['
        for child in self.children:
            child.dump(level + 1)
        print indent + ']'


def parse(data):
    stack = []
    for token, arg in tokenise(data):
    #    print '%6s %r' % (token, arg)
        if token == LBRACE:
            stack.append(Group())
        elif token == RBRACE:
            group = stack.pop()
            if stack:
                stack[-1].add(group)
            else:
                return group
        else:
            stack[-1].add(Node(token, arg))


if __name__ == '__main__':
    import sys
    aa = open(sys.argv[1], 'U').read()
    root = parse(aa)
    root.dump(0)
