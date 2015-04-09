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
#include <ctype.h>

#include "Python.h"
#include "structmember.h"
#include "Numeric/arrayobject.h"

static PyObject *instrument_func = NULL;

#define INSTRUMENT(args) \
    if (instrument_func != Py_None) { \
	PyObject *args_tuple, *result; \
 \
	args_tuple = result = NULL; \
	args_tuple = Py_BuildValue args; \
	if (args_tuple != NULL) \
	    result = PyObject_CallObject(instrument_func, args_tuple); \
	if (result == NULL || args_tuple == NULL) \
	    PyErr_Clear(); \
	Py_XDECREF(result); \
	Py_XDECREF(args_tuple); \
    }

typedef struct {
    PyArrayObject *array;	/* must DECREF once finished */
    char *data;			/* step through array data */
    int stride;			/* distance between each element */
    int index;			/* current array index */
    int len;			/* array length */
} ArrayInfo;

static void free_array_info(ArrayInfo *array_info, int num_arrays)
{
    ArrayInfo *info;
    int i;
    
    for (i = 0, info = array_info; i < num_arrays; i++, info++)
	Py_XDECREF(info->array);
    free(array_info);
}

static void set_array_info(ArrayInfo *info, PyArrayObject *array)
{
    info->array = array;
    info->data = array->data;
    info->stride = array->strides[0];
    info->index = 0;
    info->len = array->dimensions[0];
}

static ArrayInfo *check_array_args(PyObject *args,
				   int min_arrays, int max_arrays,
				   int contiguous)
{
    char msg[128];
    ArrayInfo *array_info, *info;
    int num_arrays, type_num, i;

    num_arrays = PyTuple_Size(args);
    if (num_arrays < min_arrays) {
	sprintf(msg, "at least %d arrays required", min_arrays);
	PyErr_SetString(PyExc_ValueError, msg);
	return NULL;
    }
    if (max_arrays > 0 && num_arrays > max_arrays) {
	sprintf(msg, "more than %d arrays not supported", max_arrays);
	PyErr_SetString(PyExc_ValueError, msg);
	return NULL;
    }
    type_num = -1;
    array_info = malloc(sizeof(*array_info) * num_arrays);
    if (array_info == NULL)
	return (ArrayInfo*)PyErr_NoMemory();
    memset(array_info, 0, sizeof(*array_info) * num_arrays);

    for (i = 0, info = array_info; i < num_arrays; i++, info++) {
	PyObject *arg;
	PyArrayObject *array;

	arg = PyTuple_GetItem(args, i);
	if (arg == NULL)
	    goto error;
	if (contiguous)
	    array = (PyArrayObject *)
		PyArray_ContiguousFromObject(arg, PyArray_NOTYPE, 0, 0);
	else
	    array = (PyArrayObject *)
		PyArray_FromObject(arg, PyArray_NOTYPE, 0, 0);
	if (array == NULL)
	    goto error;
	if (i == 0)
	    type_num = array->descr->type_num;
	else if (array->descr->type_num != type_num) {
	    PyErr_SetString(PyExc_ValueError,
			    "arrays must have the same typecode");
	    goto error;
	}
	if (array->nd != 1) {
	    PyErr_SetString(PyExc_ValueError, "arrays must be rank-1");
	    goto error;
	}
	if (array->descr->type_num == PyArray_CFLOAT
	    || array->descr->type_num == PyArray_CDOUBLE
	    || array->descr->type_num == PyArray_OBJECT
	    || array->descr->type_num == PyArray_NTYPES
	    || array->descr->type_num == PyArray_NOTYPE) {
	    PyErr_SetString(PyExc_ValueError, "unhandled array type");
	    goto error;
	}
	set_array_info(info, array);
    }
    return array_info;

error:
    free_array_info(array_info, num_arrays);
    return NULL;
}

#define unique_func(NAME, TYPE) \
static void NAME(ArrayInfo *info1, ArrayInfo *info2) \
{ \
    while (info1->index < info1->len && info2->index < info2->len) { \
	char *value = info1->data; \
 \
	*(TYPE *)info2->data = *(TYPE *)info1->data; \
	info1->index++; \
	info2->index++; \
	info1->data += info1->stride; \
	info2->data += info2->stride; \
 \
	while (info1->index < info1->len \
	       && *(TYPE *)info1->data == *(TYPE *)value) { \
	    info1->index++; \
	    info1->data += info1->stride; \
	} \
    } \
    info2->len = info2->index; \
}

unique_func(unique_schar, signed char)
unique_func(unique_uchar, unsigned char)
unique_func(unique_short, short)
unique_func(unique_int, int)
unique_func(unique_long, long)
unique_func(unique_float, float)
unique_func(unique_double, double)

static char soomfunc_unique__doc__[] =
"unique(a [,b]) -> array\n"
"\n"
"    Remove all duplicate values from the input rank-1 array returning\n"
"    a new rank-1 array of unique values.  If a second argument is\n"
"    supplied it will be used to store the result.\n";

