/*
 *  The contents of this file are subject to the HACOS License Version 1.2
 *  (the "License"); you may not use this file except in compliance with
 *  the License.  Software distributed under the License is distributed
 *  on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
 *  implied. See the LICENSE file for the specific language governing
 *  rights and limitations under the License.  The Original Software
 *  is "NetEpi Analysis". The Initial Developer of the Original
 *  Software is the Health Administration Corporation, incorporated in
 *  the State of New South Wales, Australia.
 *
 *  Copyright (C) 2004,2005 Health Administration Corporation.
 *  All Rights Reserved.
 */
/*-------------------------------------------------------------------
 * Implement a simple sequential storage manager.  Each BLOB is
 * accessed via an integer index.
 *
 * All of the BLOB data is managed by a table of BlobDesc structures.
 * By keeping the structures which control the data in one location we
 * can avoid scanning (and paging in) the entire file.
 */
#include "Python.h"
#include "storage.h"

#define GROW_INC (64 * 1024)
#define TABLE_INC 1024

static PyObject *index_error(void)
{
    static PyObject *str;

    if (str == NULL)
	str = PyString_FromString("list index out of range");
    return str;
}

static int grow_file_error(MmapBlobStore *sm, size_t old_size, char *reason)
{
    PyErr_SetFromErrnoWithFilename(PyExc_IOError, reason);
    fprintf(stderr, "grow_file() %s failed: old-size:%ul new-size:%ul\n",
	    reason, old_size, sm->size);
    return -1;
}

/* Grow the data store file to at least the specified min_size -
 * return success status.
 */
static int grow_file(MmapBlobStore *sm, off_t min_size)
{
    size_t old_size;

    old_size = sm->size;
    sm->cycle++;
    sm->size = min_size;
    if (sm->size % GROW_INC)
	sm->size += GROW_INC - sm->size % GROW_INC;
    if (sm->header != (StoreHeader*)-1) {
	if (munmap(sm->header, old_size) < 0)
	    return grow_file_error(sm, old_size, "munmap");
	sm->header = (StoreHeader*)-1;
    }
    if (lseek(sm->fd, sm->size - 1, SEEK_SET) < 0)
	return grow_file_error(sm, old_size, "lseek");
    if (write(sm->fd, "", 1) != 1)
	return grow_file_error(sm, old_size, "write");
    sm->header = (StoreHeader*)
	mmap(0, sm->size, sm->prot, MAP_SHARED, sm->fd, 0);
    if (sm->header == (StoreHeader*)-1)
	return grow_file_error(sm, old_size, "mmap");
    return 0;
}

/* Return a pointer to the BlobDesc specified by index.
 */
static BlobDesc *get_desc(MmapBlobStore *sm, int index)
{
    return (BlobDesc*)((((char*)sm->header) + sm->header->table_loc)) + index;
}

/* Return the address of the BLOB data managed by desc.
 */
void *store_blob_address(MmapBlobStore *sm, BlobDesc *desc)
{
    return ((char*)sm->header) + desc->loc;
}

/* Retrieve the BLOB sequence
 */
static int *get_sequence(MmapBlobStore *sm)
{
    return store_blob_address(sm, get_desc(sm, sm->header->seq_index));
}

/* Enforce data alignment.
 */
static off_t data_align(off_t offset)
{
    int frag;

    frag = offset % sizeof(int);
    if (frag)
	return offset + sizeof(int) - frag; 
    return offset;
}

/* Initialise a new BLOB store file.
 */
static int init_store(MmapBlobStore *sm)
{
    BlobDesc *table_desc;

    /* allocate initial block of data*/
    if (grow_file(sm, GROW_INC) < 0)
	return -1;
    /* initialise the header */
    sm->header->table_loc = sizeof(*sm->header);
    sm->header->table_size = TABLE_INC;
    sm->header->table_len = 1;
    sm->header->table_index = 0;

    sm->header->seq_index = -1;
    sm->header->seq_size = 0;
    sm->header->seq_len = 0;

    table_desc = get_desc(sm, 0);
    table_desc->loc = sm->header->table_loc;
    table_desc->len = sm->header->table_size * sizeof(*table_desc);
    table_desc->size = data_align(table_desc->len);
    table_desc->status = BLOB_TABLE;
    table_desc->type = table_desc->other = 0;
    return 0;
}

/* Grow the table which contains all of the BlobDesc structures.
 * This is a bit complex because the table is actually contained in
 * space managed by the table.
 */
