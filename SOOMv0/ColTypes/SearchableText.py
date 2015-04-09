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
# $Id: SearchableText.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/ColTypes/SearchableText.py,v $

import os
import re
import time
import stat
import struct
import array
import bisect

from soomarray import ArrayVocab
from soomfunc import strip_word

from SOOMv0.common import *
from SOOMv0.Soom import soom
from SOOMv0.ColTypes.base import DatasetColumnBase

class SearchableTextDatasetColumn(DatasetColumnBase):
    coltype = 'searchabletext'
    loadables = DatasetColumnBase.loadables + ('wordidx', 'occurrences')

    def is_searchabletext(self):
        return True

    WORD_RE = re.compile(r"[A-Z0-9][A-Z0-9']+", re.I)

    def __init__(self, *args, **kw):
        """
        Initialise the cache
        """
        DatasetColumnBase.__init__(self, *args, **kw)
        self.entries_cache = {}
        self.wordidx_filename = self.object_path('SOOMstringvocab', 'wordidx',
                                         mkdirs=True)
        self.occurrences_filename = self.object_path('SOOMpackeddata', 'occurrences',
                                         mkdirs=True)
        self._wordidx = None
        self._occurrences = None

    def _wordidx_gen(self, src):
        # Keep a count of the occurrences of each word.
        for rownum, value in enumerate(src):
            if value:
                words = {}
                for wordnum, match in enumerate(self.WORD_RE.finditer(value)):
                    word = strip_word(match.group())
                    words.setdefault(word, []).append(wordnum)
                self.add_row_words(rownum, words)
            yield value
        self._store_wordidx()

    def get_store_chain(self, data, mask=None):
        self.create_wordidx()
        src = iter(data)
        if mask is not None:
            src = self._mask_gen(src, mask)
        if self.missingvalues:
            src = self._missing_gen(src, self.missingvalues)
        src = self._storedata_gen(src)
        src = self._wordidx_gen(src)
        return src

    def _store_wordidx(self):
        """
        Make sure the accumulated word information is flushed
        """
        if not self.parent_dataset.backed:
            raise Error('Searchable text requires a "backed" dataset')
        self.flush()

    def create_wordidx(self):
        """
        Open the word index files read-write and prepare them
        """
        if not self.parent_dataset.backed:
            raise NotImplementedError
        if self._wordidx is None:
            starttime = time.time()
            self._wordidx = ArrayVocab(self.wordidx_filename, 'c')
            self._occurrences = file(self.occurrences_filename, 'wb+')
            # create an empty block 0
            self._occurrences.write("\0" * self.BLOCK_SIZE)
            elapsed = time.time() - starttime
            soom.info('creation of %r index took %.3f seconds.' % (self.name, elapsed))

    def load_wordidx(self):
        """
        Open the word index files read-only
        """
        if not self.parent_dataset.backed:
            raise NotImplementedError
        if self._wordidx is None:
            starttime = time.time()
            self._wordidx = ArrayVocab(self.wordidx_filename, 'r')
            self._occurrences = file(self.occurrences_filename, 'rb')
            blocks = os.fstat(self._occurrences.fileno())[stat.ST_SIZE] / self.BLOCK_SIZE
            elapsed = time.time() - starttime
            soom.info('load of %r index (%d words/%d blocks) took %.3f seconds.' %\
                        (self.name, len(self._wordidx), blocks, elapsed))
    load_occurrences = load_wordidx

    def get_wordidx(self):
        if self._wordidx is None:
            self.load_wordidx()
        return self._wordidx
    wordidx = property(get_wordidx)

    def get_occurrences(self):
        if self._occurrences is None:
            self.load_occurrences()
        return self._occurrences
    occurrences = property(get_occurrences)

    def op_contains(self, sexpr, filter_keys):
        return sexpr(self)[0]

    # Data set management routines
    #
    # Actual word occurrences are kept packed in a file.  Occurrences are kept
    # as linked sets of data blocks.  The word index file contains the block
    # number of the first block in each word's chain.
    #
    # All data items in blocks are 4 byte integers.  Each block sequence
    # contains the following:
    #
    # size      the size (in blocks) of this sequence
    # link      the block number of the next sequence (zero if there is no next block)
    # used      the number OF ENTRIES used within this current sequence
    #           the total number of possible entries is (size * block_size - 6) / entry_size
    #
    # then follows multiple entries of the form
    #
    # row       the row number for a word
    # word      the word number within the row
    #
    # The first block in the file is special and contains the links to the first
    # block of the free list for each of the various block sizes.  Block 0 is
    # thus also used as a sentinel value to mark the end of block chains.
    # (At the moment there is no free block pool as the file only grows.)

    BYTE_ORDER = ">"
    BLOCK_SIZE = 512
    BLOCK_HEADER = "LLL"
    BLOCK_HEADER_STRUCT = BYTE_ORDER + BLOCK_HEADER
    BLOCK_HEADER_LENGTH = struct.calcsize(BLOCK_HEADER_STRUCT)
    ENTRY_TYPE = "L"
    ENTRY_SIZE = 2
    ENTRY_BYTE_SIZE = 2 * array.array(ENTRY_TYPE).itemsize
    # this list must be in sorted order
    BLOCK_SIZES = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)

    def _get_occurrences(self, word):
        # first look for the word itself in the index
        block = self.get_blocks(word)[0]
        if block is None:
            return None
        # load and assemble all entries in the file
        entries = array.array(self.ENTRY_TYPE)
        while block:
            block, size, link, used, entries = self.load_block(block, entries)
            #print "loaded", used, "entries from block", block, "for", word
            block = link
        return entries

    def round_size(self, size):
        """
        Round the given size up to the next large block size allocation
        """
        try:
            size = self.BLOCK_SIZES[bisect.bisect_left(self.BLOCK_SIZES, size)]
        except IndexError:
            # choose the largest block size
            size = self.BLOCK_SIZES[-1]
        return size

    def entry_capacity(self, size):
        """
        Calculate the number of entries that will fit in a sequence of the given
        size.
        """
        return (size * self.BLOCK_SIZE - self.BLOCK_HEADER_LENGTH) / self.ENTRY_BYTE_SIZE

    def load_block_info(self, block):
        """
        Load and return the header information for a block sequence
        """
        occurrences = self.occurrences
        occurrences.seek(block * self.BLOCK_SIZE)
        fmt = self.BLOCK_HEADER_STRUCT
        size, link, used = struct.unpack(fmt, occurrences.read(self.BLOCK_HEADER_LENGTH))
        return size, link, used

    def write_block_info(self, block, size = None, link = None, used = None):
        """
        Rewrite the information in a block header
        """
        # WARNING we can change the size here in case we ever want to amalgamate
        # blocks but at the moment we're not doing that
        if size is None or link is None or used is None:
            current_size, current_link, current_used = self.load_block_info(block)
            if size is None:
                size = current_size
            elif size != current_size:
                raise ValueError, "can't change size of block %d" % block
            if link is None:
                link = current_link
            if used is None:
                used = current_used
        occurrences = self.occurrences
        occurrences.seek(block * self.BLOCK_SIZE)
        fmt = self.BLOCK_HEADER_STRUCT
        occurrences.write(struct.pack(fmt, size, link, used))
        return size, link, used

    def write_block(self, block, entries):
        size, link, used = self.write_block_info(block, used = len(entries) / self.ENTRY_SIZE)
        entries.tofile(self.occurrences)
        return size, link, used

    def load_block(self, block, entries = None, space_needed = 1):
        """
        Load and return the header information for a block sequence
        """
        if entries is None:
            entries = array.array(self.ENTRY_TYPE)
        if block is None:
            # we're actually allocating so allocate a new smallest block sequence
            size, link, used = self.round_size(space_needed), None, 0
            block = self.chain_new_block(word, None, size)
        else:
            size, link, used = self.load_block_info(block)
            if used:
                entries.fromfile(self.occurrences, used * self.ENTRY_SIZE)
        return block, size, link, used, entries

    def add_row_words(self, rownum, words):
        """
        For the given rownum add the words: a dictionary of
        
            word: [wordnum, wordnum, ...]

        pairs
        """
        for word, wordnums in words.iteritems():
            # get a block prepared for us to write out some entries
            # this will make sure a block exists (creating it if necessary)
            # and also gives us a chance to grow a block if necessary
            # we get back the block entries and the number of entries we can
            # write before having to ask for another block
            n, remaining = 0, len(wordnums)
            while remaining:
                last_block, entries, space_left = self.get_last_entries(word, remaining)
                #print space_left, "entries left for", word, "in block", last_block
                count = min(space_left, remaining)
                new_entries = []
                for i in range(n, n + count):
                    entries.extend([rownum, wordnums[i]])
                # when (space_left - count) == 0, get_last_entries() will
                # automatically allocate a new block the next time around
                #print "adding", count, "entries to", word
                self.entries_cache[last_block] = [entries, space_left - count]
                n += count
                remaining -= count

    def get_last_entries(self, word, space_needed):
        """
        Return an array object caching the current entries for the last block
        allocated for word.  If more space is needed grow the block, shuffling
        things around if needed.  Return the amount of space remaining in the
        block (we may be at the maximum block size).
        """
        first_block, last_block = self.get_blocks(word, space_needed)
        #print word, "has a first block of", first_block, "and a last block of", last_block
        entries, space_left = self.entries_cache.get(last_block)
        #print "\tentries cache said", space_left, "entries left"
        if entries is None:
            last_block, size, link, used, entries = self.load_block(last_block)
            space_left = self.entry_capacity(size) - used
            self.entries_cache[last_block] = [entries, space_left]
        if space_needed and not space_left:
            # flush out the current block
            size, link, used = self.flush_block(last_block)
            # allocate a new block the next size up from the current block
            last_block, size, entries = self.chain_new_block(word, last_block, size + 1)
            space_left = self.entry_capacity(size)
            self.entries_cache[last_block] = [entries, space_left]
        return last_block, entries, space_left

    def chain_new_block(self, word, block, size):
        """
        Allocate a new empty block sequence rounded to the appropriate size
        at the end of the file and chain it to the specified block.  Make sure
        the file gets extended.
        """
        size = self.round_size(size)
        occurrences = self.occurrences
        occurrences.seek(0, 2)
        new_block_start = occurrences.tell()
        new_block = new_block_start / self.BLOCK_SIZE
        #print "creating new block", new_block, "at", new_block_start, "with size", size, "for", word
        # add the new block to the chain if necessary
        if block:
            #print "\tlinking block", block, "to new block", new_block
            self.write_block_info(block, link = new_block)
            first_block, last_block = self.wordidx[word]
        else:
            first_block = new_block
        # write a new header
        self.write_block_info(new_block, size = size, link = 0, used = 0)
        # extend the file out the requisite number of blocks
        occurrences.seek(new_block_start + size * self.BLOCK_SIZE - 1)
        occurrences.write("\0")
        entries = array.array(self.ENTRY_TYPE)
        self.wordidx[word] = (first_block, new_block)
        return new_block, size, entries

    def flush_block(self, block):
        """
        Write in memory entries back to the file and delete the entries from the
        cache
        """
        entries, space_left = self.entries_cache.get(block, (None, None))
        if entries is None:
            return
        size, link, used = self.write_block(block, entries)
        del self.entries_cache[block]
        return size, link, used

    def flush(self):
        """
        Flush all in memory entries
        """
        for block in self.entries_cache.keys():
            self.flush_block(block)
        self._wordidx.sync()

    def get_blocks(self, word, space_needed = 0):
        """
        Get the blocks allocated to a word. Allocate a new block if required.
        """
        first_block, last_block = self.wordidx.get(word, (None, None))
        if not space_needed:
            return first_block, last_block
        if not first_block:
            # force a block to be created
            # this will slightly over allocate
            first_block, size, entries = self.chain_new_block(word, None, size = space_needed / self.entry_capacity(self.BLOCK_SIZES[0]))
            last_block = first_block
            space_left = self.entry_capacity(size)
            self.entries_cache[last_block] = [entries, space_left]
            self.wordidx[word] = (first_block, last_block)
        return first_block, last_block