static PyObject *soomfunc_unique(PyObject *module, PyObject *args)
{
    ArrayInfo *array_info, *info, info_ret;
    int type_num, num_arrays;
    PyArrayObject *ret;

    array_info = check_array_args(args, 1, 2, 0);
    if (array_info == NULL)
	return NULL;
    type_num = array_info->array->descr->type_num;
    num_arrays = PyTuple_Size(args);

    INSTRUMENT(("ssi", "unique", "enter", array_info[0].len));

    if (num_arrays != 2) {
	int shape[1];

	/* Build the array to capture the unique values.
	 */
	shape[0] = array_info->len;
	ret = (PyArrayObject *)PyArray_FromDims(1, shape, type_num);
	if (ret == NULL) {
	    free_array_info(array_info, num_arrays);
	    return NULL;
	}
	set_array_info(&info_ret, ret);
	info = &info_ret;
    } else {
	info = &array_info[1];
	ret = info->array;
    }

    /* Generate the unique array.
     */
    switch (type_num) {
    case PyArray_CHAR:
    case PyArray_SBYTE:
	unique_schar(array_info, info);
	break;
    case PyArray_UBYTE:
	unique_uchar(array_info, info);
	break;
    case PyArray_SHORT:
	unique_short(array_info, info);
	break;
    case PyArray_INT:
	unique_int(array_info, info);
	break;
    case PyArray_LONG:
	unique_long(array_info, info);
	break;
    case PyArray_FLOAT:
	unique_float(array_info, info);
	break;
    case PyArray_DOUBLE: 
	unique_double(array_info, info);
	break;
    }

    ret->dimensions[0] = info->len;

    free_array_info(array_info, num_arrays);

    INSTRUMENT(("ssi", "unique", "exit", ret->dimensions[0]));
    return (PyObject *)ret;
}

#define intersect_func(NAME, TYPE) \
inline int NAME##_search(char *key, char *base, int num, int stride, int mid) \
{ \
    int low, high; \
    char *val; \
 \
    low = 0; \
    high = num - 1; \
    while (low <= high) { \
	val = base + mid * stride; \
	if (*(TYPE*)key < *(TYPE*)val) \
	    high = mid - 1; \
	else if (*(TYPE*)key > *(TYPE*)val) \
	    low = mid + 1; \
	else \
	    return mid; \
	mid = (low + high) / 2; \
    } \
    return mid + 1; \
} \
 \
static void sparse_##NAME(ArrayInfo *info1, ArrayInfo *info2, ArrayInfo *info_res) \
{ \
    char *data1 = info1->array->data; \
    char *data2 = info2->array->data; \
    char *data_res = info_res->array->data; \
    int index1, index2, index_res; \
    int stride1, stride2, stride_res; \
    int len1, len2; \
    int skip1 = 0, skip2 = 0; \
 \
    index1 = index2 = index_res = 0; \
    stride1 = info1->stride; \
    stride2 = info2->stride; \
    stride_res = info_res->stride; \
    len1 = info1->len; \
    len2 = info2->len; \
 \
    INSTRUMENT(("ssii", "sparse_intersect", "enter", len1, len2)); \
 \
    while (index1 < len1 && index2 < len2) { \
	if (*(TYPE *)data1 < *(TYPE *)data2) { \
	    int num1, mid; \
 \
	    num1 = len1 - index1; \
            mid = skip1 * 3; \
	    if (!mid || mid > num1 / 2) \
		mid = num1 / 2; \
	    skip1 = NAME##_search(data2, data1, num1, stride1, mid); \
	    index1 += skip1; \
	    data1 += skip1 * stride1; \
	} else if (*(TYPE *)data2 < *(TYPE *)data1) { \
	    int num2, mid; \
 \
	    num2 = len2 - index2; \
            mid = skip2 * 3; \
	    if (!mid || mid > num2 / 2) \
		mid = num2 / 2; \
	    skip2 = NAME##_search(data1, data2, num2, stride2, mid); \
	    index2 += skip2; \
	    data2 += skip2 * stride2; \
	} else { \
	    char *match_value; \
 \
	    match_value = data1; \
	    *(TYPE *)data_res = *(TYPE *)data1; \
	    index_res++; \
	    data_res += stride_res; \
 \
	    index1++; \
	    data1 += stride1; \
	    while (index1 < len1 && *(TYPE *)data1 == *(TYPE *)match_value) { \
		index1++; \
		data1 += stride1; \
	    } \
	    index2++; \
	    data2 += stride2; \
	    while (index2 < len2 && *(TYPE *)data2 == *(TYPE *)match_value) { \
		index2++; \
		data2 += stride2; \
	    } \
	} \
    } \
    info_res->len = index_res; \
 \
    INSTRUMENT(("ssi", "sparse_intersect", "exit", index_res)); \
 \
} \
 \
static void dense_##NAME(ArrayInfo *info1, ArrayInfo *info2, ArrayInfo *info_res) \
{ \
    char *data1 = info1->array->data; \
    char *data2 = info2->array->data; \
    char *data_res = info_res->array->data; \
    int index1, index2, index_res; \
    int stride1, stride2, stride_res; \
    int len1, len2; \
 \
    index1 = index2 = index_res = 0; \
    stride1 = info1->stride; \
    stride2 = info2->stride; \
    stride_res = info_res->stride; \
    len1 = info1->len; \
    len2 = info2->len; \
 \
    INSTRUMENT(("ssii", "dense_intersect", "enter", len1, len2)); \
 \
    while (index1 < len1 && index2 < len2) { \
	if (*(TYPE *)data1 < *(TYPE *)data2) { \
	    index1++; \
	    data1 += stride1; \
	} else if (*(TYPE *)data2 < *(TYPE *)data1) { \
	    index2++; \
	    data2 += stride2; \
	} else { \
	    char *match_value; \
 \
	    match_value = data1; \
	    *(TYPE *)data_res = *(TYPE *)data1; \
	    index_res++; \
	    data_res += info_res->stride; \
 \
	    index1++; \
	    data1 += stride1; \
	    while (index1 < len1 \
		   && *(TYPE *)data1 == *(TYPE *)match_value) { \
		index1++; \
		data1 += stride1; \
	    } \
	    index2++; \
	    data2 += stride2; \
	    while (index2 < len2 \
		   && *(TYPE *)data2 == *(TYPE *)match_value) { \
		index2++; \
		data2 += stride2; \
	    } \
	} \
    } \
    info_res->len = index_res; \
 \
    INSTRUMENT(("ssi", "dense_intersect", "exit", index_res)); \
 \
} \
 \
