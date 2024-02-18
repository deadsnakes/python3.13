#ifndef Py_INTERNAL_OPTIMIZER_H
#define Py_INTERNAL_OPTIMIZER_H
#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#  error "this header requires Py_BUILD_CORE define"
#endif

#include "pycore_uop_ids.h"

// This is the length of the trace we project initially.
#define UOP_MAX_TRACE_LENGTH 512

#define TRACE_STACK_SIZE 5

int _Py_uop_analyze_and_optimize(_PyInterpreterFrame *frame,
    _PyUOpInstruction *trace, int trace_len, int curr_stackentries,
    _PyBloomFilter *dependencies);

extern PyTypeObject _PyCounterExecutor_Type;
extern PyTypeObject _PyCounterOptimizer_Type;
extern PyTypeObject _PyDefaultOptimizer_Type;
extern PyTypeObject _PyUOpExecutor_Type;
extern PyTypeObject _PyUOpOptimizer_Type;

#ifdef __cplusplus
}
#endif
#endif /* !Py_INTERNAL_OPTIMIZER_H */
