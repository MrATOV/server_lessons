import os
import random
import string
import struct

DIR = ".files"
IMAGE_DIR = "images"
ARRAY_DIR = "arrays"
MATRIX_DIR = "matrix"

def generate_file_token(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

class Filesystem:    
    def __init__(self):
        self.dir = os.path.join(os.getcwd(), DIR)
        image_dir = os.path.join(self.dir, IMAGE_DIR)
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        array_dir = os.path.join(self.dir, ARRAY_DIR)
        if not os.path.exists(array_dir):
            os.makedirs(array_dir)
        matrix_dir = os.path.join(self.dir, MATRIX_DIR)
        if not os.path.exists(matrix_dir):
            os.makedirs(matrix_dir)

    async def save_image(self, file, extension):
        image_dir = os.path.join(self.dir, IMAGE_DIR)
        filename = f"{generate_file_token(32)}.{extension}"
        file_path = os.path.join(image_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(await file.read())
        return filename

    def get_image(self, filename):
        image_dir = os.path.join(self.dir, IMAGE_DIR)
        file_path = os.path.join(image_dir, filename)
        if os.path.exists(file_path):
            return file_path
        
    def delete_image(self, filename):
        image_dir = os.path.join(self.dir, IMAGE_DIR)
        file_path = os.path.join(image_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    def get_array(self, filename, page=1, limit=10):
        array_dir = os.path.join(self.dir, ARRAY_DIR)
        file_path = os.path.join(array_dir, filename)
        with open(file_path, 'rb') as file:
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
        
    def get_matrix(self, filename, page_row: int = 1, limit_row: int = 10, page_col: int = 1, limit_col: int = 10):
        # Формируем путь к файлу
        matrix_dir = os.path.join(self.dir, MATRIX_DIR)
        file_path = os.path.join(matrix_dir, filename)
        
        # Открываем файл для чтения в бинарном режиме
        with open(file_path, 'rb') as file:
            # Чтение размера типа данных (8 байт)
            type_size = struct.unpack('<Q', file.read(8))[0]
            
            # Определение формата данных на основе размера типа
            if type_size == 4:
                fmt = '<i'  # int32
            elif type_size == 8:
                fmt = '<d'  # double
            elif type_size == 1:
                fmt = '<b'  # int8
            elif type_size == 2:
                fmt = '<h'  # int16
            else:
                raise ValueError(f'Unsupported type size: {type_size}')
            
            # Чтение количества строк и столбцов (по 8 байт каждое)
            rows = struct.unpack('<Q', file.read(8))[0]
            cols = struct.unpack('<Q', file.read(8))[0]
            

            # # Вычисление общего количества страниц для строк и столбцов
            total_pages_row = (rows + limit_row - 1) // limit_row
            total_pages_col = (cols + limit_col - 1) // limit_col

            # Корректировка номера страницы для строк
            if page_row < 1:
                page_row = 1
            elif page_row > total_pages_row:
                page_row = total_pages_row

            # Корректировка номера страницы для столбцов
            if page_col < 1:
                page_col = 1
            elif page_col > total_pages_col:
                page_col = total_pages_col

            # Вычисление офсетов для строк и столбцов
            offset_row = (page_row - 1) * limit_row
            offset_col = (page_col - 1) * limit_col

            # Перемещение указателя файла на начало данных
            # 24 байта — это размер заголовка (type_size + rows + cols)
            file.seek(24 + offset_row * cols * type_size + offset_col * type_size)

            # Чтение данных с учетом лимитов
            data = []
            for i in range(min(limit_row, rows - offset_row)):
                row = []
                for j in range(min(limit_col, cols - offset_col)):
                    element = struct.unpack(fmt, file.read(type_size))[0]
                    row.append(element)
                data.append(row)

            # Возврат результата
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