static void NAME(ArrayInfo *info1, ArrayInfo *info2, ArrayInfo *info_res) \
{ \
    if (info1->len > info2->len) { \
	if (info2->len > 0 && info1->len / info2->len >= 3) \
	    sparse_##NAME(info1, info2, info_res); \
	else \
	    dense_##NAME(info1, info2, info_res); \
    } else if (info1->len > 0 && info2->len / info1->len >= 3) \
	sparse_##NAME(info1, info2, info_res); \
    else \
	dense_##NAME(info1, info2, info_res); \
}

intersect_func(intersect_schar, signed char)
intersect_func(intersect_uchar, unsigned char)
intersect_func(intersect_short, short)
intersect_func(intersect_int, int)
intersect_func(intersect_long, long)
intersect_func(intersect_float, float)
intersect_func(intersect_double, double)

typedef void (*IntersectFunc)(ArrayInfo *info1, ArrayInfo *info2,
			      ArrayInfo *info_res);

typedef struct {
    IntersectFunc schar_func;
    IntersectFunc uchar_func;
    IntersectFunc short_func;
    IntersectFunc int_func;
    IntersectFunc long_func;
    IntersectFunc float_func;
    IntersectFunc double_func;
} IntersectTable;

static int ai_size_cmp(const void *info1, const void *info2)
{
    return (((ArrayInfo *)info1)->len - ((ArrayInfo *)info2)->len);
}

static PyObject *intersect_with(IntersectTable *table, PyObject *args)
{
    ArrayInfo *array_info, info1, *info2, info_ret;
    PyArrayObject *ret;
    int shape[1];
    int alloc_size, i;
    int type_num, num_arrays;

    array_info = check_array_args(args, 2, -1, 0);
    if (array_info == NULL)
	return NULL;
    type_num = array_info->array->descr->type_num;
    num_arrays = PyTuple_Size(args);

    /* These algorithms are much faster if they are applied smallest array to
     * largest, so we sort the array list (this will, however, be a net loss
     * in the degenerate case of lots of small arrays) */
    qsort(array_info, num_arrays, sizeof(*array_info), ai_size_cmp);

    alloc_size = array_info->len;

    /* Build the array to capture the intersection */
    shape[0] = alloc_size;
    ret = (PyArrayObject *)PyArray_FromDims(1, shape, type_num);
    if (ret == NULL) {
	free_array_info(array_info, num_arrays);
	return NULL;
    }
    set_array_info(&info_ret, ret);

    /* Generate the intersection.  Intersect the smallest array with
     * each other array - after each operation subsitute the result
     * for the smallest array.
     */
    info1 = *array_info;
    i = 1;
    info2 = array_info + 1;
    while (i < num_arrays && info1.len > 0)
    {
	switch (type_num) {
	case PyArray_CHAR:
	case PyArray_SBYTE:
	    table->schar_func(&info1, info2, &info_ret);
	    break;
	case PyArray_UBYTE:
	    table->uchar_func(&info1, info2, &info_ret);
	    break;
	case PyArray_SHORT:
	    table->short_func(&info1, info2, &info_ret);
	    break;
	case PyArray_INT:
	    table->int_func(&info1, info2, &info_ret);
	    break;
	case PyArray_LONG:
	    table->long_func(&info1, info2, &info_ret);
	    break;
	case PyArray_FLOAT:
	    table->float_func(&info1, info2, &info_ret);
	    break;
	case PyArray_DOUBLE: 
	    table->double_func(&info1, info2, &info_ret);
	    break;
	}
	info1 = info_ret;
	i++;
	info2++;
    }
    free_array_info(array_info, num_arrays);

    ret->dimensions[0] = info_ret.len;
    return (PyObject *)ret;
}

static char soomfunc_intersect__doc__[] =
"intersect(a, b, ...) -> array\n"
"\n"
"    Return the intersection of the rank-1 arrays passed.  All arrays\n"
"    must have the same typecode.\n";

static PyObject *soomfunc_intersect(PyObject *module, PyObject *args)
{
    static IntersectTable intersect = {
	intersect_schar,
	intersect_uchar,
	intersect_short,
	intersect_int,
	intersect_long,
	intersect_float,
	intersect_double
    };

    return intersect_with(&intersect, args);
}

static char soomfunc_dense_intersect__doc__[] =
"dense_intersect(a, b, ...) -> array\n"
"\n"
"    Return the intersection of the rank-1 arrays passed.  All arrays\n"
"    must have the same typecode.\n";

static PyObject *soomfunc_dense_intersect(PyObject *module, PyObject *args)
{
    static IntersectTable dense_intersect = {
	dense_intersect_schar,
	dense_intersect_uchar,
	dense_intersect_short,
	dense_intersect_int,
	dense_intersect_long,
	dense_intersect_float,
	dense_intersect_double
    };

    return intersect_with(&dense_intersect, args);
}

static char soomfunc_sparse_intersect__doc__[] =
"sparse_intersect(a, b, ...) -> array\n"
"\n"
"    Return the intersection of the rank-1 arrays passed.  All arrays\n"
"    must have the same typecode.\n";

static PyObject *soomfunc_sparse_intersect(PyObject *module, PyObject *args)
{
    static IntersectTable sparse_intersect = {
	sparse_intersect_schar,
	sparse_intersect_uchar,
	sparse_intersect_short,
	sparse_intersect_int,
	sparse_intersect_long,
	sparse_intersect_float,
	sparse_intersect_double
    };

    return intersect_with(&sparse_intersect, args);
}

