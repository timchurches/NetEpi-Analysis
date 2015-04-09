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
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

enum {
    BLOB_FREE,			/* blob is free space */
    BLOB_TABLE,			/* blob contains the blob table! */
    BLOB_SEQUENCE,		/* blob contains the sequence lookup table */
    BLOB_DATA			/* blob contains data */
};

typedef struct {
    off_t loc;			/* location of the blob */
    size_t size;		/* size of blob */
    size_t len;			/* length of blob */
    int status;			/* status of blob */
    int type;			/* user: type of blob */
    int other;			/* user: index of related blob */
} BlobDesc;

typedef struct {
    off_t table_loc;		/* where the blob table is stored */
    int table_size;		/* allocated table size */
    int table_len;		/* entries used in the table */
    int table_index;		/* blob which contains the blob table */

    int seq_index;		/* blob which contains the array lookup */
    int seq_size;		/* allocated sequence size */
    int seq_len;		/* number of blobs in the sequence */
} StoreHeader;

typedef struct {
    int mode;			/* file open mode */
    int fd;			/* file descriptor */
    int prot;			/* mmap prot */
    StoreHeader *header;	/* address of start of store */
    size_t size;		/* size of file */
    int cycle;			/* increment when file remapped */
} MmapBlobStore;

MmapBlobStore *store_open(char *filename, char *mode);
int store_append(MmapBlobStore *sm);
void *store_blob_address(MmapBlobStore *sm, BlobDesc *desc);
int store_num_blobs(MmapBlobStore *sm);
int store_get_header(MmapBlobStore *sm, StoreHeader *header);
void store_usage(MmapBlobStore *sm, size_t *used, size_t *unused);
int store_close(MmapBlobStore *sm);
size_t store_compress(MmapBlobStore *sm);
int store_cycle(MmapBlobStore *sm);
BlobDesc *store_get_blobdesc(MmapBlobStore *sm, int index, int from_seq);
int store_blob_resize(MmapBlobStore *sm, int index, size_t data_len);
int store_blob_free(MmapBlobStore *sm, int index);
int store_blob_size(MmapBlobStore *sm, int index);
