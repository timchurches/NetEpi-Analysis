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

/* Header for array BLOBs which describes the array.
 */
typedef struct {
    int type_num;
    int rank;
    int shape[40];
} MmapArrayDesc;

static void reload_desc(BlobObject *self)
{
    self->desc = store_get_blobdesc(self->store->sm,
				    self->index, !self->is_raw);
}

/* Array data size calculation lifted out of Numpy source - no
 * alignment included because we might want to append...
 */
static size_t array_data_size(PyArrayObject *array)
{
    int data_size, i;

    data_size = array->descr->elsize;
    for (i = 0; i < array->nd; i++)
        data_size *= array->dimensions[i] ? array->dimensions[i] : 1;
    return data_size;
}

static int array_matches_desc(PyArrayObject *array, MmapArrayDesc *desc)
{
    return desc->type_num == array->descr->type_num
	&& desc->rank == array->nd
	&& memcmp(desc->shape, array->dimensions,
		  desc->rank * sizeof(desc->shape[0])) == 0;
}

static int array_can_append(PyArrayObject *array, MmapArrayDesc *desc)
{
    return desc->type_num == array->descr->type_num
	&& desc->rank == 1
	&& array->nd == 1;
}

static char Blob_as_array__doc__[] = 
"";

static PyObject *Blob_as_array(BlobObject *self, PyObject *args)
{
    MmapArrayDesc *arraydesc;
    MmapBlobStore *sm;

    if (self->is_raw) {
	PyErr_SetString(PyExc_TypeError, "not supported for raw blob");
	return NULL;
    }

    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    reload_desc(self);
    sm = self->store->sm;
    arraydesc = store_blob_address(sm, self->desc);
    if (self->obj != NULL && !PyArray_Check(self->obj)) {
	Py_DECREF(self->obj);
	self->obj = NULL;
    }
    if (self->obj == NULL) {
	self->obj = PyArray_FromDimsAndData(arraydesc->rank,
					    arraydesc->shape,
					    arraydesc->type_num,
					    (char *)(arraydesc + 1));
	if (self->obj == NULL)
	    return NULL;
    } else
	((PyArrayObject*)self->obj)->data = (char *)(arraydesc + 1);
    Py_INCREF(self->obj);
    return self->obj;
}

static char Blob_as_str__doc__[] = 
"";

static PyObject *Blob_as_str(BlobObject *self, PyObject *args)
{
    MmapBlobStore *sm;

    if (self->is_raw) {
	PyErr_SetString(PyExc_TypeError, "not supported for raw blob");
	return NULL;
    }

    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    if (self->obj != NULL) {
	if (!PyString_Check(self->obj)) {
	    Py_DECREF(self->obj);
	    self->obj = NULL;
	} else {
	    Py_INCREF(self->obj);
	    return self->obj;
	}
    }

    reload_desc(self);
    sm = self->store->sm;
    self->obj = PyString_FromStringAndSize(store_blob_address(sm, self->desc),
					   self->desc->len);
    if (self->obj == NULL)
	return NULL;
    Py_INCREF(self->obj);
    return self->obj;
}

static char Blob_save_array__doc__[] = 
"";

static PyObject *Blob_save_array(BlobObject *self, PyObject *args)
{
    PyObject *obj;
    PyArrayObject *array;
    size_t array_size;
    MmapArrayDesc *arraydesc = NULL;
    MmapBlobStore *sm;
    int resize_blob;

    if (self->is_raw) {
	PyErr_SetString(PyExc_TypeError, "not supported for raw blob");
	return NULL;
    }

    if (!PyArg_ParseTuple(args, "O", &obj))
	return NULL;
    array = (PyArrayObject *)
	PyArray_ContiguousFromObject(obj, PyArray_NOTYPE, 0, 0);
    if (array == NULL)
	return NULL;

    sm = self->store->sm;
    array_size = array_data_size(array);
    if (store_blob_size(sm, self->index) > 0) {
	reload_desc(self);
	arraydesc = store_blob_address(sm, self->desc);
	resize_blob = !array_matches_desc(array, arraydesc);
    } else
	resize_blob = 1;

    if (resize_blob) {
	/* (re)allocate blob */
	if (store_blob_resize(sm, self->index,
			      sizeof(*arraydesc) + array_size) < 0) {
	    Py_DECREF(array);
	    return NULL;
	}
	reload_desc(self);
	arraydesc = store_blob_address(sm, self->desc);
	/* copy array description */
	arraydesc->type_num = array->descr->type_num;
	arraydesc->rank = array->nd;
	memcpy(arraydesc->shape, array->dimensions,
	       arraydesc->rank * sizeof(arraydesc->shape[0]));
    }
    /* copy array data */
    memmove(arraydesc + 1, array->data, array_size);

    if (self->obj) {
	Py_DECREF(self->obj);
	self->obj = NULL;
    }

    Py_DECREF(array);
    Py_INCREF(Py_None);
    return Py_None;
}

static char Blob_append_array__doc__[] = 
"";

