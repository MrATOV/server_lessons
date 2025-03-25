from fastapi import HTTPException
import os
import random
import string
import struct
import src.data_generator as DG
from src.schemas import RandomArrayDTO, OrderArrayDTO, RandomMatrixDTO, OrderMatrixDTO, TextDTO

DIR = ".files"

class Filesystem:    
    def __init__(self):
        self.dir = os.path.join(os.getcwd(), DIR)
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def create_random_array(self, data: RandomArrayDTO):
        file_path = os.path.join(self.dir, data.filename)
        return DG.generate_random_array(data.size, data.dataType, data.min, data.max, file_path)
    
    def create_order_array(self, data: OrderArrayDTO):
        file_path = os.path.join(self.dir, data.filename)
        return DG.generate_ordered_array(data.size, data.dataType, data.fillType, data.start, data.step, data.interval, file_path)
    
    def create_random_matrix(self, data: RandomMatrixDTO):
        file_path = os.path.join(self.dir, data.filename)
        return DG.generate_random_matrix(data.rows, data.cols, data.dataType, data.min, data.max, file_path)
    
    def create_order_matrix(self, data: OrderMatrixDTO):
        file_path = os.path.join(self.dir, data.filename)
        return DG.generate_ordered_matrix(data.rows, data.cols, data.dataType, data.fillType, data.start, data.step, data.interval, file_path)

    def create_text(self, data: TextDTO):
        file_path = os.path.join(self.dir, data.filename)
        return DG.generate_text_file(data.text, file_path)

    def get_array(self, temp_file_path, page=1, limit=10):
        try:
            with open(temp_file_path, 'rb') as file:
                type_size = struct.unpack('<Q', file.read(8))[0]

                if type_size == 4:
                    fmt = '<i'
                elif type_size == 8:
                    fmt = '<d'
                elif type_size == 1:
                    fmt = '<b'
                elif type_size == 2:
                    fmt = '<h'
                else:
                    raise ValueError(f'Unsupported type size: {type_size}')
                
                size = struct.unpack('<Q', file.read(8))[0]

                total_pages = (size + limit - 1) // limit

                if page < 1:
                    page = 1
                elif page > total_pages:
                    page = total_pages

                offset = (page - 1) * limit
                file.seek(16 + offset * type_size)

                data = []
                for _ in range(min(limit, size - offset)):
                    element = struct.unpack(fmt, file.read(type_size))[0]
                    data.append(element)
                
                return {
                    "data": data,
                    "page": page,
                    "limit": limit,
                    "total_pages": total_pages,
                    "total_elements": size
                }
        finally:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as e:
                raise HTTPException(500, f"Error removing temporary file: {e}")
        
    def get_matrix(self, temp_file_path, page_row: int = 1, limit_row: int = 10, page_col: int = 1, limit_col: int = 10):
        try:
            with open(temp_file_path, 'rb') as file:
                type_size = struct.unpack('<Q', file.read(8))[0]
                
                if type_size == 4:
                    fmt = '<i'
                elif type_size == 8:
                    fmt = '<d'
                elif type_size == 1:
                    fmt = '<b'
                elif type_size == 2:
                    fmt = '<h'
                else:
                    raise ValueError(f'Unsupported type size: {type_size}')
                
                rows = struct.unpack('<Q', file.read(8))[0]
                cols = struct.unpack('<Q', file.read(8))[0]
                
                total_pages_row = (rows + limit_row - 1) // limit_row
                total_pages_col = (cols + limit_col - 1) // limit_col

                if page_row < 1:
                    page_row = 1
                elif page_row > total_pages_row:
                    page_row = total_pages_row

                if page_col < 1:
                    page_col = 1
                elif page_col > total_pages_col:
                    page_col = total_pages_col

                offset_row = (page_row - 1) * limit_row
                offset_col = (page_col - 1) * limit_col

                file.seek(24 + offset_row * cols * type_size + offset_col * type_size)

                data = []
                for i in range(min(limit_row, rows - offset_row)):
                    row = []
                    for j in range(min(limit_col, cols - offset_col)):
                        element = struct.unpack(fmt, file.read(type_size))[0]
                        row.append(element)
                    data.append(row)

                return {
                    "data": data,
                    "page_row": page_row,
                    "page_col": page_col,
                    "limit_row": limit_row,
                    "limit_col": limit_col,
                    "total_pages_row": total_pages_row,
                    "total_pages_col": total_pages_col,
                    "total_rows": rows,
                    "total_cols": cols
                }
        finally:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as e:
                raise HTTPException(500, f"Error removing temporary file: {e}")

    def get_text_data(self, temp_file_path: str):
        try:
            if not os.path.exists(temp_file_path):
                raise HTTPException(404, "Temporary file not found or already deleted")
                
            with open(temp_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return content
                
        except UnicodeDecodeError:
            try:
                with open(temp_file_path, 'r', encoding='cp1251') as file:
                    return file.read()
            except Exception as e:
                raise HTTPException(400,f"Failed to decode text file: {str(e)}")
                
        except Exception as e:
            raise HTTPException(500,f"Error reading text file: {str(e)}")
            
        finally:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as e:
                raise HTTPException(500, f"Error removing temporary file: {e}")