#define outersect_func(NAME, TYPE) \
static PyObject *NAME(ArrayInfo *array_info, int num_arrays) \
{ \
    ArrayInfo *info; \
    int type_num, i, out_size, out_len; \
    TYPE *out_data; \
 \
    out_size = type_num = 0; \
    for (info = array_info, i = 0; i < num_arrays; info++, i++) { \
	type_num = info->array->descr->type_num; \
	if (info->len > out_size) \
	    out_size = info->len; \
    } \
    out_size /= 2; \
 \
    out_len = 0; \
    out_data = malloc(out_size * sizeof(TYPE)); \
    if (out_data == NULL) { \
	PyErr_SetString(PyExc_MemoryError, "can't allocate memory for array"); \
	return NULL; \
    } \
 \
    for (;;) { \
	ArrayInfo *use_info = NULL; \
	int duplicate_count = 0; \
 \
	/* Find the minimum unique value \
	 */ \
	for (info = array_info, i = 0; i < num_arrays; info++, i++) { \
	    if (info->index < info->len) { \
		if (use_info == NULL) { \
		    /* Minimum unique value is here (I think) \
		     */ \
		    use_info = info; \
		    duplicate_count = 1; \
		} else if (*(TYPE *)info->data < *(TYPE *)use_info->data) { \
		    /* Nope - minimum unique value is here (I think) \
		     */ \
		    use_info = info; \
		    duplicate_count = 1; \
		} else if (*(TYPE *)info->data == *(TYPE *)use_info->data) { \
		    /* Nope - minimum (I think) value has duplicate \
		     */ \
		    duplicate_count++; \
		} \
	    } \
	} \
	/* Now handle minimum value search result \
	 */ \
	if (duplicate_count) { \
	    char *data = use_info->data; \
 \
	    if (duplicate_count < num_arrays) { \
		/* Woohoo - found a minimum value which is not in all sets \
		 */ \
		if (out_len == out_size) { \
		    TYPE *new_data; \
 \
		    out_size *= 2; \
		    new_data = realloc(out_data, out_size * sizeof(TYPE)); \
		    if (new_data == NULL) { \
			PyErr_SetString(PyExc_MemoryError, "can't allocate memory for array"); \
			free(out_data); \
			return NULL; \
		    } \
		    out_data = new_data; \
		} \
		out_data[out_len++] = *(TYPE *)use_info->data; \
	    } \
	    /* Skip over all duplicate values \
	     */ \
	    for (info = array_info, i = 0; i < num_arrays; info++, i++) { \
		while (info->index < info->len \
		       && *(TYPE *)info->data == *(TYPE *)data) { \
		    info->data += info->stride; \
		    info->index++; \
		} \
	    } \
	} else { \
	    /* Finished scanning all arrays \
	     */ \
	    PyArrayObject *ret; \
	    int shape[1]; \
 \
	    shape[0] = out_len; \
	    ret = (PyArrayObject *) \
		PyArray_FromDimsAndData(1, shape, type_num, (char *)out_data); \
	    if (ret) \
		ret->flags |= OWN_DATA; \
	    else \
		free(out_data); \
 \
	    return (PyObject *)ret; \
	} \
    } \
}

outersect_func(outersect_schar, signed char)
outersect_func(outersect_uchar, unsigned char)
outersect_func(outersect_short, short)
outersect_func(outersect_int, int)
outersect_func(outersect_long, long)
outersect_func(outersect_float, float)
outersect_func(outersect_double, double)

static char soomfunc_outersect__doc__[] =
"outersect(a, b, ...) -> array\n"
"\n"
"    Return the symmetric difference of the rank-1 arrays\n"
"    passed.  All arrays must have the same typecode.\n";

static PyObject *soomfunc_outersect(PyObject *module, PyObject *args)
{
    ArrayInfo *array_info;
    PyArrayObject *ret;
    int type_num, num_arrays;

    array_info = check_array_args(args, 2, -1, 0);
    if (array_info == NULL)
	return NULL;
    type_num = array_info->array->descr->type_num;
    num_arrays = PyTuple_Size(args);

    INSTRUMENT(("ssi", "outersect", "enter", num_arrays));

    /* Accumulate the difference cumulatively by comparing the first
     * two arrays then comparing the result with the third and so on.
     */
    ret = NULL;
    switch (type_num) {
    case PyArray_CHAR:
    case PyArray_SBYTE:
	ret = (PyArrayObject *)outersect_schar(array_info, num_arrays);
	break;
    case PyArray_UBYTE:
	ret = (PyArrayObject *)outersect_uchar(array_info, num_arrays);
	break;
    case PyArray_SHORT:
	ret = (PyArrayObject *)outersect_short(array_info, num_arrays);
	break;
    case PyArray_INT:
	ret = (PyArrayObject *)outersect_int(array_info, num_arrays);
	break;
    case PyArray_LONG:
	ret = (PyArrayObject *)outersect_long(array_info, num_arrays);
	break;
    case PyArray_FLOAT:
	ret = (PyArrayObject *)outersect_float(array_info, num_arrays);
	break;
    case PyArray_DOUBLE: 
	ret = (PyArrayObject *)outersect_double(array_info, num_arrays);
	break;
    default:
	PyErr_SetString(PyExc_ValueError, "bogus - unhandled array type");
    }
    free_array_info(array_info, num_arrays);

    INSTRUMENT(("ssi", "outersect", "exit", ret->dimensions[0]));
    return (PyObject *)ret;
}

