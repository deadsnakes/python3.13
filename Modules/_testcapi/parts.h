#ifndef Py_TESTCAPI_PARTS_H
#define Py_TESTCAPI_PARTS_H

// Always enable assertions
#undef NDEBUG

// The _testcapi extension tests the public C API: header files in Include/ and
// Include/cpython/ directories. The internal C API must not be tested by
// _testcapi: use _testinternalcapi for that.
//
// _testcapi C files can built with the Py_BUILD_CORE_BUILTIN macro defined if
// one of the Modules/Setup files asks to build _testcapi as "static"
// (gh-109723).
//
// The Visual Studio projects builds _testcapi with Py_BUILD_CORE_MODULE.
#undef Py_BUILD_CORE_MODULE
#undef Py_BUILD_CORE_BUILTIN

#include "Python.h"

#ifdef Py_BUILD_CORE
#  error "_testcapi must test the public Python C API, not the internal C API"
#endif

int _PyTestCapi_Init_Vectorcall(PyObject *module);
int _PyTestCapi_Init_Heaptype(PyObject *module);
int _PyTestCapi_Init_Abstract(PyObject *module);
int _PyTestCapi_Init_Unicode(PyObject *module);
int _PyTestCapi_Init_GetArgs(PyObject *module);
int _PyTestCapi_Init_DateTime(PyObject *module);
int _PyTestCapi_Init_Docstring(PyObject *module);
int _PyTestCapi_Init_Mem(PyObject *module);
int _PyTestCapi_Init_Watchers(PyObject *module);
int _PyTestCapi_Init_Long(PyObject *module);
int _PyTestCapi_Init_Float(PyObject *module);
int _PyTestCapi_Init_Dict(PyObject *module);
int _PyTestCapi_Init_Set(PyObject *module);
int _PyTestCapi_Init_Structmember(PyObject *module);
int _PyTestCapi_Init_Exceptions(PyObject *module);
int _PyTestCapi_Init_Code(PyObject *module);
int _PyTestCapi_Init_Buffer(PyObject *module);
int _PyTestCapi_Init_PyAtomic(PyObject *module);
int _PyTestCapi_Init_PyOS(PyObject *module);
int _PyTestCapi_Init_Immortal(PyObject *module);
int _PyTestCapi_Init_GC(PyObject *mod);

int _PyTestCapi_Init_VectorcallLimited(PyObject *module);
int _PyTestCapi_Init_HeaptypeRelative(PyObject *module);

#endif // Py_TESTCAPI_PARTS_H
