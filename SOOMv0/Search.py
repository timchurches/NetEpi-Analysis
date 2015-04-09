# vim: set ts=4 sw=4 et:
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
# $Id: Search.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Search.py,v $

import re
import sets
import Numeric
import soomfunc

# A search expression tree is built up by the parser when the query is first
# parsed and evaulated by the contains operator.
#
# Intermediate results are parsed up the tree as a pair whose first element
# is a Numeric.array of rows which have been hit and the whose second element is
# a dictionary keyed by row containing a value consisting of a Numeric.array
# containing words hit in that row.  This allows the use of some of the soomfunc
# operations on Numeric.array structures.

class Disjunction:
    # Used below to make rowwise unions easier
    _EMPTY = Numeric.array([],  Numeric.Int)

    def __init__(self, part):
        self.parts = [part]

    def append(self, part):
        self.parts.append(part)

    def __call__(self, datasetColumn):
        # compute the union of the part hit sets
        rows, words = self.parts[0](datasetColumn)
        for part in self.parts[1:]:
            other_rows, other_words = part(datasetColumn)
            rows = soomfunc.union(rows, other_rows)
            # almalgamate word hits
            new_words = {}
            for r in rows:
                new_words[r] = soomfunc.union(words.get(r, self._EMPTY),
                                              other_words.get(r, self._EMPTY))
            words = new_words
        return rows, words

    def __str__(self):
        return "(%s)" % " | ".join(map(str, self.parts))

class Conjunction:

    # nearness masks
    _BEFORE = 1
    _AFTER = 2

    DEFAULT_NEARNESS = 10

    def __init__(self, op, lhs, rhs, nearness = DEFAULT_NEARNESS):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
        self.nearness = nearness

    def __call__(self, datasetColumn):
        lhsrowwords = self.lhs(datasetColumn)
        rhsrowwords = self.rhs(datasetColumn)
        if self.op == '&':
            # & is rowwise intersection
            return self.intersect(lhsrowwords, rhsrowwords)
        if self.op == '&!':
            # &! is rowwise set difference
            return self.difference(lhsrowwords, rhsrowwords)
        # before and after are a variation on near
        if self.op == '<':
            return self.near(lhsrowwords, rhsrowwords, mask = self._BEFORE)
        if self.op == '>':
            return self.near(lhsrowwords, rhsrowwords, mask = self._AFTER)
        if self.op == '~':
            return self.near(lhsrowwords, rhsrowwords)
        raise NotImplementedError

    def __str__(self):
        if nearness != self.DEFAULT_NEARNESS:
            op = "%s[%d]" % (self.op, self.nearness)
        else:
            op = self.op
        return "(%s %s %s)" % (self.lhs, op, self.rhs)

    def intersect(self, lhsrowwords, rhsrowwords):
        # find matching rows
        rows = soomfunc.intersect(lhsrowwords[0], rhsrowwords[0])
        lhswords = lhsrowwords[1]
        rhswords = rhsrowwords[1]
        # almalgamate word hits
        words = {}
        for r in rows:
            words[r] = soomfunc.union(lhswords[r], rhswords[r])
        return rows, words

    def difference(self, lhsrowwords, rhsrowwords):
        # find residual rows
        rows = soomfunc.difference(lhsrowwords[0], rhsrowwords[0])
        # use only lhs word hits
        lhswords = lhsrowwords[1]
        words = {}
        for r in rows:
            words[r] = lhswords[r]
        return rows, words

    def near(self, lhsrowwords, rhsrowwords, mask = _BEFORE | _AFTER):
        # only check matching rows
        rows = soomfunc.intersect(lhsrowwords[0], rhsrowwords[0])
        lhswords = lhsrowwords[1]
        rhswords = rhsrowwords[1]
        words = {}
        _BEFORE = self._BEFORE
        _AFTER = self._AFTER
        nearness = self.nearness
        for row in rows:
            hits = sets.Set()
            # this is O(n*n) and could be improved
            # find all hits and then remove duplicates
            for left in lhswords[row]:
                for right in rhswords[row]:
                    if (mask & _BEFORE) and right - nearness <= left <= right:
                        hits.add(left)
                        hits.add(right)
                    if (mask & _AFTER) and right <= left <= right + nearness:
                        hits.add(left)
                        hits.add(right)
            if hits:
                hits = list(hits)
                hits.sort()
                words[row] = Numeric.array(hits, Numeric.Int)
        # remove rows that have no hits left
        rows = Numeric.array(filter(lambda r: r in words, rows), Numeric.Int)
        return rows, words

class Phrase:
    def __init__(self, words):
        self.words = words

    def __call__(self, datasetColumn):
        # a phrase is a conjunction with the added constraint that words
        # must exactly follow one another
        rowwords = self.words[0](datasetColumn)
        for word in self.words[1:]:
            otherwords = word(datasetColumn)
            rowwords = self.follow(rowwords, otherwords)
            if not rowwords:
                # nothing left
                break
        return rowwords
                
    def follow(self, lhsrowwords, rhsrowwords):
        # find matching rows
        rows = soomfunc.intersect(lhsrowwords[0], rhsrowwords[0])
        lhswords = lhsrowwords[1]
        rhswords = rhsrowwords[1]
        # almalgamate word hits
        words = {}
        for row in rows:
            hits = sets.Set()
            # this is O(n*n) and could be improved
            # find all hits and remove duplicates
            for left in lhswords[row]:
                for right in rhswords[row]:
                    if right == left + 1:
                        hits.add(left)
                        hits.add(right)
            if hits:
                hits = list(hits)
                hits.sort()
                words[row] = Numeric.array(hits, Numeric.Int)
        # remove rows that have no hits left
        rows = Numeric.array(filter(lambda r: r in words, rows), Numeric.Int)
        return rows, words

    def __str__(self):
        return '"%s"' % ' '.join(map(str, self.words))

class Word:
    def __init__(self, word):
        self.word = soomfunc.strip_word(word)
        if '*' in word:
            self.re = re.compile('%s$' % self.word.replace('*', '.*'))
            self.wildcard = True
        else:
            self.wildcard = False

    def __call__(self, datasetColumn):
        if self.wildcard:
            return self.wild(datasetColumn)
        v = datasetColumn._get_occurrences(self.word)
        if v is None:
            return [], {}
        rows = []
        wordOccurrences = {}
        currentRow = None
        for n in range(0, len(v), 2):
            row, word = v[n:n + 2]
            if row != currentRow:
                rows.append(row)
                wordOccurrences[row] = []
                currentRow = row
            wordOccurrences[row].append(word)
        rows = Numeric.array(rows, Numeric.Int)
        words = {}
        for k, v in wordOccurrences.iteritems():
            words[k] = Numeric.array(v, Numeric.Int)
        return rows, words

    def wild(self, datasetColumn):
        # find all words matching this pattern and turn the word
        # list into a disjunction
        words = [ w for w in datasetColumn.wordidx.keys() if self.re.match(w) ]
        if not words:
            return [], {}
        expr = Disjunction(Word(words[0]))
        for word in words[1:]:
            expr.append(Word(word))
        return expr(datasetColumn)

    def __str__(self):
        return self.word

