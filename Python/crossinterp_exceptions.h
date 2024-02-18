
/* InterpreterError extends Exception */

static PyTypeObject _PyExc_InterpreterError = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "interpreters.InterpreterError",
    .tp_doc = PyDoc_STR("A cross-interpreter operation failed"),
    //.tp_base = (PyTypeObject *)PyExc_BaseException,
};
PyObject *PyExc_InterpreterError = (PyObject *)&_PyExc_InterpreterError;

/* InterpreterNotFoundError extends InterpreterError */

static PyTypeObject _PyExc_InterpreterNotFoundError = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "interpreters.InterpreterNotFoundError",
    .tp_doc = PyDoc_STR("An interpreter was not found"),
    .tp_base = &_PyExc_InterpreterError,
};
PyObject *PyExc_InterpreterNotFoundError = (PyObject *)&_PyExc_InterpreterNotFoundError;

/* NotShareableError extends ValueError */

static int
_init_not_shareable_error_type(PyInterpreterState *interp)
{
    const char *name = "interpreters.NotShareableError";
    PyObject *base = PyExc_ValueError;
    PyObject *ns = NULL;
    PyObject *exctype = PyErr_NewException(name, base, ns);
    if (exctype == NULL) {
        return -1;
    }

    _PyInterpreterState_GetXIState(interp)->PyExc_NotShareableError = exctype;
    return 0;
}

static void
_fini_not_shareable_error_type(PyInterpreterState *interp)
{
    Py_CLEAR(_PyInterpreterState_GetXIState(interp)->PyExc_NotShareableError);
}

static PyObject *
_get_not_shareable_error_type(PyInterpreterState *interp)
{
    assert(_PyInterpreterState_GetXIState(interp)->PyExc_NotShareableError != NULL);
    return _PyInterpreterState_GetXIState(interp)->PyExc_NotShareableError;
}


/* lifecycle */

static int
init_exceptions(PyInterpreterState *interp)
{
    // builtin static types
    _PyExc_InterpreterError.tp_base = (PyTypeObject *)PyExc_BaseException;
    if (_PyStaticType_InitBuiltin(interp, &_PyExc_InterpreterError) < 0) {
        return -1;
    }
    if (_PyStaticType_InitBuiltin(interp, &_PyExc_InterpreterNotFoundError) < 0) {
        return -1;
    }

    // heap types
    // We would  call _init_not_shareable_error_type() here too,
    // but that leads to ref leaks

    return 0;
}

static void
fini_exceptions(PyInterpreterState *interp)
{
    // Likewise with _fini_not_shareable_error_type().
    _PyStaticType_Dealloc(interp, &_PyExc_InterpreterNotFoundError);
    _PyStaticType_Dealloc(interp, &_PyExc_InterpreterError);
}