static int grow_table(MmapBlobStore *sm)
{
    BlobDesc *last_desc, *table_desc, *new_table_desc;
    int old_table_index;
    off_t new_table_loc;
    size_t data_len, data_size;

    /* the location of the new table will be at the end of the file */
    last_desc = get_desc(sm, sm->header->table_len - 1);
    new_table_loc = last_desc->loc + last_desc->size;
    data_len = (sm->header->table_size + TABLE_INC) * sizeof(*last_desc);
    data_size = data_align(data_len);
    if (new_table_loc + data_size >= sm->size) {
	/* grow the file */
	if (grow_file(sm, new_table_loc + data_size) < 0)
	    return -1;
    }

    /* current table is stored in desc (sm->header->table_index) */
    old_table_index = sm->header->table_index;
    table_desc = get_desc(sm, old_table_index);
    /* we want to move it to address of new_table_loc */
    memmove(((char*)sm->header) + new_table_loc,
	    store_blob_address(sm, table_desc),
	    sm->header->table_len * sizeof(*table_desc));

    /* update the file header */
    sm->header->table_loc = new_table_loc;
    sm->header->table_size += TABLE_INC;
    sm->header->table_index = sm->header->table_len;
    /* now setup new desc for new desc table */
    new_table_desc = get_desc(sm, sm->header->table_len);
    new_table_desc->loc = new_table_loc;
    new_table_desc->size = data_size;
    new_table_desc->len = data_len;
    new_table_desc->status = BLOB_TABLE;
    new_table_desc->type = new_table_desc->other = 0;
    /* use up the desc used to store the new desc table */
    sm->header->table_len++;
    /* free desc which held old desc table */
    table_desc = get_desc(sm, old_table_index);
    table_desc->status = BLOB_FREE;

    return 0;
}

/* Find the index of a free BlobDesc.
 */
static int find_free_blob(MmapBlobStore *sm, size_t data_len)
{
    BlobDesc *table_desc, *desc;
    int i, best, wasted;
    
    table_desc = get_desc(sm, sm->header->table_index);
    desc = store_blob_address(sm, table_desc);
    best = -1;
    wasted = 0;
    for (i = 0; i < sm->header->table_size; i++, desc++)
	if (desc->status == BLOB_FREE && desc->size > data_len) {
	    if (best < 0 || desc->size - data_len < wasted) {
		best = i;
		wasted = desc->size - data_len;
	    }
	}
    return best;
}

/* Reuse a free BlobDesc.
 */
static void reuse_free_blob(MmapBlobStore *sm, int index, size_t data_len)
{
    BlobDesc *desc;

    desc = get_desc(sm, index);
    desc->len = data_len;
    desc->status = BLOB_DATA;
    desc->type = desc->other = 0;
}

/* Allocate a new BlobDesc.
 */
static int allocate_new_blob(MmapBlobStore *sm, size_t data_len, int status)
{
    BlobDesc *desc, *prev_desc;
    off_t desc_loc;
    int index;
    size_t data_size;

    data_size = data_align(data_len);
    if (sm->header->table_len == sm->header->table_size) {
	/* grow the table */
	if (grow_table(sm) < 0)
	    return -1;
    }
    prev_desc = get_desc(sm, sm->header->table_len - 1);
    desc_loc = prev_desc->loc + prev_desc->size;
    if (desc_loc + data_size >= sm->size) {
	/* grow the file */
	if (grow_file(sm, desc_loc + data_size) < 0)
	    return -1;
    }
    index = sm->header->table_len;
    desc = get_desc(sm, index);
    sm->header->table_len++;
    desc->loc = desc_loc;
    desc->size = data_size;
    desc->len = data_len;
    desc->status = status;
    desc->type = desc->other = 0;
    return index;
}

static int grow_last_desc(MmapBlobStore *sm, size_t data_len)
{
    size_t data_size;
    BlobDesc *desc;

    desc = get_desc(sm, sm->header->table_len - 1);
    data_size = data_align(data_len);
    if (desc->loc + data_size >= sm->size) {
	/* grow the file */
	if (grow_file(sm, desc->loc + data_size) < 0)
	    return -1;
	desc = get_desc(sm, sm->header->table_len - 1);
    }
    desc->len = data_len;
    desc->size = data_size;
    return 0;
}

/* Find a free BLOB or allocate a new BLOB for specified size.
 */
static int allocate_blob(MmapBlobStore *sm, size_t data_len, int status)
{
    int index;

    /* first look for a free BLOB */
    index = find_free_blob(sm, data_len);
    if (index < 0) {
	/* allocate a new BLOB */
	index = allocate_new_blob(sm, data_len, status);
	if (index < 0)
	    return -1;
    } else
	reuse_free_blob(sm, index, data_len);
    return index;
}

/* Change the size of a BLOB.
 */
