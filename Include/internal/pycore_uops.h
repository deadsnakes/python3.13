#ifndef Py_INTERNAL_UOPS_H
#define Py_INTERNAL_UOPS_H
#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#  error "this header requires Py_BUILD_CORE define"
#endif

#include "pycore_frame.h"         // _PyInterpreterFrame

#define _Py_UOP_MAX_TRACE_LENGTH 128

typedef struct {
    uint32_t opcode;
    uint32_t oparg;
    uint64_t operand;  // A cache entry
} _PyUOpInstruction;

typedef struct {
    _PyExecutorObject base;
    _PyUOpInstruction trace[1];
} _PyUOpExecutorObject;

_PyInterpreterFrame *_PyUopExecute(
    _PyExecutorObject *executor,
    _PyInterpreterFrame *frame,
    PyObject **stack_pointer);

#ifdef __cplusplus
}
#endif
#endif /* !Py_INTERNAL_UOPS_H */
