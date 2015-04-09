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
#include "Python.h"
#include "structmember.h"
#include "Numeric/arrayobject.h"

#include "storage.h"

typedef struct {
    PyObject_HEAD

    MmapBlobStore *sm;          /* BLOB store */
} BlobStoreObject;

typedef struct {
    PyObject_HEAD

    BlobStoreObject *store;
    int index;
    int is_raw;

    BlobDesc *desc;
    PyObject *obj;
} BlobObject;

extern PyTypeObject BlobType;
PyObject *BlobObject__init__(BlobStoreObject *store, int index, int is_raw);
void blob_make_numpy_work_please(void);
