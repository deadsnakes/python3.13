// _testclinic_limited can built with the Py_BUILD_CORE_BUILTIN macro defined
// if one of the Modules/Setup files asks to build it as "static" (gh-109723).
#undef Py_BUILD_CORE
#undef Py_BUILD_CORE_MODULE
#undef Py_BUILD_CORE_BUILTIN

// For now, only limited C API 3.13 is supported
#define Py_LIMITED_API 0x030d0000

/* Always enable assertions */
#undef NDEBUG

#include "Python.h"


#include "clinic/_testclinic_limited.c.h"


/*[clinic input]
module  _testclinic_limited
[clinic start generated code]*/
/*[clinic end generated code: output=da39a3ee5e6b4b0d input=dd408149a4fc0dbb]*/


/*[clinic input]
test_empty_function

[clinic start generated code]*/

static PyObject *
test_empty_function_impl(PyObject *module)
/*[clinic end generated code: output=0f8aeb3ddced55cb input=0dd7048651ad4ae4]*/
{
    Py_RETURN_NONE;
}


/*[clinic input]
my_int_func -> int

    arg: int
    /

[clinic start generated code]*/

static int
my_int_func_impl(PyObject *module, int arg)
/*[clinic end generated code: output=761cd54582f10e4f input=16eb8bba71d82740]*/
{
    return arg;
}


/*[clinic input]
my_int_sum -> int

    x: int
    y: int
    /

[clinic start generated code]*/

static int
my_int_sum_impl(PyObject *module, int x, int y)
/*[clinic end generated code: output=3e52db9ab5f37e2f input=0edb6796813bf2d3]*/
{
    return x + y;
}


static PyMethodDef tester_methods[] = {
    TEST_EMPTY_FUNCTION_METHODDEF
    MY_INT_FUNC_METHODDEF
    MY_INT_SUM_METHODDEF
    {NULL, NULL}
};

static struct PyModuleDef _testclinic_module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_testclinic_limited",
    .m_size = 0,
    .m_methods = tester_methods,
};

PyMODINIT_FUNC
PyInit__testclinic_limited(void)
{
    PyObject *m = PyModule_Create(&_testclinic_module);
    if (m == NULL) {
        return NULL;
    }
    return m;
}
