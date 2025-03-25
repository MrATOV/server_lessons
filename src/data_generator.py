import os
import ctypes
from ctypes import *
from enum import IntEnum

class DataType(IntEnum):
    CHAR = 0
    UCHAR = 1
    SHORT = 2
    USHORT = 3
    INT = 4
    UINT = 5
    LONG = 6
    ULONG = 7
    FLOAT = 8
    DOUBLE = 9

class FillType(IntEnum):
    ASCENDING = 0
    DESCENDING = 1
    RANDOM = 2

lib_dir = 'lib'
lib_filename = 'libDataGenerator.so'
path = os.path.join(os.getcwd(), lib_dir, lib_filename)

lib = ctypes.CDLL(path)

def generate_random_array(size, data_type, min_val, max_val, file_path):
    file_path_bytes = f'{file_path}.array'.encode('utf-8')
    
    if data_type == DataType.CHAR:
        lib.GenerateArrayFileChar(size, c_char(min_val), c_char(max_val), file_path_bytes)
    elif data_type == DataType.UCHAR:
        lib.GenerateArrayFileUChar(size, c_ubyte(min_val), c_ubyte(max_val), file_path_bytes)
    elif data_type == DataType.SHORT:
        lib.GenerateArrayFileShort(size, c_short(min_val), c_short(max_val), file_path_bytes)
    elif data_type == DataType.USHORT:
        lib.GenerateArrayFileUShort(size, c_ushort(min_val), c_ushort(max_val), file_path_bytes)
    elif data_type == DataType.INT:
        lib.GenerateArrayFileInt(size, c_int(min_val), c_int(max_val), file_path_bytes)
    elif data_type == DataType.UINT:
        lib.GenerateArrayFileUInt(size, c_uint(min_val), c_uint(max_val), file_path_bytes)
    elif data_type == DataType.LONG:
        lib.GenerateArrayFileLong(size, c_long(min_val), c_long(max_val), file_path_bytes)
    elif data_type == DataType.ULONG:
        lib.GenerateArrayFileULong(size, c_ulong(min_val), c_ulong(max_val), file_path_bytes)
    elif data_type == DataType.FLOAT:
        lib.GenerateArrayFileFloat(size, c_float(min_val), c_float(max_val), file_path_bytes)
    elif data_type == DataType.DOUBLE:
        lib.GenerateArrayFileDouble(size, c_double(min_val), c_double(max_val), file_path_bytes)
    else:
        raise ValueError("Unsupported data type")
    return file_path_bytes.decode('utf-8')

def generate_ordered_array(size, data_type, fill_type, start, step, interval, file_path):
    file_path_bytes = f'{file_path}.array'.encode('utf-8')
    
    if data_type == DataType.CHAR:
        lib.GenerateOrderArrayFileChar(size, fill_type, c_char(start), c_char(step), interval, file_path_bytes)
    elif data_type == DataType.UCHAR:
        lib.GenerateOrderArrayFileUChar(size, fill_type, c_ubyte(start), c_ubyte(step), interval, file_path_bytes)
    elif data_type == DataType.SHORT:
        lib.GenerateOrderArrayFileShort(size, fill_type, c_short(start), c_short(step), interval, file_path_bytes)
    elif data_type == DataType.USHORT:
        lib.GenerateOrderArrayFileUShort(size, fill_type, c_ushort(start), c_ushort(step), interval, file_path_bytes)
    elif data_type == DataType.INT:
        lib.GenerateOrderArrayFileInt(size, fill_type, c_int(start), c_int(step), interval, file_path_bytes)
    elif data_type == DataType.UINT:
        lib.GenerateOrderArrayFileUInt(size, fill_type, c_uint(start), c_uint(step), interval, file_path_bytes)
    elif data_type == DataType.LONG:
        lib.GenerateOrderArrayFileLong(size, fill_type, c_long(start), c_long(step), interval, file_path_bytes)
    elif data_type == DataType.ULONG:
        lib.GenerateOrderArrayFileULong(size, fill_type, c_ulong(start), c_ulong(step), interval, file_path_bytes)
    elif data_type == DataType.FLOAT:
        lib.GenerateOrderArrayFileFloat(size, fill_type, c_float(start), c_float(step), interval, file_path_bytes)
    elif data_type == DataType.DOUBLE:
        lib.GenerateOrderArrayFileDouble(size, fill_type, c_double(start), c_double(step), interval, file_path_bytes)
    else:
        raise ValueError("Unsupported data type")
    return file_path_bytes.decode('utf-8')

