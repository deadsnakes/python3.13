import _ctypes_test
import ctypes
import unittest
from ctypes import (CDLL, Structure, CFUNCTYPE, sizeof, _CFuncPtr,
                    c_void_p, c_char_p, c_char, c_int, c_uint, c_long)


try:
    WINFUNCTYPE = ctypes.WINFUNCTYPE
except AttributeError:
    # fake to enable this test on Linux
    WINFUNCTYPE = CFUNCTYPE

lib = CDLL(_ctypes_test.__file__)


class CFuncPtrTestCase(unittest.TestCase):
    def test_basic(self):
        X = WINFUNCTYPE(c_int, c_int, c_int)

        def func(*args):
            return len(args)

        x = X(func)
        self.assertEqual(x.restype, c_int)
        self.assertEqual(x.argtypes, (c_int, c_int))
        self.assertEqual(sizeof(x), sizeof(c_void_p))
        self.assertEqual(sizeof(X), sizeof(c_void_p))

    def test_first(self):
        StdCallback = WINFUNCTYPE(c_int, c_int, c_int)
        CdeclCallback = CFUNCTYPE(c_int, c_int, c_int)

        def func(a, b):
            return a + b

        s = StdCallback(func)
        c = CdeclCallback(func)

        self.assertEqual(s(1, 2), 3)
        self.assertEqual(c(1, 2), 3)
        # The following no longer raises a TypeError - it is now
        # possible, as in C, to call cdecl functions with more parameters.
        #self.assertRaises(TypeError, c, 1, 2, 3)
        self.assertEqual(c(1, 2, 3, 4, 5, 6), 3)
        if WINFUNCTYPE is not CFUNCTYPE:
            self.assertRaises(TypeError, s, 1, 2, 3)

    def test_structures(self):
        WNDPROC = WINFUNCTYPE(c_long, c_int, c_int, c_int, c_int)

        def wndproc(hwnd, msg, wParam, lParam):
            return hwnd + msg + wParam + lParam

        HINSTANCE = c_int
        HICON = c_int
        HCURSOR = c_int
        LPCTSTR = c_char_p

        class WNDCLASS(Structure):
            _fields_ = [("style", c_uint),
                        ("lpfnWndProc", WNDPROC),
                        ("cbClsExtra", c_int),
                        ("cbWndExtra", c_int),
                        ("hInstance", HINSTANCE),
                        ("hIcon", HICON),
                        ("hCursor", HCURSOR),
                        ("lpszMenuName", LPCTSTR),
                        ("lpszClassName", LPCTSTR)]

        wndclass = WNDCLASS()
        wndclass.lpfnWndProc = WNDPROC(wndproc)

        WNDPROC_2 = WINFUNCTYPE(c_long, c_int, c_int, c_int, c_int)

        self.assertIs(WNDPROC, WNDPROC_2)
        self.assertEqual(wndclass.lpfnWndProc(1, 2, 3, 4), 10)

        f = wndclass.lpfnWndProc

        del wndclass
        del wndproc

        self.assertEqual(f(10, 11, 12, 13), 46)

    def test_dllfunctions(self):
        strchr = lib.my_strchr
        strchr.restype = c_char_p
        strchr.argtypes = (c_char_p, c_char)
        self.assertEqual(strchr(b"abcdefghi", b"b"), b"bcdefghi")
        self.assertEqual(strchr(b"abcdefghi", b"x"), None)

        strtok = lib.my_strtok
        strtok.restype = c_char_p

        def c_string(init):
            size = len(init) + 1
            return (c_char*size)(*init)

        s = b"a\nb\nc"
        b = c_string(s)

        self.assertEqual(strtok(b, b"\n"), b"a")
        self.assertEqual(strtok(None, b"\n"), b"b")
        self.assertEqual(strtok(None, b"\n"), b"c")
        self.assertEqual(strtok(None, b"\n"), None)

    def test_abstract(self):
        self.assertRaises(TypeError, _CFuncPtr, 13, "name", 42, "iid")


if __name__ == '__main__':
    unittest.main()
