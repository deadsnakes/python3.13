#ifndef Py_INTERNAL_PYTHREAD_H
#define Py_INTERNAL_PYTHREAD_H
#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#  error "this header requires Py_BUILD_CORE define"
#endif

// Get _POSIX_THREADS and _POSIX_SEMAPHORES macros if available
#if (defined(HAVE_UNISTD_H) && !defined(_POSIX_THREADS) \
                            && !defined(_POSIX_SEMAPHORES))
#  include <unistd.h>             // _POSIX_THREADS, _POSIX_SEMAPHORES
#endif
#if (defined(HAVE_PTHREAD_H) && !defined(_POSIX_THREADS) \
                             && !defined(_POSIX_SEMAPHORES))
   // This means pthreads are not implemented in libc headers, hence the macro
   // not present in <unistd.h>. But they still can be implemented as an
   // external library (e.g. gnu pth in pthread emulation)
#  include <pthread.h>            // _POSIX_THREADS, _POSIX_SEMAPHORES
#endif
#if !defined(_POSIX_THREADS) && defined(__hpux) && defined(_SC_THREADS)
   // Check if we're running on HP-UX and _SC_THREADS is defined. If so, then
   // enough of the POSIX threads package is implemented to support Python
   // threads.
   //
   // This is valid for HP-UX 11.23 running on an ia64 system. If needed, add
   // a check of __ia64 to verify that we're running on an ia64 system instead
   // of a pa-risc system.
#  define _POSIX_THREADS
#endif


#if defined(_POSIX_THREADS) || defined(HAVE_PTHREAD_STUBS)
#  define _USE_PTHREADS
#endif

#if defined(_USE_PTHREADS) && defined(HAVE_PTHREAD_CONDATTR_SETCLOCK) && defined(HAVE_CLOCK_GETTIME) && defined(CLOCK_MONOTONIC)
// monotonic is supported statically.  It doesn't mean it works on runtime.
#  define CONDATTR_MONOTONIC
#endif


#if defined(HAVE_PTHREAD_STUBS)
#include <stdbool.h>              // bool

// pthread_key
struct py_stub_tls_entry {
    bool in_use;
    void *value;
};
#endif

struct _pythread_runtime_state {
    int initialized;

#ifdef _USE_PTHREADS
    // This matches when thread_pthread.h is used.
    struct {
        /* NULL when pthread_condattr_setclock(CLOCK_MONOTONIC) is not supported. */
        pthread_condattr_t *ptr;
# ifdef CONDATTR_MONOTONIC
    /* The value to which condattr_monotonic is set. */
        pthread_condattr_t val;
# endif
    } _condattr_monotonic;

#endif  // USE_PTHREADS

#if defined(HAVE_PTHREAD_STUBS)
    struct {
        struct py_stub_tls_entry tls_entries[PTHREAD_KEYS_MAX];
    } stubs;
#endif
};


#ifdef HAVE_FORK
/* Private function to reinitialize a lock at fork in the child process.
   Reset the lock to the unlocked state.
   Return 0 on success, return -1 on error. */
extern int _PyThread_at_fork_reinit(PyThread_type_lock *lock);
#endif  /* HAVE_FORK */


#ifdef __cplusplus
}
#endif
#endif /* !Py_INTERNAL_PYTHREAD_H */
