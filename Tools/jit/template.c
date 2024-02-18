#include "Python.h"

#include "pycore_call.h"
#include "pycore_ceval.h"
#include "pycore_dict.h"
#include "pycore_emscripten_signal.h"
#include "pycore_intrinsics.h"
#include "pycore_jit.h"
#include "pycore_long.h"
#include "pycore_opcode_metadata.h"
#include "pycore_opcode_utils.h"
#include "pycore_range.h"
#include "pycore_setobject.h"
#include "pycore_sliceobject.h"

#include "ceval_macros.h"

#undef CURRENT_OPARG
#define CURRENT_OPARG() (_oparg)

#undef CURRENT_OPERAND
#define CURRENT_OPERAND() (_operand)

#undef DEOPT_IF
#define DEOPT_IF(COND, INSTNAME) \
    do {                         \
        if ((COND)) {            \
            goto deoptimize;     \
        }                        \
    } while (0)

#undef ENABLE_SPECIALIZATION
#define ENABLE_SPECIALIZATION (0)

#undef GOTO_ERROR
#define GOTO_ERROR(LABEL)        \
    do {                         \
        goto LABEL ## _tier_two; \
    } while (0)

#undef LOAD_IP
#define LOAD_IP(UNUSED) \
    do {                \
    } while (0)

#define PATCH_VALUE(TYPE, NAME, ALIAS)  \
    extern void ALIAS;                  \
    TYPE NAME = (TYPE)(uint64_t)&ALIAS;

#define PATCH_JUMP(ALIAS)                                    \
    extern void ALIAS;                                       \
    __attribute__((musttail))                                \
    return ((jit_func)&ALIAS)(frame, stack_pointer, tstate);

_Py_CODEUNIT *
_JIT_ENTRY(_PyInterpreterFrame *frame, PyObject **stack_pointer, PyThreadState *tstate)
{
    // Locals that the instruction implementations expect to exist:
    PATCH_VALUE(_PyExecutorObject *, current_executor, _JIT_EXECUTOR)
    int oparg;
    int opcode = _JIT_OPCODE;
    _PyUOpInstruction *next_uop;
    // Other stuff we need handy:
    PATCH_VALUE(uint16_t, _oparg, _JIT_OPARG)
    PATCH_VALUE(uint64_t, _operand, _JIT_OPERAND)
    PATCH_VALUE(uint32_t, _target, _JIT_TARGET)
    // The actual instruction definitions (only one will be used):
    if (opcode == _JUMP_TO_TOP) {
        CHECK_EVAL_BREAKER();
        PATCH_JUMP(_JIT_TOP);
    }
    switch (opcode) {
#include "executor_cases.c.h"
        default:
            Py_UNREACHABLE();
    }
    PATCH_JUMP(_JIT_CONTINUE);
    // Labels that the instruction implementations expect to exist:
unbound_local_error_tier_two:
    _PyEval_FormatExcCheckArg(
        tstate, PyExc_UnboundLocalError, UNBOUNDLOCAL_ERROR_MSG,
        PyTuple_GetItem(_PyFrame_GetCode(frame)->co_localsplusnames, oparg));
    goto error_tier_two;
pop_4_error_tier_two:
    STACK_SHRINK(1);
pop_3_error_tier_two:
    STACK_SHRINK(1);
pop_2_error_tier_two:
    STACK_SHRINK(1);
pop_1_error_tier_two:
    STACK_SHRINK(1);
error_tier_two:
    _PyFrame_SetStackPointer(frame, stack_pointer);
    return NULL;
deoptimize:
    _PyFrame_SetStackPointer(frame, stack_pointer);
    return _PyCode_CODE(_PyFrame_GetCode(frame)) + _target;
}
