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

#include "Python.h"
#include "structmember.h"
#include "Numeric/arrayobject.h"

/* Implement an object which looks like UserArray but does the mmap
 * thing.
 */

typedef struct {
    int type_num;
    int rank;
    int shape[40];
} MmapArrayDesc;

typedef struct {
    PyObject_HEAD

    MmapArrayDesc *desc;
    off_t len;
    PyArrayObject *array;
} MmapArrayObject;

staticforward PyTypeObject MmapArray_Type;

static char MmapArray_as_array__doc__[] = 
"as_array() -> array";

static PyObject *MmapArray_as_array(MmapArrayObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    Py_INCREF(self->array);
    return (PyObject *)self->array;
}

static struct PyMethodDef MmapArray_methods[] = {
    { "as_array", (PyCFunction)MmapArray_as_array, METH_VARARGS, MmapArray_as_array__doc__ },
    { NULL, NULL}
};

#define OFFSET(x) offsetof(MmapArrayObject, x)

static struct memberlist MmapArray_memberlist[] = {
    { NULL }
};

static PyObject *MmapArray__getattr__(MmapArrayObject *self, char *name)
{
    PyObject *rv;

    rv = PyMember_Get((char *)self->desc, MmapArray_memberlist, name);
    if (rv)
	return rv;
    PyErr_Clear();
    return Py_FindMethod(MmapArray_methods, (PyObject *)self, name);
}

static int MmapArray__setattr__(MmapArrayObject *self, char *name, PyObject *v)
{
    if (v == NULL) {
	PyErr_SetString(PyExc_AttributeError, "Cannot delete attribute");
	return -1;
    }
    return PyMember_Set((char *)self->desc, MmapArray_memberlist, name, v);
}

static void MmapArray__del__(MmapArrayObject *self)
{
    Py_XDECREF(self->array);
    munmap(self->desc, self->len);
    PyMem_DEL(self);
}

static char MmapArray_Type__doc__[] = 
"";

static PyTypeObject MmapArray_Type = {
    PyObject_HEAD_INIT(0)
    0,				/*ob_size*/
    "MmapArray",		/*tp_name*/
    sizeof(MmapArrayObject),	/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)MmapArray__del__,/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)MmapArray__getattr__, /*tp_getattr*/
    (setattrfunc)MmapArray__setattr__, /*tp_setattr*/
    (cmpfunc)0,			/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,				/*tp_as_number*/
    0,				/*tp_as_sequence*/
    0,				/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)0,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    (getattrofunc)0,		/*tp_getattro*/
    (setattrofunc)0,		/*tp_setattro*/
    (PyBufferProcs *)0,		/*tp_as_buffer*/
    0,				/*tp_flags*/
    MmapArray_Type__doc__,	/* Documentation string */
};

char mmaparray_read__doc__[] =
"read(filename) -> MmapArray";

PyObject *mmaparray_read(PyObject *module, PyObject *args)
{
    char *filename;
    int fd;
    struct stat st;
    MmapArrayDesc *desc;
    PyArrayObject *array;
    MmapArrayObject *self;

    if (!PyArg_ParseTuple(args, "s", &filename))
	return NULL;
    fd = open(filename, O_RDONLY);
    if (fd < 0) {
	PyErr_SetString(PyExc_IOError, "could not open file");
	return NULL;
    }
    if (fstat(fd, &st) < 0) {
	PyErr_SetString(PyExc_IOError, "stat failed");
	close(fd);
	return NULL;
    }
    desc = (MmapArrayDesc*)mmap(0, st.st_size, PROT_READ, MAP_SHARED, fd, 0);
    close(fd);
    if ((caddr_t)desc == (caddr_t)-1) {
	PyErr_SetString(PyExc_IOError, "mmap failed");
	return NULL;
    }

    array = (PyArrayObject *)
	PyArray_FromDimsAndData(desc->rank, desc->shape, desc->type_num,
				(char *)(desc + 1));
    if (array == NULL) {
	munmap(desc, st.st_size);
	return NULL;
    }

    self = PyObject_NEW(MmapArrayObject, &MmapArray_Type);
    if (self == NULL) {
	Py_XDECREF(array);
	munmap(desc, st.st_size);
	return NULL;
    }

    self->desc = desc;
    self->len = st.st_size;
    self->array = array;

    return (PyObject*)self;
}

char mmaparray_write__doc__[] =
"write(filename, array)";

PyObject *mmaparray_write(PyObject *module, PyObject *args)
{
    char *filename;
    int fd;
    int data_size, i;
    MmapArrayDesc desc;
    PyArrayObject *array;
    PyArrayObject *new_array;

    if (!PyArg_ParseTuple(args, "sO", &filename, &array))
	return NULL;

    if (!PyArray_Check(array)) {
	PyErr_SetString(PyExc_ValueError, "array object expected");
	return NULL;
    }

    fd = open(filename, O_WRONLY|O_CREAT|O_TRUNC, 0666);
    if (fd < 0) {
	PyErr_SetString(PyExc_IOError, "could not create file");
	return NULL;
    }

    new_array = (PyArrayObject*)
	PyArray_ContiguousFromObject((PyObject*)array,
				     array->descr->type_num, 0, 0);
    if (new_array == NULL) {
	close(fd);
	unlink(filename);
	return NULL;
    }

    memset(&desc, 0, sizeof(desc));
    desc.type_num = new_array->descr->type_num;
    desc.rank = new_array->nd;
    memcpy(desc.shape, new_array->dimensions, desc.rank * sizeof(desc.shape[0]));

    data_size = new_array->descr->elsize;
    for (i = 0; i < new_array->nd; i++)
        data_size *= new_array->dimensions[i] ? new_array->dimensions[i] : 1;
    /* Make sure we're alligned on ints. */
    data_size += sizeof(int) - data_size % sizeof(int); 

    if (write(fd, &desc, sizeof(desc)) != sizeof(desc)
	|| write(fd, new_array->data, data_size) != data_size) {
	close(fd);
	unlink(filename);
	Py_DECREF(new_array);
	PyErr_SetString(PyExc_IOError, "could not write file");
	return NULL;
    }
    close(fd);

    Py_DECREF(new_array);
    Py_INCREF(Py_None);
    return Py_None;
}

static struct PyMethodDef mmaparray_methods[] = {
    { "read", (PyCFunction)mmaparray_read, METH_VARARGS, mmaparray_read__doc__ },
    { "write", (PyCFunction)mmaparray_write, METH_VARARGS, mmaparray_write__doc__ },
    { NULL, (PyCFunction)NULL, 0, NULL }
};

char mmaparray_module__doc__[] =
"Implements a simple mmap file based Numeric array.  To create a new\n"
"memory mapped array you call the write() function.\n"
"\n"
">>> a = Numeric.array(range(100))\n"
">>> mmaparray.write('blah.dat', a)\n"
"\n"
"To access the array in the file you call the read function.\n"
"\n"
">>> b = mmaparray.read('blah.dat')\n"
"\n"
"The object returned has the type MmapArray.  The only method\n"
"implemented in the MmapArray type is as_array().  This allows\n"
"MmapArray objects to be used in by soomarray.MmapArray UserArray\n"
"class.\n"
"\n"
">>> c = soomarray.MmapArray(b)\n"
;

void initmmaparray(void)
{
    PyObject *module;

    module = Py_InitModule4("mmaparray", mmaparray_methods,
			    mmaparray_module__doc__,
			    (PyObject*)NULL, PYTHON_API_VERSION);
    MmapArray_Type.ob_type = &PyType_Type;

    import_array();
}