#define sparse_union_func(NAME, TYPE) \
static PyObject *sparse_##NAME(ArrayInfo *array_info, int num_arrays) \
{ \
    ArrayInfo *info; \
    int type_num, i, out_size, out_len; \
    TYPE *out_data; \
 \
    out_size = type_num = 0; \
    for (info = array_info, i = 0; i < num_arrays; info++, i++) { \
	type_num = info->array->descr->type_num; \
	if (info->len > out_size) \
	    out_size = info->len; \
    } \
 \
    out_len = 0; \
    out_data = malloc(out_size * sizeof(TYPE)); \
    if (out_data == NULL) { \
	PyErr_SetString(PyExc_MemoryError, "can't allocate memory for array"); \
	return NULL; \
    } \
 \
    for (;;) { \
	ArrayInfo *use_info = NULL; \
	int have_duplicate = 0; \
 \
	/* Find the minimum value \
	 */ \
	for (info = array_info, i = 0; i < num_arrays; info++, i++) { \
	    if (info->index < info->len) { \
		if (use_info == NULL) \
		    /* Minimum value is here (I think) \
		     */ \
		    use_info = info; \
		else if (*(TYPE *)info->data < *(TYPE *)use_info->data) { \
		    /* Nope - minimum value is here (I think) \
		     */ \
		    use_info = info; \
		    have_duplicate = 0; \
		} else if (*(TYPE *)info->data == *(TYPE *)use_info->data) { \
		    /* Nope - minimum (I think) value has duplicate \
		     */ \
		    have_duplicate = 1; \
		} \
	    } \
	} \
	/* Now handle minimum value search result \
	 */ \
	if (use_info) { \
	    /* Woohoo - found a minimum value \
	     */ \
	    char *data = use_info->data; \
 \
	    if (out_len == out_size) { \
		TYPE *new_data; \
 \
		out_size *= 2; \
		new_data = realloc(out_data, out_size * sizeof(TYPE)); \
		if (new_data == NULL) { \
		    PyErr_SetString(PyExc_MemoryError, "can't allocate memory for array"); \
		    free(out_data); \
		    return NULL; \
		} \
		out_data = new_data; \
	    } \
	    out_data[out_len++] = *(TYPE *)use_info->data; \
 \
	    if (have_duplicate) { \
		/* Skip over all duplicate values \
		 */ \
		char *data = use_info->data; \
		for (info = array_info, i = 0; i < num_arrays; info++, i++) { \
		    while (info->index < info->len \
			   && *(TYPE *)info->data == *(TYPE *)data) { \
			info->data += info->stride; \
			info->index++; \
		    } \
		} \
	    } else { \
		while (use_info->index < use_info->len \
		       && *(TYPE *)use_info->data == *(TYPE *)data) { \
		    use_info->data += use_info->stride; \
		    use_info->index++; \
		} \
	    } \
	} else { \
	    /* Finished scanning all arrays \
	     */ \
	    PyArrayObject *ret; \
	    int shape[1]; \
 \
	    shape[0] = out_len; \
	    ret = (PyArrayObject *) \
		PyArray_FromDimsAndData(1, shape, type_num, (char *)out_data); \
	    if (ret) \
		ret->flags |= OWN_DATA; \
	    else \
		free(out_data); \
	    return (PyObject *)ret; \
	} \
    } \
}

#define dense_union_func(NAME, TYPE) \
static PyObject *dense_##NAME(ArrayInfo *array_info, int num_arrays) \
{ \
    int type_num = 0, i, v; \
    ArrayInfo *info; \
    TYPE min = 0, max = 0, *p; \
    unsigned long arg_tot_len, range, out_size; \
    unsigned char *map; \
    int shape[1]; \
    PyArrayObject *ret; \
 \
    info = array_info; \
    arg_tot_len = 0; \
    for (i = 0; i < num_arrays; i++) { \
        type_num = info->array->descr->type_num; \
        if (info->len) { \
            if (!arg_tot_len || *(TYPE *)info->data < min) \
                min = *(TYPE *)info->data; \
            if (!arg_tot_len || *(TYPE *)(info->data + info->stride * (info->len - 1)) > max) \
                max = *(TYPE *)(info->data + info->stride * (info->len - 1)); \
            arg_tot_len += info->len; \
        } \
        info++; \
    } \
    if (!arg_tot_len) { \
        shape[0] = 0; \
        return (PyObject *)PyArray_FromDims(1, shape, type_num); \
    } \
    range = max - min + 1; \
/*    printf("num_arrays %d, min %ld, max %ld, range %ld, arg_tot_len %ld, sparse %d\n", \
           num_arrays, (long)min, (long)max, (long)range, (long)arg_tot_len, \
           ((range / arg_tot_len) >= 3)); */ \
    if ((range / arg_tot_len) >= 3) \
        return sparse_##NAME(array_info, num_arrays); \
    map = malloc(range); \
    if (map == NULL) { \
	PyErr_SetString(PyExc_MemoryError, "can't allocate memory for array"); \
	return NULL; \
    } \
    memset(map, 0, range); \
    out_size = 0; \
    for (info = array_info, i = 0; i < num_arrays; info++, i++) { \
        for (; info->index < info->len; ++info->index) { \
            v = *(TYPE *)info->data - min; \
            if (v < 0 || v >= range) { \
                PyErr_SetString(PyExc_ValueError, "arrays must be sorted"); \
                free(map); \
                return NULL; \
            } \
            if (!map[v]) { \
                ++out_size; \
                map[v] = 1; \
            } \
            info->data += info->stride; \
        } \
    } \
    shape[0] = out_size; \
    ret = (PyArrayObject *)PyArray_FromDims(1, shape, type_num); \
    if (ret == NULL) { \
        free(map); \
        return NULL; \
    } \
    for (i = 0, p = (TYPE*)ret->data; i < range; ++i) \
        if (map[i]) \
            *p++ = i + min; \
    free(map); \
    return (PyObject *)ret; \
}

