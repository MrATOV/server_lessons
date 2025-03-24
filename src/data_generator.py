import ctypes
import os

lib = ctypes.CDLL(os.path.abspath("./.lib/libDataGenerator.so"))

lib.GenerateArrayFileInt.argtypes = [ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
lib.GenerateMatrixFileInt.argtypes = [ctypes.c_size_t, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]

lib.GenerateArrayFileUInt.argtypes = [ctypes.c_size_t, ctypes.c_uint, ctypes.c_uint, ctypes.c_char_p]
lib.GenerateMatrixFileUInt.argtypes = [ctypes.c_size_t, ctypes.c_size_t, ctypes.c_uint, ctypes.c_uint, ctypes.c_char_p]

lib.GenerateArrayFileDouble.argtypes = [ctypes.c_size_t, ctypes.c_double, ctypes.c_double, ctypes.c_char_p]
lib.GenerateMatrixFileDouble.argtypes = [ctypes.c_size_t, ctypes.c_size_t, ctypes.c_double, ctypes.c_double, ctypes.c_char_p]

lib.GenerateArrayFileFloat.argtypes = [ctypes.c_size_t, ctypes.c_float, ctypes.c_float, ctypes.c_char_p]
lib.GenerateMatrixFileFloat.argtypes = [ctypes.c_size_t, ctypes.c_size_t, ctypes.c_float, ctypes.c_float, ctypes.c_char_p]

lib.GenerateArrayFileLong.argtypes = [ctypes.c_size_t, ctypes.c_long, ctypes.c_long, ctypes.c_char_p]
lib.GenerateMatrixFileLong.argtypes = [ctypes.c_size_t, ctypes.c_size_t, ctypes.c_long, ctypes.c_long, ctypes.c_char_p]

lib.GenerateArrayFileULong.argtypes = [ctypes.c_size_t, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p]
lib.GenerateMatrixFileULong.argtypes = [ctypes.c_size_t, ctypes.c_size_t, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p]

lib.GenerateTextFile.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

lib.GenerateArrayFileInt(10, 0, 100, b"output_int_array.array")
lib.GenerateArrayFileUInt(10, 0, 100, b"output_uint_array.array")
lib.GenerateArrayFileDouble(10, 0.0, 100.0, b"output_double_array.array")
lib.GenerateArrayFileFloat(10, 0.0, 100.0, b"output_float_array.array")
lib.GenerateArrayFileLong(10, 0, 100, b"output_long_array.array")
lib.GenerateArrayFileULong(10, 0, 100, b"output_ulong_array.array")

lib.GenerateMatrixFileInt(5, 5, 0, 100, b"output_int_matrix.matrix")
lib.GenerateMatrixFileUInt(5, 5, 0, 100, b"output_uint_matrix.matrix")
lib.GenerateMatrixFileDouble(5, 5, 0.0, 100.0, b"output_double_matrix.matrix")
lib.GenerateMatrixFileFloat(5, 5, 0.0, 100.0, b"output_float_matrix.matrix")
lib.GenerateMatrixFileLong(5, 5, 0, 100, b"output_long_matrix.matrix")
lib.GenerateMatrixFileULong(5, 5, 0, 100, b"output_ulong_matrix.matrix")

lib.GenerateTextFile(b"Hello, World!", b"output_ulong_matrix.txt")