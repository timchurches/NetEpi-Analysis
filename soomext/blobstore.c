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
#include "blobstore.h"

/*-------------------------------------------------------------------
 * Provide an object which works like a Python list of BLOB objects.
 * BLOBs can be stored as either strings or Numpy arrays.
 */

static char BlobStore_append__doc__[] = 
"append() -> int";

static PyObject *BlobStore_append(BlobStoreObject *self, PyObject *args)
{
    int index;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    index = store_append(self->sm);
    if (index < 0)
	return NULL;

    return PyInt_FromLong(index);
}

static char BlobStore_get__doc__[] = 
"get(int) -> blob";

static PyObject *BlobStore_get(BlobStoreObject *self, PyObject *args)
{
    int index;

    if (!PyArg_ParseTuple(args, "i", &index))
	return NULL;

    return BlobObject__init__(self, index, 1);
}

static char BlobStore_free__doc__[] = 
"free(int) -> None";

static PyObject *BlobStore_free(BlobStoreObject *self, PyObject *args)
{
    int index;

    if (!PyArg_ParseTuple(args, "i", &index))
	return NULL;

    if (store_blob_free(self->sm, index) < 0)
	return NULL;

    Py_INCREF(Py_None);
    return Py_None;
}

static char BlobStore_usage__doc__[] = 
"usage() -> (int, int)";

static PyObject *BlobStore_usage(BlobStoreObject *self, PyObject *args)
{
    size_t used, unused;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    store_usage(self->sm, &used, &unused);
    return Py_BuildValue("(ii)", (int)used, (int)unused);
}

static char BlobStore_header__doc__[] = 
"header() -> (table_size, table_len, table_index, table_loc, seq_size, seq_len, seq_index)";

static PyObject *BlobStore_header(BlobStoreObject *self, PyObject *args)
{
    StoreHeader header;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    if (store_get_header(self->sm, &header) < 0)
	return NULL;
    return Py_BuildValue("(iiiiiii)",
			 (int)header.table_size,
			 (int)header.table_len,
			 (int)header.table_index,
			 (int)header.table_loc,
			 (int)header.seq_size,
			 (int)header.seq_len,
			 (int)header.seq_index);
}

static struct PyMethodDef BlobStore_methods[] = {
    { "append", (PyCFunction)BlobStore_append, METH_VARARGS, BlobStore_append__doc__ },
    { "get", (PyCFunction)BlobStore_get, METH_VARARGS, BlobStore_get__doc__ },
    { "free", (PyCFunction)BlobStore_free, METH_VARARGS, BlobStore_free__doc__ },
    { "usage", (PyCFunction)BlobStore_usage, METH_VARARGS, BlobStore_usage__doc__ },
    { "header", (PyCFunction)BlobStore_header, METH_VARARGS, BlobStore_header__doc__ },
    { NULL, NULL }
};

static void BlobStore__del__(BlobStoreObject *self)
{
    if (self->sm != NULL)
	store_close(self->sm);
    PyMem_DEL(self);
}

static PyObject *BlobStore__getattr__(BlobStoreObject *self, char *name)
{
    return Py_FindMethod(BlobStore_methods, (PyObject *)self, name);
}

static int BlobStore__setattr__(BlobStoreObject *self, char *name, PyObject *v)
{
    return -1;
}

/*---------------------------------------------------------
 * Access as a Sequence
 *---------------------------------------------------------*/

static int BlobStore__len__(BlobStoreObject *self)
{
    return store_num_blobs(self->sm);
}

static PyObject *BlobStore__getitem__(BlobStoreObject *self, int i)
{
    return BlobObject__init__(self, i, 0);
}

static PySequenceMethods BlobStore_as_sequence = {
    (inquiry)BlobStore__len__,	/*sq_length*/
    0,				/*sq_concat*/
    0,				/*sq_repeat*/
    (intargfunc)BlobStore__getitem__, /*sq_item*/
    0,				/*sq_slice*/
    0,				/*sq_ass_item*/
    0,				/*sq_ass_slice*/
};

static char BlobStoreType__doc__[] = 
"";

static PyTypeObject BlobStoreType = {
    PyObject_HEAD_INIT(0)
    0,				/*ob_size*/
    "BlobStore",		/*tp_name*/
    sizeof(BlobStoreObject),	/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)BlobStore__del__,/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)BlobStore__getattr__, /*tp_getattr*/
    (setattrfunc)BlobStore__setattr__, /*tp_setattr*/
    (cmpfunc)0,			/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,				/*tp_as_number*/
    &BlobStore_as_sequence,	/*tp_as_sequence*/
    0,				/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)0,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    0L, 0L, 0L, 0L,
    BlobStoreType__doc__
};

static PyObject *BlobStore__init__(char *filename, char *mode)
{
    BlobStoreObject *self;

    self = PyObject_NEW(BlobStoreObject, &BlobStoreType);
    if (self == NULL)
	return NULL;

    self->sm = NULL;

    /* open the BLOB store */
    self->sm = store_open(filename, mode);
    if (self->sm == NULL)
	goto error;

    return (PyObject*)self;

error:
    Py_DECREF(self);
    return NULL;
}

static char blobstore_open__doc__[] =
"";

static PyObject *blobstore_open(PyObject *module, PyObject *args)
{
    char *filename;
    char *mode = "r";

    if (!PyArg_ParseTuple(args, "s|s", &filename, &mode))
	return NULL;

    return BlobStore__init__(filename, mode);
}

static struct PyMethodDef blobstore_methods[] = {
    { "open", (PyCFunction)blobstore_open, METH_VARARGS, blobstore_open__doc__ },
    { NULL, (PyCFunction)NULL, 0, NULL }
};

static char blobstore_module__doc__[] = 
"";

void initblobstore(void)
{
    PyObject *module, *dict, *ver = NULL;

    module = Py_InitModule4("blobstore", blobstore_methods,
			    blobstore_module__doc__,
			    (PyObject*)NULL, PYTHON_API_VERSION);

    BlobStoreType.ob_type = &PyType_Type;
    BlobType.ob_type = &PyType_Type;

    blob_make_numpy_work_please();

    if ((dict = PyModule_GetDict(module)) == NULL)
	goto error;
    if ((ver = PyString_FromString("0.11")) == NULL)
        goto error;
    if (PyDict_SetItemString(dict, "__version__", ver) < 0)
        goto error;

error:
    Py_XDECREF(ver);

    if (PyErr_Occurred())
	Py_FatalError("can't initialize module blobstore");
}