sparse_union_func(union_schar, signed char)
sparse_union_func(union_uchar, unsigned char)
sparse_union_func(union_short, short)
sparse_union_func(union_int, int)
sparse_union_func(union_long, long)
sparse_union_func(union_float, float)
sparse_union_func(union_double, double)
dense_union_func(union_schar, signed char)
dense_union_func(union_uchar, unsigned char)
dense_union_func(union_short, short)
dense_union_func(union_int, int)
dense_union_func(union_long, long)

static char soomfunc_union__doc__[] =
"union(a, b, ...) -> array\n"
"\n"
"    Return the union of the rank-1 arrays passed.  All arrays must\n"
"    have the same typecode.\n";

static PyObject *soomfunc_union(PyObject *module, PyObject *args)
{
    ArrayInfo *array_info;
    PyArrayObject *ret;
    int type_num, num_arrays;

    array_info = check_array_args(args, 2, -1, 0);
    if (array_info == NULL)
	return NULL;
    type_num = array_info->array->descr->type_num;
    num_arrays = PyTuple_Size(args);

    INSTRUMENT(("ssi", "union", "enter", num_arrays));

    /* Accumulate the difference cumulatively by comparing the first
     * two arrays then comparing the result with the third and so on.
     */
    ret = NULL;
    switch (type_num) {
    case PyArray_CHAR:
    case PyArray_SBYTE:
        ret = (PyArrayObject *)dense_union_schar(array_info, num_arrays);
	break;
    case PyArray_UBYTE:
        ret = (PyArrayObject *)dense_union_uchar(array_info, num_arrays);
	break;
    case PyArray_SHORT:
        ret = (PyArrayObject *)dense_union_short(array_info, num_arrays);
	break;
    case PyArray_INT:
        ret = (PyArrayObject *)dense_union_int(array_info, num_arrays);
	break;
    case PyArray_LONG:
        ret = (PyArrayObject *)dense_union_long(array_info, num_arrays);
	break;
    case PyArray_FLOAT:
	ret = (PyArrayObject *)sparse_union_float(array_info, num_arrays);
	break;
    case PyArray_DOUBLE: 
	ret = (PyArrayObject *)sparse_union_double(array_info, num_arrays);
	break;
    default:
	PyErr_SetString(PyExc_ValueError, "bogus - unhandled array type");
    }
    free_array_info(array_info, num_arrays);

    INSTRUMENT(("ssi", "union", "exit", ret->dimensions[0]));
    return (PyObject *)ret;
}

#define difference_func(NAME, TYPE) \
static void NAME(ArrayInfo *info1, ArrayInfo *info2, ArrayInfo *info_res) \
{ \
    char *prev; \
 \
    info1->data = info1->array->data; \
    info2->data = info2->array->data; \
    info_res->data = info_res->array->data; \
    info1->index = info2->index = info_res->index = 0; \
 \
    INSTRUMENT(("ssii", "difference", "enter", info1->len, info2->len)); \
 \
    while (info1->index < info1->len && info2->index < info2->len) { \
	if (*(TYPE *)info1->data < *(TYPE *)info2->data) { \
	    *(TYPE *)info_res->data = *(TYPE *)info1->data; \
	    info_res->index++; \
	    info_res->data += info_res->stride; \
 \
	    prev = info1->data; \
	    info1->index++; \
	    info1->data += info1->stride; \
 \
	    while (info1->index < info1->len \
		   && *(TYPE *)info1->data == *(TYPE *)prev) { \
		info1->index++; \
		info1->data += info1->stride; \
	    } \
	} else if (*(TYPE *)info2->data < *(TYPE *)info1->data) { \
	    info2->index++; \
	    info2->data += info2->stride; \
	} else { \
	    prev = info1->data; \
 \
	    info1->index++; \
	    info1->data += info1->stride; \
	    while (info1->index < info1->len \
		   && *(TYPE *)info1->data == *(TYPE *)prev) { \
		info1->index++; \
		info1->data += info1->stride; \
	    } \
	    info2->index++; \
	    info2->data += info2->stride; \
	    while (info2->index < info2->len \
		   && *(TYPE *)info2->data == *(TYPE *)prev) { \
		info2->index++; \
		info2->data += info2->stride; \
	    } \
	} \
    } \
    while (info1->index < info1->len) { \
	*(TYPE *)info_res->data = *(TYPE *)info1->data; \
	info_res->index++; \
	info_res->data += info_res->stride; \
 \
	prev = info1->data; \
	info1->index++; \
	info1->data += info1->stride; \
 \
	while (info1->index < info1->len \
	       && *(TYPE *)info1->data == *(TYPE *)prev) { \
	    info1->index++; \
	    info1->data += info1->stride; \
	} \
    } \
 \
    info_res->len = info_res->index; \
 \
    INSTRUMENT(("ssi", "difference", "exit", info_res->len)); \
}

difference_func(difference_schar, signed char)
difference_func(difference_uchar, unsigned char)
difference_func(difference_short, short)
difference_func(difference_int, int)
difference_func(difference_long, long)
difference_func(difference_float, float)
difference_func(difference_double, double)

static char soomfunc_difference__doc__[] =
"difference(a, b, ...) -> array\n"
"\n"
"    Return the result of subtracting the second and subsequent rank-1\n"
"    arrays from the first rank-1 array.  All arrays must have the same\n"
"    typecode.\n";