def generate_random_matrix(rows, cols, data_type, min_val, max_val, file_path):
    file_path_bytes = f'{file_path}.matrix'.encode('utf-8')
    
    if data_type == DataType.CHAR:
        lib.GenerateMatrixFileChar(rows, cols, c_char(min_val), c_char(max_val), file_path_bytes)
    elif data_type == DataType.UCHAR:
        lib.GenerateMatrixFileUChar(rows, cols, c_ubyte(min_val), c_ubyte(max_val), file_path_bytes)
    elif data_type == DataType.SHORT:
        lib.GenerateMatrixFileShort(rows, cols, c_short(min_val), c_short(max_val), file_path_bytes)
    elif data_type == DataType.USHORT:
        lib.GenerateMatrixFileUShort(rows, cols, c_ushort(min_val), c_ushort(max_val), file_path_bytes)
    elif data_type == DataType.INT:
        lib.GenerateMatrixFileInt(rows, cols, c_int(min_val), c_int(max_val), file_path_bytes)
    elif data_type == DataType.UINT:
        lib.GenerateMatrixFileUInt(rows, cols, c_uint(min_val), c_uint(max_val), file_path_bytes)
    elif data_type == DataType.LONG:
        lib.GenerateMatrixFileLong(rows, cols, c_long(min_val), c_long(max_val), file_path_bytes)
    elif data_type == DataType.ULONG:
        lib.GenerateMatrixFileULong(rows, cols, c_ulong(min_val), c_ulong(max_val), file_path_bytes)
    elif data_type == DataType.FLOAT:
        lib.GenerateMatrixFileFloat(rows, cols, c_float(min_val), c_float(max_val), file_path_bytes)
    elif data_type == DataType.DOUBLE:
        lib.GenerateMatrixFileDouble(rows, cols, c_double(min_val), c_double(max_val), file_path_bytes)
    else:
        raise ValueError("Unsupported data type")
    return file_path_bytes.decode('utf-8')

def generate_ordered_matrix(rows, cols, data_type, fill_type, start, step, interval, file_path):
    file_path_bytes = f'{file_path}.matrix'.encode('utf-8')
    
    if data_type == DataType.CHAR:
        lib.GenerateOrderMatrixFileChar(rows, cols, fill_type, c_char(start), c_char(step), interval, file_path_bytes)
    elif data_type == DataType.UCHAR:
        lib.GenerateOrderMatrixFileUChar(rows, cols, fill_type, c_ubyte(start), c_ubyte(step), interval, file_path_bytes)
    elif data_type == DataType.SHORT:
        lib.GenerateOrderMatrixFileShort(rows, cols, fill_type, c_short(start), c_short(step), interval, file_path_bytes)
    elif data_type == DataType.USHORT:
        lib.GenerateOrderMatrixFileUShort(rows, cols, fill_type, c_ushort(start), c_ushort(step), interval, file_path_bytes)
    elif data_type == DataType.INT:
        lib.GenerateOrderMatrixFileInt(rows, cols, fill_type, c_int(start), c_int(step), interval, file_path_bytes)
    elif data_type == DataType.UINT:
        lib.GenerateOrderMatrixFileUInt(rows, cols, fill_type, c_uint(start), c_uint(step), interval, file_path_bytes)
    elif data_type == DataType.LONG:
        lib.GenerateOrderMatrixFileLong(rows, cols, fill_type, c_long(start), c_long(step), interval, file_path_bytes)
    elif data_type == DataType.ULONG:
        lib.GenerateOrderMatrixFileULong(rows, cols, fill_type, c_ulong(start), c_ulong(step), interval, file_path_bytes)
    elif data_type == DataType.FLOAT:
        lib.GenerateOrderMatrixFileFloat(rows, cols, fill_type, c_float(start), c_float(step), interval, file_path_bytes)
    elif data_type == DataType.DOUBLE:
        lib.GenerateOrderMatrixFileDouble(rows, cols, fill_type, c_double(start), c_double(step), interval, file_path_bytes)
    else:
        raise ValueError("Unsupported data type")
    return file_path_bytes.decode('utf-8')

def generate_text_file(data, file_path):
    file_path_bytes = f'{file_path}.txt'.encode('utf-8')
    data_bytes = data.encode('utf-8')
    lib.GenerateTextFile(data_bytes, file_path_bytes)
    return file_path_bytes.decode('utf-8')