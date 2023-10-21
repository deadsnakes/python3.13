#ifndef Py_INTERNAL_OPTIMIZER_H
#define Py_INTERNAL_OPTIMIZER_H
#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#  error "this header requires Py_BUILD_CORE define"
#endif

#include "pycore_uops.h"          // _PyUOpInstruction

int _Py_uop_analyze_and_optimize(PyCodeObject *code,
    _PyUOpInstruction *trace, int trace_len, int curr_stackentries);


#ifdef __cplusplus
}
#endif
#endif /* !Py_INTERNAL_OPTIMIZER_H */
