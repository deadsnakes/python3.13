// This header file provides wrappers around the atomic operations found in
// `pyatomic.h` that are only atomic in free-threaded builds.
//
// These are intended to be used in places where atomics are required in
// free-threaded builds, but not in the default build, and we don't want to
// introduce the potential performance overhead of an atomic operation in the
// default build.
//
// All usages of these macros should be replaced with unconditionally atomic or
// non-atomic versions, and this file should be removed, once the dust settles
// on free threading.
#ifndef Py_ATOMIC_FT_WRAPPERS_H
#define Py_ATOMIC_FT_WRAPPERS_H
#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#error "this header requires Py_BUILD_CORE define"
#endif

#ifdef Py_GIL_DISABLED
#define FT_ATOMIC_LOAD_SSIZE(value) _Py_atomic_load_ssize(&value)
#define FT_ATOMIC_LOAD_SSIZE_RELAXED(value) \
    _Py_atomic_load_ssize_relaxed(&value)
#define FT_ATOMIC_STORE_SSIZE_RELAXED(value, new_value) \
    _Py_atomic_store_ssize_relaxed(&value, new_value)
#else
#define FT_ATOMIC_LOAD_SSIZE(value) value
#define FT_ATOMIC_LOAD_SSIZE_RELAXED(value) value
#define FT_ATOMIC_STORE_SSIZE_RELAXED(value, new_value) value = new_value
#endif

#ifdef __cplusplus
}
#endif
#endif /* !Py_ATOMIC_FT_WRAPPERS_H */