static PyObject *soomfunc_difference(PyObject *module, PyObject *args)
{
    ArrayInfo *array_info, info1, *info2, info_ret;
    PyArrayObject *ret;
    int shape[1];
    int alloc_size, i;
    int type_num, num_arrays;

    array_info = check_array_args(args, 2, -1, 0);
    if (array_info == NULL)
	return NULL;
    type_num = array_info->array->descr->type_num;
    num_arrays = PyTuple_Size(args);

    alloc_size = array_info->len;

    /* Build the array to capture the intersection */
    shape[0] = alloc_size;
    ret = (PyArrayObject *)PyArray_FromDims(1, shape, type_num);
    if (ret == NULL) {
	free_array_info(array_info, num_arrays);
	return NULL;
    }
    set_array_info(&info_ret, ret);

    /* Generate the difference.  Subtract the second array from the
     * first - after each operation subsitute the result for the first
     * array.
     */
    info1 = array_info[0];
    for (i = 1, info2 = array_info + 1; i < num_arrays; i++, info2++) {
	switch (type_num) {
	case PyArray_CHAR:
	case PyArray_SBYTE:
	    difference_schar(&info1, info2, &info_ret);
	    break;
	case PyArray_UBYTE:
	    difference_uchar(&info1, info2, &info_ret);
	    break;
	case PyArray_SHORT:
	    difference_short(&info1, info2, &info_ret);
	    break;
	case PyArray_INT:
	    difference_int(&info1, info2, &info_ret);
	    break;
	case PyArray_LONG:
	    difference_long(&info1, info2, &info_ret);
	    break;
	case PyArray_FLOAT:
	    difference_float(&info1, info2, &info_ret);
	    break;
	case PyArray_DOUBLE: 
	    difference_double(&info1, info2, &info_ret);
	    break;
	}
	info1 = info_ret;
    }
    free_array_info(array_info, num_arrays);

    ret->dimensions[0] = info_ret.len;
    return (PyObject *)ret;
}

#define valuepos_func(NAME, TYPE) \
static void NAME(ArrayInfo *info1, ArrayInfo *info2, ArrayInfo *info_res) \
{ \
    int index1, index_res; \
    TYPE *data1; \
    long *data_res; \
 \
    data1 = (TYPE*)info1->array->data; \
    data_res = (long*)info_res->array->data; \
    for (index1 = index_res = 0; index1 < info1->len; index1++, data1++) { \
	int index2; \
	TYPE *data2; \
 \
	data2 = (TYPE*)info2->array->data; \
	for (index2 = 0; index2 < info2->len; index2++, data2++) \
	    if (*data1 == *data2) { \
		*data_res++ = (long)index1; \
		index_res++; \
	    } \
    } \
    info_res->len = index_res; \
}

valuepos_func(valuepos_schar, signed char)
valuepos_func(valuepos_uchar, unsigned char)
valuepos_func(valuepos_short, short)
valuepos_func(valuepos_int, int)
valuepos_func(valuepos_long, long)
valuepos_func(valuepos_float, float)
valuepos_func(valuepos_double, double)

static char soomfunc_valuepos__doc__[] =
"valuepos(a, b) -> array\n"
"\n"
"    Return the equivalent of the following (where the result is c):\n"
"    c = []\n"
"    for i in range(len(a)):\n"
"        if a[i] in b:\n"
"            c.append(i)\n"
"    c = array(c)\n";

static PyObject *soomfunc_valuepos(PyObject *module, PyObject *args)
{
    ArrayInfo *array_info, info_ret;
    PyArrayObject *ret;
    int shape[1];
    int alloc_size;
    int type_num, num_arrays;

    array_info = check_array_args(args, 2, 2, 0);
    if (array_info == NULL)
	return NULL;
    type_num = array_info->array->descr->type_num;
    num_arrays = PyTuple_Size(args);

    alloc_size = array_info->len;

    INSTRUMENT(("ssii", "valuepos", "enter", array_info[0].len, array_info[1].len));

    /* Build the array to capture the result */
    shape[0] = alloc_size;
    ret = (PyArrayObject *)PyArray_FromDims(1, shape, PyArray_LONG);
    if (ret == NULL) {
	free_array_info(array_info, num_arrays);
	return NULL;
    }
    set_array_info(&info_ret, ret);

    /* Generate the valuepos.
     */
    switch (type_num) {
    case PyArray_CHAR:
    case PyArray_SBYTE:
	valuepos_schar(&array_info[0], &array_info[1], &info_ret);
	break;
    case PyArray_UBYTE:
	valuepos_uchar(&array_info[0], &array_info[1], &info_ret);
	break;
    case PyArray_SHORT:
	valuepos_short(&array_info[0], &array_info[1], &info_ret);
	break;
    case PyArray_INT:
	valuepos_int(&array_info[0], &array_info[1], &info_ret);
	break;
    case PyArray_LONG:
	valuepos_long(&array_info[0], &array_info[1], &info_ret);
	break;
    case PyArray_FLOAT:
	valuepos_float(&array_info[0], &array_info[1], &info_ret);
	break;
    case PyArray_DOUBLE: 
	valuepos_double(&array_info[0], &array_info[1], &info_ret);
	break;
    }
    free_array_info(array_info, num_arrays);

    ret->dimensions[0] = info_ret.len;

    INSTRUMENT(("ssi", "valuepos", "exit", info_ret.len));
    return (PyObject *)ret;
}

#define preload_func(NAME, TYPE) \
static void NAME(PyArrayObject *array, int preload) \
{ \
    int step; \
    volatile TYPE *data; \
 \
    step = 4096 / sizeof(TYPE) / 2; \
    for (data = ((volatile TYPE *)array->data) + preload; \
	 preload >= 0; preload -= step, data -= step) \
      *data; \
}