static PyObject *Blob_append_array(BlobObject *self, PyObject *args)
{
    PyObject *obj;
    PyArrayObject *array;
    size_t array_size;
    MmapArrayDesc *arraydesc = NULL;
    MmapBlobStore *sm;
    int blob_len, num_elems;

    if (self->is_raw) {
	PyErr_SetString(PyExc_TypeError, "not supported for raw blob");
	return NULL;
    }

    if (!PyArg_ParseTuple(args, "O", &obj))
	return NULL;
    array = (PyArrayObject *)
	PyArray_ContiguousFromObject(obj, PyArray_NOTYPE, 0, 0);
    if (array == NULL)
	return NULL;

    sm = self->store->sm;
    if (store_blob_size(sm, self->index) > 0) {
	reload_desc(self);
	arraydesc = store_blob_address(sm, self->desc);
	if (!array_can_append(array, arraydesc)) {
	    Py_DECREF(array);
	    PyErr_SetString(PyExc_TypeError, "can only append rank-1 arrays");
	    return NULL;
	}
	blob_len = self->desc->len;
	num_elems = arraydesc->shape[0];
    } else {
	blob_len = sizeof(*arraydesc);
	num_elems = 0;
    }

    /* (re)allocate blob */
    array_size = array_data_size(array);
    if (store_blob_resize(sm, self->index, blob_len + array_size) < 0) {
	Py_DECREF(array);
	return NULL;
    }
    reload_desc(self);
    arraydesc = store_blob_address(sm, self->desc);
    /* copy array description */
    arraydesc->type_num = array->descr->type_num;
    arraydesc->rank = 1;
    arraydesc->shape[0] = num_elems + array->dimensions[0];

    /* copy array data */
    memmove(((char*)arraydesc) + blob_len, array->data, array_size);

    if (self->obj) {
	Py_DECREF(self->obj);
	self->obj = NULL;
    }

    Py_DECREF(array);
    Py_INCREF(Py_None);
    return Py_None;
}

static char Blob_save_str__doc__[] = 
"";

static PyObject *Blob_save_str(BlobObject *self, PyObject *args)
{
    char *str;
    int len;
    caddr_t addr = NULL;
    MmapBlobStore *sm;
    int resize_blob;

    if (self->is_raw) {
	PyErr_SetString(PyExc_TypeError, "not supported for raw blob");
	return NULL;
    }

    if (!PyArg_ParseTuple(args, "s#", &str, &len))
	return NULL;

    sm = self->store->sm;
    if (store_blob_size(sm, self->index) > 0) {
	reload_desc(self);
	addr = store_blob_address(sm, self->desc);
	resize_blob = (len != self->desc->len);
    } else
	resize_blob = 1;
    if (resize_blob) {
	if (store_blob_resize(sm, self->index, len) < 0)
	    return NULL;
	reload_desc(self);
	addr = store_blob_address(sm, self->desc);
    }
    /* copy string data */
    memmove(addr, str, len);

    if (self->obj) {
	Py_DECREF(self->obj);
	self->obj = NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static struct PyMethodDef Blob_methods[] = {
    { "as_array", (PyCFunction)Blob_as_array, METH_VARARGS, Blob_as_array__doc__ },
    { "as_str", (PyCFunction)Blob_as_str, METH_VARARGS, Blob_as_str__doc__ },
    { "save_array", (PyCFunction)Blob_save_array, METH_VARARGS, Blob_save_array__doc__ },
    { "save_str", (PyCFunction)Blob_save_str, METH_VARARGS, Blob_save_str__doc__ },
    { "append_array", (PyCFunction)Blob_append_array, METH_VARARGS, Blob_append_array__doc__ },
    { NULL, NULL}
};

static void Blob__del__(BlobObject *self)
{
    Py_XDECREF(self->obj);
    Py_XDECREF(self->store);

    PyMem_DEL(self);
}

#define OFFSET(x) offsetof(BlobDesc, x)

static struct memberlist Blob_memberlist[] = {
    { "len",    T_INT, OFFSET(len),    RO },
    { "loc",    T_INT, OFFSET(loc),    RO },
    { "other",  T_INT, OFFSET(other) },
    { "size",   T_INT, OFFSET(size),   RO },
    { "status", T_INT, OFFSET(status), RO },
    { "type",   T_INT, OFFSET(type) },
    { NULL }
};

static PyObject *Blob__getattr__(BlobObject *self, char *name)
{
    PyObject *rv;

    reload_desc(self);

    rv = PyMember_Get((char *)self->desc, Blob_memberlist, name);
    if (rv)
	return rv;
    PyErr_Clear();
    return Py_FindMethod(Blob_methods, (PyObject *)self, name);
}


static int Blob__setattr__(BlobObject *self, char *name, PyObject *v)
{
    if (v == NULL) {
	PyErr_SetString(PyExc_AttributeError, "Cannot delete attribute");
	return -1;
    }
    reload_desc(self);
    return PyMember_Set((char *)self->desc, Blob_memberlist, name, v);
}

static char BlobType__doc__[] = 
"";

PyTypeObject BlobType = {
    PyObject_HEAD_INIT(0)
    0,				/*ob_size*/
    "BlobType",			/*tp_name*/
    sizeof(BlobObject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)Blob__del__,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)Blob__getattr__, /*tp_getattr*/
    (setattrfunc)Blob__setattr__, /*tp_setattr*/
    (cmpfunc)0,			/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,				/*tp_as_number*/
    0,				/*tp_as_sequence*/
    0,				/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)0,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    0L,0L,0L,0L,
    BlobType__doc__
};

PyObject *BlobObject__init__(BlobStoreObject *store, int index, int is_raw)
{
    BlobObject *self;
    MmapBlobStore *sm;
    BlobDesc *desc;

    sm = store->sm;
    desc = store_get_blobdesc(sm, index, !is_raw);
    if (desc == NULL)
	return NULL;

    self = PyObject_NEW(BlobObject, &BlobType);
    if (self == NULL)
	return NULL;

    self->store = store;
    Py_INCREF(store);
    self->desc = desc;
    self->index = index;
    self->is_raw = is_raw;
    self->obj = NULL;

    return (PyObject*)self;
}

void blob_make_numpy_work_please(void)
{
    import_array();
}
