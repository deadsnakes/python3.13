import unittest
import sys
import test.support as support

from test.support import import_helper

# Skip this test if the _testcapi module isn't available.
_testcapi = import_helper.import_module('_testcapi')

NULL = None

class IntSubclass(int):
    pass

class Index:
    def __init__(self, value):
        self.value = value

    def __index__(self):
        return self.value

# use __index__(), not __int__()
class MyIndexAndInt:
    def __index__(self):
        return 10
    def __int__(self):
        return 22


class LongTests(unittest.TestCase):

    def test_compact(self):
        for n in {
            # Edge cases
            *(2**n for n in range(66)),
            *(-2**n for n in range(66)),
            *(2**n - 1 for n in range(66)),
            *(-2**n + 1 for n in range(66)),
            # Essentially random
            *(37**n for n in range(14)),
            *(-37**n for n in range(14)),
        }:
            with self.subTest(n=n):
                is_compact, value = _testcapi.call_long_compact_api(n)
                if is_compact:
                    self.assertEqual(n, value)

    def test_compact_known(self):
        # Sanity-check some implementation details (we don't guarantee
        # that these are/aren't compact)
        self.assertEqual(_testcapi.call_long_compact_api(-1), (True, -1))
        self.assertEqual(_testcapi.call_long_compact_api(0), (True, 0))
        self.assertEqual(_testcapi.call_long_compact_api(256), (True, 256))
        self.assertEqual(_testcapi.call_long_compact_api(sys.maxsize),
                         (False, -1))

    def test_long_check(self):
        # Test PyLong_Check()
        check = _testcapi.pylong_check
        self.assertTrue(check(1))
        self.assertTrue(check(123456789012345678901234567890))
        self.assertTrue(check(-1))
        self.assertTrue(check(True))
        self.assertTrue(check(IntSubclass(1)))
        self.assertFalse(check(1.0))
        self.assertFalse(check(object()))
        # CRASHES check(NULL)

    def test_long_checkexact(self):
        # Test PyLong_CheckExact()
        check = _testcapi.pylong_checkexact
        self.assertTrue(check(1))
        self.assertTrue(check(123456789012345678901234567890))
        self.assertTrue(check(-1))
        self.assertFalse(check(True))
        self.assertFalse(check(IntSubclass(1)))
        self.assertFalse(check(1.0))
        self.assertFalse(check(object()))
        # CRASHES check(NULL)

    def test_long_fromdouble(self):
        # Test PyLong_FromDouble()
        fromdouble = _testcapi.pylong_fromdouble
        float_max = sys.float_info.max
        for value in (5.0, 5.1, 5.9, -5.1, -5.9, 0.0, -0.0, float_max, -float_max):
            with self.subTest(value=value):
                self.assertEqual(fromdouble(value), int(value))
        self.assertRaises(OverflowError, fromdouble, float('inf'))
        self.assertRaises(OverflowError, fromdouble, float('-inf'))
        self.assertRaises(ValueError, fromdouble, float('nan'))

    def test_long_fromvoidptr(self):
        # Test PyLong_FromVoidPtr()
        fromvoidptr = _testcapi.pylong_fromvoidptr
        obj = object()
        x = fromvoidptr(obj)
        y = fromvoidptr(NULL)
        self.assertIsInstance(x, int)
        self.assertGreaterEqual(x, 0)
        self.assertIsInstance(y, int)
        self.assertEqual(y, 0)
        self.assertNotEqual(x, y)

    def test_long_fromstring(self):
        # Test PyLong_FromString()
        fromstring = _testcapi.pylong_fromstring
        self.assertEqual(fromstring(b'123', 10), (123, 3))
        self.assertEqual(fromstring(b'cafe', 16), (0xcafe, 4))
        self.assertEqual(fromstring(b'xyz', 36), (44027, 3))
        self.assertEqual(fromstring(b'123', 0), (123, 3))
        self.assertEqual(fromstring(b'0xcafe', 0), (0xcafe, 6))
        self.assertRaises(ValueError, fromstring, b'cafe', 0)
        self.assertEqual(fromstring(b'-123', 10), (-123, 4))
        self.assertEqual(fromstring(b' -123 ', 10), (-123, 6))
        self.assertEqual(fromstring(b'1_23', 10), (123, 4))
        self.assertRaises(ValueError, fromstring, b'- 123', 10)
        self.assertRaises(ValueError, fromstring, b'', 10)

        self.assertRaises(ValueError, fromstring, b'123', 1)
        self.assertRaises(ValueError, fromstring, b'123', -1)
        self.assertRaises(ValueError, fromstring, b'123', 37)

        self.assertRaises(ValueError, fromstring, '١٢٣٤٥٦٧٨٩٠'.encode(), 0)
        self.assertRaises(ValueError, fromstring, '١٢٣٤٥٦٧٨٩٠'.encode(), 16)

        self.assertEqual(fromstring(b'123\x00', 0), (123, 3))
        self.assertEqual(fromstring(b'123\x00456', 0), (123, 3))
        self.assertEqual(fromstring(b'123\x00', 16), (0x123, 3))
        self.assertEqual(fromstring(b'123\x00456', 16), (0x123, 3))

        # CRASHES fromstring(NULL, 0)
        # CRASHES fromstring(NULL, 16)

    def test_long_fromunicodeobject(self):
        # Test PyLong_FromUnicodeObject()
        fromunicodeobject = _testcapi.pylong_fromunicodeobject
        self.assertEqual(fromunicodeobject('123', 10), 123)
        self.assertEqual(fromunicodeobject('cafe', 16), 0xcafe)
        self.assertEqual(fromunicodeobject('xyz', 36), 44027)
        self.assertEqual(fromunicodeobject('123', 0), 123)
        self.assertEqual(fromunicodeobject('0xcafe', 0), 0xcafe)
        self.assertRaises(ValueError, fromunicodeobject, 'cafe', 0)
        self.assertEqual(fromunicodeobject('-123', 10), -123)
        self.assertEqual(fromunicodeobject(' -123 ', 10), -123)
        self.assertEqual(fromunicodeobject('1_23', 10), 123)
        self.assertRaises(ValueError, fromunicodeobject, '- 123', 10)
        self.assertRaises(ValueError, fromunicodeobject, '', 10)

        self.assertRaises(ValueError, fromunicodeobject, '123', 1)
        self.assertRaises(ValueError, fromunicodeobject, '123', -1)
        self.assertRaises(ValueError, fromunicodeobject, '123', 37)

        self.assertEqual(fromunicodeobject('١٢٣٤٥٦٧٨٩٠', 0), 1234567890)
        self.assertEqual(fromunicodeobject('١٢٣٤٥٦٧٨٩٠', 16), 0x1234567890)

        self.assertRaises(ValueError, fromunicodeobject, '123\x00', 0)
        self.assertRaises(ValueError, fromunicodeobject, '123\x00456', 0)
        self.assertRaises(ValueError, fromunicodeobject, '123\x00', 16)
        self.assertRaises(ValueError, fromunicodeobject, '123\x00456', 16)

        # CRASHES fromunicodeobject(NULL, 0)
        # CRASHES fromunicodeobject(NULL, 16)

    def test_long_asint(self):
        # Test PyLong_AsInt()
        PyLong_AsInt = _testcapi.PyLong_AsInt
        from _testcapi import INT_MIN, INT_MAX

        # round trip (object -> int -> object)
        for value in (INT_MIN, INT_MAX, -1, 0, 1, 123):
            with self.subTest(value=value):
                self.assertEqual(PyLong_AsInt(value), value)
        self.assertEqual(PyLong_AsInt(IntSubclass(42)), 42)
        self.assertEqual(PyLong_AsInt(Index(42)), 42)
        self.assertEqual(PyLong_AsInt(MyIndexAndInt()), 10)

        # bound checking
        self.assertRaises(OverflowError, PyLong_AsInt, INT_MIN - 1)
        self.assertRaises(OverflowError, PyLong_AsInt, INT_MAX + 1)

        # invalid type
        self.assertRaises(TypeError, PyLong_AsInt, 1.0)
        self.assertRaises(TypeError, PyLong_AsInt, b'2')
        self.assertRaises(TypeError, PyLong_AsInt, '3')
        self.assertRaises(SystemError, PyLong_AsInt, NULL)

    def test_long_aslong(self):
        # Test PyLong_AsLong() and PyLong_FromLong()
        aslong = _testcapi.pylong_aslong
        from _testcapi import LONG_MIN, LONG_MAX
        # round trip (object -> long -> object)
        for value in (LONG_MIN, LONG_MAX, -1, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(aslong(value), value)

        self.assertEqual(aslong(IntSubclass(42)), 42)
        self.assertEqual(aslong(Index(42)), 42)
        self.assertEqual(aslong(MyIndexAndInt()), 10)

        self.assertRaises(OverflowError, aslong, LONG_MIN - 1)
        self.assertRaises(OverflowError, aslong, LONG_MAX + 1)
        self.assertRaises(TypeError, aslong, 1.0)
        self.assertRaises(TypeError, aslong, b'2')
        self.assertRaises(TypeError, aslong, '3')
        self.assertRaises(SystemError, aslong, NULL)

    def test_long_aslongandoverflow(self):
        # Test PyLong_AsLongAndOverflow()
        aslongandoverflow = _testcapi.pylong_aslongandoverflow
        from _testcapi import LONG_MIN, LONG_MAX
        # round trip (object -> long -> object)
        for value in (LONG_MIN, LONG_MAX, -1, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(aslongandoverflow(value), (value, 0))

        self.assertEqual(aslongandoverflow(IntSubclass(42)), (42, 0))
        self.assertEqual(aslongandoverflow(Index(42)), (42, 0))
        self.assertEqual(aslongandoverflow(MyIndexAndInt()), (10, 0))

        self.assertEqual(aslongandoverflow(LONG_MIN - 1), (-1, -1))
        self.assertEqual(aslongandoverflow(LONG_MAX + 1), (-1, 1))
        # CRASHES aslongandoverflow(1.0)
        # CRASHES aslongandoverflow(NULL)

    def test_long_asunsignedlong(self):
        # Test PyLong_AsUnsignedLong() and PyLong_FromUnsignedLong()
        asunsignedlong = _testcapi.pylong_asunsignedlong
        from _testcapi import ULONG_MAX
        # round trip (object -> unsigned long -> object)
        for value in (ULONG_MAX, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(asunsignedlong(value), value)

        self.assertEqual(asunsignedlong(IntSubclass(42)), 42)
        self.assertRaises(TypeError, asunsignedlong, Index(42))
        self.assertRaises(TypeError, asunsignedlong, MyIndexAndInt())

        self.assertRaises(OverflowError, asunsignedlong, -1)
        self.assertRaises(OverflowError, asunsignedlong, ULONG_MAX + 1)
        self.assertRaises(TypeError, asunsignedlong, 1.0)
        self.assertRaises(TypeError, asunsignedlong, b'2')
        self.assertRaises(TypeError, asunsignedlong, '3')
        self.assertRaises(SystemError, asunsignedlong, NULL)

    def test_long_asunsignedlongmask(self):
        # Test PyLong_AsUnsignedLongMask()
        asunsignedlongmask = _testcapi.pylong_asunsignedlongmask
        from _testcapi import ULONG_MAX
        # round trip (object -> unsigned long -> object)
        for value in (ULONG_MAX, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(asunsignedlongmask(value), value)

        self.assertEqual(asunsignedlongmask(IntSubclass(42)), 42)
        self.assertEqual(asunsignedlongmask(Index(42)), 42)
        self.assertEqual(asunsignedlongmask(MyIndexAndInt()), 10)

        self.assertEqual(asunsignedlongmask(-1), ULONG_MAX)
        self.assertEqual(asunsignedlongmask(ULONG_MAX + 1), 0)
        self.assertRaises(TypeError, asunsignedlongmask, 1.0)
        self.assertRaises(TypeError, asunsignedlongmask, b'2')
        self.assertRaises(TypeError, asunsignedlongmask, '3')
        self.assertRaises(SystemError, asunsignedlongmask, NULL)

    def test_long_aslonglong(self):
        # Test PyLong_AsLongLong() and PyLong_FromLongLong()
        aslonglong = _testcapi.pylong_aslonglong
        from _testcapi import LLONG_MIN, LLONG_MAX
        # round trip (object -> long long -> object)
        for value in (LLONG_MIN, LLONG_MAX, -1, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(aslonglong(value), value)

        self.assertEqual(aslonglong(IntSubclass(42)), 42)
        self.assertEqual(aslonglong(Index(42)), 42)
        self.assertEqual(aslonglong(MyIndexAndInt()), 10)

        self.assertRaises(OverflowError, aslonglong, LLONG_MIN - 1)
        self.assertRaises(OverflowError, aslonglong, LLONG_MAX + 1)
        self.assertRaises(TypeError, aslonglong, 1.0)
        self.assertRaises(TypeError, aslonglong, b'2')
        self.assertRaises(TypeError, aslonglong, '3')
        self.assertRaises(SystemError, aslonglong, NULL)

    def test_long_aslonglongandoverflow(self):
        # Test PyLong_AsLongLongAndOverflow()
        aslonglongandoverflow = _testcapi.pylong_aslonglongandoverflow
        from _testcapi import LLONG_MIN, LLONG_MAX
        # round trip (object -> long long -> object)
        for value in (LLONG_MIN, LLONG_MAX, -1, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(aslonglongandoverflow(value), (value, 0))

        self.assertEqual(aslonglongandoverflow(IntSubclass(42)), (42, 0))
        self.assertEqual(aslonglongandoverflow(Index(42)), (42, 0))
        self.assertEqual(aslonglongandoverflow(MyIndexAndInt()), (10, 0))

        self.assertEqual(aslonglongandoverflow(LLONG_MIN - 1), (-1, -1))
        self.assertEqual(aslonglongandoverflow(LLONG_MAX + 1), (-1, 1))
        # CRASHES aslonglongandoverflow(1.0)
        # CRASHES aslonglongandoverflow(NULL)

    def test_long_asunsignedlonglong(self):
        # Test PyLong_AsUnsignedLongLong() and PyLong_FromUnsignedLongLong()
        asunsignedlonglong = _testcapi.pylong_asunsignedlonglong
        from _testcapi import ULLONG_MAX
        # round trip (object -> unsigned long long -> object)
        for value in (ULLONG_MAX, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(asunsignedlonglong(value), value)

        self.assertEqual(asunsignedlonglong(IntSubclass(42)), 42)
        self.assertRaises(TypeError, asunsignedlonglong, Index(42))
        self.assertRaises(TypeError, asunsignedlonglong, MyIndexAndInt())

        self.assertRaises(OverflowError, asunsignedlonglong, -1)
        self.assertRaises(OverflowError, asunsignedlonglong, ULLONG_MAX + 1)
        self.assertRaises(TypeError, asunsignedlonglong, 1.0)
        self.assertRaises(TypeError, asunsignedlonglong, b'2')
        self.assertRaises(TypeError, asunsignedlonglong, '3')
        self.assertRaises(SystemError, asunsignedlonglong, NULL)

    def test_long_asunsignedlonglongmask(self):
        # Test PyLong_AsUnsignedLongLongMask()
        asunsignedlonglongmask = _testcapi.pylong_asunsignedlonglongmask
        from _testcapi import ULLONG_MAX
        # round trip (object -> unsigned long long -> object)
        for value in (ULLONG_MAX, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(asunsignedlonglongmask(value), value)

        self.assertEqual(asunsignedlonglongmask(IntSubclass(42)), 42)
        self.assertEqual(asunsignedlonglongmask(Index(42)), 42)
        self.assertEqual(asunsignedlonglongmask(MyIndexAndInt()), 10)

        self.assertEqual(asunsignedlonglongmask(-1), ULLONG_MAX)
        self.assertEqual(asunsignedlonglongmask(ULLONG_MAX + 1), 0)
        self.assertRaises(TypeError, asunsignedlonglongmask, 1.0)
        self.assertRaises(TypeError, asunsignedlonglongmask, b'2')
        self.assertRaises(TypeError, asunsignedlonglongmask, '3')
        self.assertRaises(SystemError, asunsignedlonglongmask, NULL)

    def test_long_as_ssize_t(self):
        # Test PyLong_AsSsize_t() and PyLong_FromSsize_t()
        as_ssize_t = _testcapi.pylong_as_ssize_t
        from _testcapi import PY_SSIZE_T_MIN, PY_SSIZE_T_MAX
        # round trip (object -> Py_ssize_t -> object)
        for value in (PY_SSIZE_T_MIN, PY_SSIZE_T_MAX, -1, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(as_ssize_t(value), value)

        self.assertEqual(as_ssize_t(IntSubclass(42)), 42)
        self.assertRaises(TypeError, as_ssize_t, Index(42))
        self.assertRaises(TypeError, as_ssize_t, MyIndexAndInt())

        self.assertRaises(OverflowError, as_ssize_t, PY_SSIZE_T_MIN - 1)
        self.assertRaises(OverflowError, as_ssize_t, PY_SSIZE_T_MAX + 1)
        self.assertRaises(TypeError, as_ssize_t, 1.0)
        self.assertRaises(TypeError, as_ssize_t, b'2')
        self.assertRaises(TypeError, as_ssize_t, '3')
        self.assertRaises(SystemError, as_ssize_t, NULL)

    def test_long_as_size_t(self):
        # Test PyLong_AsSize_t() and PyLong_FromSize_t()
        as_size_t = _testcapi.pylong_as_size_t
        from _testcapi import SIZE_MAX
        # round trip (object -> size_t -> object)
        for value in (SIZE_MAX, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(as_size_t(value), value)

        self.assertEqual(as_size_t(IntSubclass(42)), 42)
        self.assertRaises(TypeError, as_size_t, Index(42))
        self.assertRaises(TypeError, as_size_t, MyIndexAndInt())

        self.assertRaises(OverflowError, as_size_t, -1)
        self.assertRaises(OverflowError, as_size_t, SIZE_MAX + 1)
        self.assertRaises(TypeError, as_size_t, 1.0)
        self.assertRaises(TypeError, as_size_t, b'2')
        self.assertRaises(TypeError, as_size_t, '3')
        self.assertRaises(SystemError, as_size_t, NULL)

    def test_long_asdouble(self):
        # Test PyLong_AsDouble()
        asdouble = _testcapi.pylong_asdouble
        MAX = int(sys.float_info.max)
        for value in (-MAX, MAX, -1, 0, 1, 1234):
            with self.subTest(value=value):
                self.assertEqual(asdouble(value), float(value))
                self.assertIsInstance(asdouble(value), float)

        self.assertEqual(asdouble(IntSubclass(42)), 42.0)
        self.assertRaises(TypeError, asdouble, Index(42))
        self.assertRaises(TypeError, asdouble, MyIndexAndInt())

        self.assertRaises(OverflowError, asdouble, 2 * MAX)
        self.assertRaises(OverflowError, asdouble, -2 * MAX)
        self.assertRaises(TypeError, asdouble, 1.0)
        self.assertRaises(TypeError, asdouble, b'2')
        self.assertRaises(TypeError, asdouble, '3')
        self.assertRaises(SystemError, asdouble, NULL)

    def test_long_asvoidptr(self):
        # Test PyLong_AsVoidPtr()
        fromvoidptr = _testcapi.pylong_fromvoidptr
        asvoidptr = _testcapi.pylong_asvoidptr
        obj = object()
        x = fromvoidptr(obj)
        y = fromvoidptr(NULL)
        self.assertIs(asvoidptr(x), obj)
        self.assertIs(asvoidptr(y), NULL)
        self.assertIs(asvoidptr(IntSubclass(x)), obj)

        # negative values
        M = (1 << _testcapi.SIZEOF_VOID_P * 8)
        if x >= M//2:
            self.assertIs(asvoidptr(x - M), obj)
        if y >= M//2:
            self.assertIs(asvoidptr(y - M), NULL)

        self.assertRaises(TypeError, asvoidptr, Index(x))
        self.assertRaises(TypeError, asvoidptr, object())
        self.assertRaises(OverflowError, asvoidptr, 2**1000)
        self.assertRaises(OverflowError, asvoidptr, -2**1000)
        # CRASHES asvoidptr(NULL)

    def test_long_asnativebytes(self):
        import math
        from _testcapi import (
            pylong_asnativebytes as asnativebytes,
            SIZE_MAX,
        )

        # Abbreviate sizeof(Py_ssize_t) to SZ because we use it a lot
        SZ = int(math.ceil(math.log(SIZE_MAX + 1) / math.log(2)) / 8)
        MAX_SSIZE = 2 ** (SZ * 8 - 1) - 1
        MAX_USIZE = 2 ** (SZ * 8) - 1
        if support.verbose:
            print(f"SIZEOF_SIZE={SZ}\n{MAX_SSIZE=:016X}\n{MAX_USIZE=:016X}")

        # These tests check that the requested buffer size is correct
        for v, expect in [
            (0, SZ),
            (512, SZ),
            (-512, SZ),
            (MAX_SSIZE, SZ),
            (MAX_USIZE, SZ + 1),
            (-MAX_SSIZE, SZ),
            (-MAX_USIZE, SZ + 1),
            (2**255-1, 32),
            (-(2**255-1), 32),
            (2**256-1, 33),
            (-(2**256-1), 33),
        ]:
            with self.subTest(f"sizeof-{v:X}"):
                buffer = bytearray(1)
                self.assertEqual(expect, asnativebytes(v, buffer, 0, -1),
                    "PyLong_AsNativeBytes(v, NULL, 0, -1)")
                # Also check via the __index__ path
                self.assertEqual(expect, asnativebytes(Index(v), buffer, 0, -1),
                    "PyLong_AsNativeBytes(Index(v), NULL, 0, -1)")

        # We request as many bytes as `expect_be` contains, and always check
        # the result (both big and little endian). We check the return value
        # independently, since the buffer should always be filled correctly even
        # if we need more bytes
        for v, expect_be, expect_n in [
            (0,         b'\x00',                1),
            (0,         b'\x00' * 2,            2),
            (0,         b'\x00' * 8,            min(8, SZ)),
            (1,         b'\x01',                1),
            (1,         b'\x00' * 10 + b'\x01', min(11, SZ)),
            (42,        b'\x2a',                1),
            (42,        b'\x00' * 10 + b'\x2a', min(11, SZ)),
            (-1,        b'\xff',                1),
            (-1,        b'\xff' * 10,           min(11, SZ)),
            (-42,       b'\xd6',                1),
            (-42,       b'\xff' * 10 + b'\xd6', min(11, SZ)),
            # Extracts 255 into a single byte, but requests sizeof(Py_ssize_t)
            (255,       b'\xff',                SZ),
            (255,       b'\x00\xff',            2),
            (256,       b'\x01\x00',            2),
            # Extracts successfully (unsigned), but requests 9 bytes
            (2**63,     b'\x80' + b'\x00' * 7,  9),
            # "Extracts", but requests 9 bytes
            (-2**63,    b'\x80' + b'\x00' * 7,  9),
            (2**63,     b'\x00\x80' + b'\x00' * 7, 9),
            (-2**63,    b'\xff\x80' + b'\x00' * 7, 9),

            (2**255-1,      b'\x7f' + b'\xff' * 31,                 32),
            (-(2**255-1),   b'\x80' + b'\x00' * 30 + b'\x01',       32),
            # Request extra bytes, but result says we only needed 32
            (-(2**255-1),   b'\xff\x80' + b'\x00' * 30 + b'\x01',   32),
            (-(2**255-1),   b'\xff\xff\x80' + b'\x00' * 30 + b'\x01', 32),

            # Extracting 256 bits of integer will request 33 bytes, but still
            # copy as many bits as possible into the buffer. So we *can* copy
            # into a 32-byte buffer, though negative number may be unrecoverable
            (2**256-1,      b'\xff' * 32,                           33),
            (2**256-1,      b'\x00' + b'\xff' * 32,                 33),
            (-(2**256-1),   b'\x00' * 31 + b'\x01',                 33),
            (-(2**256-1),   b'\xff' + b'\x00' * 31 + b'\x01',       33),
            (-(2**256-1),   b'\xff\xff' + b'\x00' * 31 + b'\x01',   33),

            # The classic "Windows HRESULT as negative number" case
            #   HRESULT hr;
            #   PyLong_CopyBits(<-2147467259>, &hr, sizeof(HRESULT))
            #   assert(hr == E_FAIL)
            (-2147467259, b'\x80\x00\x40\x05', 4),
        ]:
            with self.subTest(f"{v:X}-{len(expect_be)}bytes"):
                n = len(expect_be)
                buffer = bytearray(n)
                expect_le = expect_be[::-1]

                self.assertEqual(expect_n, asnativebytes(v, buffer, n, 0),
                    f"PyLong_AsNativeBytes(v, buffer, {n}, <big>)")
                self.assertEqual(expect_be, buffer[:n], "<big>")
                self.assertEqual(expect_n, asnativebytes(v, buffer, n, 1),
                    f"PyLong_AsNativeBytes(v, buffer, {n}, <little>)")
                self.assertEqual(expect_le, buffer[:n], "<little>")

        # Check a few error conditions. These are validated in code, but are
        # unspecified in docs, so if we make changes to the implementation, it's
        # fine to just update these tests rather than preserve the behaviour.
        with self.assertRaises(SystemError):
            asnativebytes(1, buffer, 0, 2)
        with self.assertRaises(TypeError):
            asnativebytes('not a number', buffer, 0, -1)

    def test_long_fromnativebytes(self):
        import math
        from _testcapi import (
            pylong_fromnativebytes as fromnativebytes,
            SIZE_MAX,
        )

        # Abbreviate sizeof(Py_ssize_t) to SZ because we use it a lot
        SZ = int(math.ceil(math.log(SIZE_MAX + 1) / math.log(2)) / 8)
        MAX_SSIZE = 2 ** (SZ * 8 - 1) - 1
        MAX_USIZE = 2 ** (SZ * 8) - 1

        for v_be, expect_s, expect_u in [
            (b'\x00', 0, 0),
            (b'\x01', 1, 1),
            (b'\xff', -1, 255),
            (b'\x00\xff', 255, 255),
            (b'\xff\xff', -1, 65535),
        ]:
            with self.subTest(f"{expect_s}-{expect_u:X}-{len(v_be)}bytes"):
                n = len(v_be)
                v_le = v_be[::-1]

                self.assertEqual(expect_s, fromnativebytes(v_be, n, 0, 1),
                    f"PyLong_FromNativeBytes(buffer, {n}, <big>)")
                self.assertEqual(expect_s, fromnativebytes(v_le, n, 1, 1),
                    f"PyLong_FromNativeBytes(buffer, {n}, <little>)")
                self.assertEqual(expect_u, fromnativebytes(v_be, n, 0, 0),
                    f"PyLong_FromUnsignedNativeBytes(buffer, {n}, <big>)")
                self.assertEqual(expect_u, fromnativebytes(v_le, n, 1, 0),
                    f"PyLong_FromUnsignedNativeBytes(buffer, {n}, <little>)")

                # Check native endian when the result would be the same either
                # way and we can test it.
                if v_be == v_le:
                    self.assertEqual(expect_s, fromnativebytes(v_be, n, -1, 1),
                        f"PyLong_FromNativeBytes(buffer, {n}, <native>)")
                    self.assertEqual(expect_u, fromnativebytes(v_be, n, -1, 0),
                        f"PyLong_FromUnsignedNativeBytes(buffer, {n}, <native>)")


if __name__ == "__main__":
    unittest.main()