preload_func(preload_schar, signed char)
preload_func(preload_uchar, unsigned char)
preload_func(preload_short, short)
preload_func(preload_int, int)
preload_func(preload_long, long)
preload_func(preload_float, float)
preload_func(preload_double, double)

static char soomfunc_preload__doc__[] =
"preload(a, num) -> array\n"
"\n"
"    Step backwards over num entries of the array forcing the pages\n"
"    into memory.\n";

static PyObject *soomfunc_preload(PyObject *module, PyObject *args)
{
    PyObject *obj;
    PyArrayObject *array;
    int preload = -1;

    if (!PyArg_ParseTuple(args, "O|i", &obj, &preload))
	return NULL;
    array = (PyArrayObject *)PyArray_FromObject(obj, PyArray_NOTYPE, 0, 0);
    if (array == NULL)
	return NULL;
    if (array->nd != 1) {
	PyErr_SetString(PyExc_ValueError, "arrays must be rank-1");
	Py_DECREF(array);
	return NULL;
    }

    if (preload < 0 || preload > array->dimensions[0])
	preload = array->dimensions[0] - 1;

    INSTRUMENT(("ssi", "preload", "enter", preload));

    switch (array->descr->type_num) {
    case PyArray_CHAR:
    case PyArray_SBYTE:
	preload_schar(array, preload);
	break;
    case PyArray_UBYTE:
	preload_uchar(array, preload);
	break;
    case PyArray_SHORT:
	preload_short(array, preload);
	break;
    case PyArray_INT:
	preload_int(array, preload);
	break;
    case PyArray_LONG:
	preload_long(array, preload);
	break;
    case PyArray_FLOAT:
	preload_float(array, preload);
	break;
    case PyArray_DOUBLE: 
	preload_double(array, preload);
	break;
    }

    Py_DECREF(array);
    Py_INCREF(Py_None);

    INSTRUMENT(("ss", "preload", "exit"));
    return Py_None;
}

static char soomfunc_set_instrument__doc__[] = 
"set_instrument(func) -> old_func";

static PyObject *soomfunc_set_instrument(PyObject *module, PyObject *args)
{
    PyObject *obj, *res;

    if (!PyArg_ParseTuple(args, "O", &obj))
	return NULL;

    res = instrument_func;
    instrument_func = obj;
    Py_INCREF(instrument_func);
    return res;
}

static char soomfunc_strip_word__doc__[] = 
"strip_word(string) -> string"
"\n"
"    Remove ' from a string and convert to uppercase.\n";

static PyObject *soomfunc_strip_word(PyObject *module, PyObject *args)
{
    PyObject *res;
    char *word, *new_word, *p, *q;
    int word_length;

    if (!PyArg_ParseTuple(args, "s#", &word, &word_length))
	return NULL;
    if (!(new_word = malloc(word_length))) {
	PyErr_SetString(PyExc_MemoryError, "could not allocate new string");
	return NULL;
    }
    for (p = word, q = new_word; word_length; word_length--) {
	if (*p == '\'')
	    p++;
	else
	    *q++ = toupper(*p++);
    }

    res = Py_BuildValue("s#", new_word, q - new_word);
    free(new_word);
    return res;
}

static struct PyMethodDef soomfunc_methods[] = {
    { "unique", (PyCFunction)soomfunc_unique, METH_VARARGS, soomfunc_unique__doc__ },
    { "intersect", (PyCFunction)soomfunc_intersect, METH_VARARGS, soomfunc_intersect__doc__ },
    { "sparse_intersect", (PyCFunction)soomfunc_sparse_intersect, METH_VARARGS, soomfunc_sparse_intersect__doc__ },
    { "dense_intersect", (PyCFunction)soomfunc_dense_intersect, METH_VARARGS, soomfunc_dense_intersect__doc__ },
    { "outersect", (PyCFunction)soomfunc_outersect, METH_VARARGS, soomfunc_outersect__doc__ },
    { "union", (PyCFunction)soomfunc_union, METH_VARARGS, soomfunc_union__doc__ },
    { "difference", (PyCFunction)soomfunc_difference, METH_VARARGS, soomfunc_difference__doc__ },
    { "valuepos", (PyCFunction)soomfunc_valuepos, METH_VARARGS, soomfunc_valuepos__doc__ },
    { "preload", (PyCFunction)soomfunc_preload, METH_VARARGS, soomfunc_preload__doc__ },

    { "set_instrument", (PyCFunction)soomfunc_set_instrument, METH_VARARGS, soomfunc_set_instrument__doc__ },
    { "strip_word", (PyCFunction)soomfunc_strip_word, METH_VARARGS, soomfunc_strip_word__doc__ },
    { NULL, (PyCFunction)NULL, 0, NULL } /* sentinel */
};

static char soomfunc_module__doc__[] =
"A collection of Numpy extension and other utility functions\n"
"intended for use in the SOOM and prototype mortality analysis\n"
"system project.\n";

void initsoomfunc(void)
{
    PyObject *module, *dict, *ver = NULL;

    /* Create the module and add the functions */
    module = Py_InitModule4("soomfunc", soomfunc_methods,
                            soomfunc_module__doc__,
                            (PyObject*)NULL, PYTHON_API_VERSION);
    if (module == NULL)
        goto error;

    /* Set instrument func to None */
    instrument_func = Py_None;
    Py_INCREF(instrument_func);

    import_array();
    if ((dict = PyModule_GetDict(module)) == NULL)
	goto error;
    if ((ver = PyString_FromString("0.8")) == NULL)
        goto error;
    if (PyDict_SetItemString(dict, "__version__", ver) < 0)
        goto error;

error:
    Py_XDECREF(ver);
    /* Check for errors */
    if (PyErr_Occurred())
        Py_FatalError("can't initialize module soomfunc");
}