static int grow_blob(MmapBlobStore *sm, int index, size_t data_len)
{
    int new_index;
    BlobDesc *desc, *new_desc;

    if (index == sm->header->table_len - 1) {
	/* this is the last BLOB in the file - just make it bigger */
	if (grow_last_desc(sm, data_len) < 0)
	    return -1;
	return index;
    }

    desc = get_desc(sm, index);
    new_index = allocate_blob(sm, data_len, desc->status);
    if (new_index < 0)
	return -1;
    desc = get_desc(sm, index);
    new_desc = get_desc(sm, new_index);
    new_desc->type = desc->type;
    new_desc->other = desc->other;
    memmove(store_blob_address(sm, new_desc),
	    store_blob_address(sm, desc), desc->size);
    desc->status = BLOB_FREE;
    return new_index;
}

/* Add a new entry to the BLOB sequence - return the index assigned.
 */
static int array_append(MmapBlobStore *sm, int index)
{
    BlobDesc *desc;
    int *seq;

    /* Initialise the BLOB sequence if it does not exist.
     */
    if (sm->header->seq_index < 0) {
	sm->header->seq_index = allocate_new_blob(sm, TABLE_INC * sizeof(*seq), BLOB_SEQUENCE);
	if (sm->header->seq_index < 0)
	    return -1;
	sm->header->seq_size = TABLE_INC;
	desc = get_desc(sm, sm->header->seq_index);
	seq = store_blob_address(sm, desc);
	memset(seq, 0, TABLE_INC * sizeof(*seq));
    } else
	desc = get_desc(sm, sm->header->seq_index);
    /* Grow the BLOB sequence if necessary.
     */
    if (sm->header->seq_len == sm->header->seq_size) {
	size_t new_size;

	sm->header->seq_size += TABLE_INC;
	new_size = sm->header->seq_size * sizeof(*seq);
	sm->header->seq_index = grow_blob(sm, sm->header->seq_index, new_size);
	if (sm->header->seq_index < 0)
	    return -1;
	desc = get_desc(sm, sm->header->seq_index);
    }
    seq = store_blob_address(sm, desc);
    /* Place BLOB desc into sequence and return new sequence index.
     */
    seq[sm->header->seq_len] = index;
    return sm->header->seq_len++;
}

/* Return the number of BLOBs in the store.
 */
int store_num_blobs(MmapBlobStore *sm)
{
    return sm->header->seq_len;
}

/* Open a BLOB store.
 */
MmapBlobStore *store_open(char *filename, char *mode)
{
    MmapBlobStore *sm;
    struct stat st;

    sm = malloc(sizeof(*sm));
    if (sm == NULL)
	return (MmapBlobStore*)PyErr_NoMemory();

    memset(sm, 0, sizeof(*sm));
    sm->fd = -1;
    sm->header = (StoreHeader*)-1;
    sm->cycle = 0;

    /* make sure mode is valid */
    if (strcmp(mode, "r") == 0) {
	sm->mode = O_RDONLY;
	sm->prot = PROT_READ;
    } else if (strcmp(mode, "r+") == 0) {
	sm->mode = O_RDWR;
	sm->prot = PROT_READ|PROT_WRITE;
    } else if (strcmp(mode, "w+") == 0 || strcmp(mode, "w") == 0) {
	sm->mode = O_RDWR|O_CREAT|O_TRUNC;
	sm->prot = PROT_READ|PROT_WRITE;
    } else {
	PyErr_SetString(PyExc_ValueError, "mode must be 'r', 'r+', 'w' or 'w+'");
	goto error;
    }
    /* open the file */
    if (sm->mode & O_CREAT)
	sm->fd = open(filename, sm->mode, 0666);
    else
	sm->fd = open(filename, sm->mode);
    if (sm->fd < 0) {
	PyErr_SetFromErrnoWithFilename(PyExc_IOError, filename);
	goto error;
    }
    if (fstat(sm->fd, &st) < 0) {
	PyErr_SetFromErrnoWithFilename(PyExc_IOError, filename);
	goto error;
    }
    /* map the file */
    sm->size = st.st_size;
    if (sm->size > 0) {
	sm->header = (StoreHeader*)
	    mmap(0, sm->size, sm->prot, MAP_SHARED, sm->fd, 0);
	if ((caddr_t)sm->header == (caddr_t)-1) {
	    PyErr_SetFromErrnoWithFilename(PyExc_IOError, "mmap");
	    goto error;
	}
    } else if (sm->mode & O_CREAT)
	/* we just created the store, intialise internal structures */
	if (init_store(sm) < 0)
	    goto error;

    return sm;

error:
    if (sm->fd >= 0)
	close(sm->fd);
    if ((caddr_t)sm->header != (caddr_t)-1)
	munmap(sm->header, sm->size);
    free(sm);
    return NULL;
}

/* Allocate a new index in the BLOB sequence.
 *
 * The first time the BLOB is accessed a BlobDesc will be allocated in
 * the table.
 */
int store_append(MmapBlobStore *sm)
{
    return array_append(sm, -1);
}

/* Return the BlobDesc referenced by index.
 */
BlobDesc *store_get_blobdesc(MmapBlobStore *sm, int index, int from_seq)
{
    if (from_seq) {
	int *seq, raw_index;

	if (index >= sm->header->seq_len) {
	    PyErr_SetObject(PyExc_IndexError, index_error());
	    return NULL;
	}
	seq = get_sequence(sm);
	if (seq[index] < 0) {
	    /* allocate empty BLOB descriptor */
	    raw_index = allocate_blob(sm, 0, BLOB_DATA);
	    seq = get_sequence(sm);
	    seq[index] = raw_index;
	}
	return get_desc(sm, seq[index]);
    }

    if (index >= sm->header->table_len) {
	PyErr_SetObject(PyExc_IndexError, index_error());
	return NULL;
    }

    return get_desc(sm, index);
}

/* Return the BLOB store header.
 */
int store_get_header(MmapBlobStore *sm, StoreHeader *header)
{
    *header = *sm->header;
    return 0;
}

int store_blob_size(MmapBlobStore *sm, int index)
{
    int *seq;
    BlobDesc *desc;

    if (index >= sm->header->seq_len) {
	PyErr_SetObject(PyExc_IndexError, index_error());
	return -1;
    }

    seq = get_sequence(sm);
    if (seq[index] < 0)
	return -1;
    desc = get_desc(sm, seq[index]);
    return desc->len;
}

int store_blob_resize(MmapBlobStore *sm, int index, size_t data_len)
{
    int *seq, raw_index;
    BlobDesc *desc;

    if (index >= sm->header->seq_len) {
	PyErr_SetObject(PyExc_IndexError, index_error());
	return -1;
    }

    /* get current desc for BLOB */
    seq = get_sequence(sm);
    raw_index = seq[index];
    if (raw_index < 0) {
	raw_index = allocate_blob(sm, data_len, BLOB_DATA);
	if (raw_index < 0)
	    return -1;
	seq = get_sequence(sm);
	seq[index] = raw_index;
	return 0;
    }

    desc = get_desc(sm, raw_index);
    if (desc->size < data_len) {
	/* need to resize the blob */
	int new_index;

	/* grow BLOB */
	new_index = grow_blob(sm, raw_index, data_len);
	if (new_index < 0)
	    return -1;
	if (new_index != raw_index) {
	    /* update the BLOB sequence to point at the new BLOB */
	    seq = get_sequence(sm);
	    seq[index] = new_index;
	}
    } else
	desc->len = data_len;

    return 0;
}

int store_blob_free(MmapBlobStore *sm, int index)
{
    int *seq, raw_index;
    BlobDesc *desc;

    if (index >= sm->header->seq_len) {
	PyErr_SetObject(PyExc_IndexError, index_error());
	return -1;
    }

    seq = get_sequence(sm);
    if (seq[index] < 0)
	return 0;

    raw_index = seq[index];
    seq[index] = -1;
    desc = get_desc(sm, raw_index);
    desc->status = BLOB_FREE;
    return 0;
}

/* Compress all free space out of the BLOB store - return amount of
 * space freed.
 */
size_t store_compress(MmapBlobStore *sm)
{
    return 0;
}

/* Return mmap() cycle
 */
int store_cycle(MmapBlobStore *sm)
{
    return sm->cycle;
}

/* Return amount of space in use and amount free.
 */
void store_usage(MmapBlobStore *sm, size_t *used, size_t *unused)
{
    BlobDesc *table_desc, *desc;
    int i;

    *used = *unused = 0;
    table_desc = get_desc(sm, sm->header->table_index);
    desc = store_blob_address(sm, table_desc);
    for (i = 0; i < sm->header->table_size; i++, desc++)
	if (desc->status == BLOB_FREE)
	    *unused += desc->size;
	else {
	    *used += desc->len;
	    *unused += desc->size - desc->len;
	}
}

/* Close the BLOB store - return success status
 */
int store_close(MmapBlobStore *sm)
{
    BlobDesc *desc;
    off_t file_size;

    desc = get_desc(sm, sm->header->table_len - 1);
    file_size = data_align(desc->loc + desc->size);
    
    if (sm->header != (StoreHeader*)-1) {
	if (munmap(sm->header, sm->size) < 0) {
	    PyErr_SetFromErrnoWithFilename(PyExc_IOError, "munmap");
	    return -1;
	}
	sm->header = (StoreHeader*)-1;
    }

    if (sm->fd >= 0 && file_size != sm->size) {
	if (ftruncate(sm->fd, file_size) < 0) {
	    PyErr_SetFromErrnoWithFilename(PyExc_IOError, "ftruncate");
	    return -1;
	}
    }
    if (sm->fd >= 0) {
	if (close(sm->fd) < 0) {
	    PyErr_SetFromErrnoWithFilename(PyExc_IOError, "close");
	    return -1;
	}
	sm->fd = -1;
    }

    free(sm);
    return 0;
}
