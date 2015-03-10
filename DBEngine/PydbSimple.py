__author__ = 'IvanDortulov'

import struct
import os
import fcntl
from collections import OrderedDict


class PydbSimple(object):

    uchar_t = "B"
    uint32_t = "I"
    INTEGER = 0
    STRING = 1

    @staticmethod
    def create_table(table, columns):
        try:
            path = table.lower() + ".td"
            fh = open(path, "wb")
            fcntl.flock(fh, fcntl.LOCK_EX)

            num_columns = len(columns)
            packed_num_columns = struct.pack(PydbSimple.uint32_t, num_columns)
            fh.write(packed_num_columns)

            for column in columns:
                column_type = column["column_type"]
                column_name = column["column_name"]
                column_name_length = len(column_name)

                packed_column_type = struct.pack(PydbSimple.uchar_t, column_type)
                packed_column_name_length = struct.pack(PydbSimple.uint32_t, column_name_length)

                fh.write(packed_column_type)
                fh.write(packed_column_name_length)
                fh.write(column_name.encode())

            fcntl.flock(fh, fcntl.LOCK_UN)
            fh.close()
            return True
        except IOError as ex:
            print("Unable to create table: " + str(ex.args[1]))
            return False

    @staticmethod
    def read_schema(fh):
        try:
            schema = []
            num_columns = struct.unpack(PydbSimple.uint32_t, fh.read(4))[0]

            for i in range(0, num_columns):
                column_type = struct.unpack(PydbSimple.uchar_t, fh.read(1))[0]
                column_name_length = struct.unpack(PydbSimple.uint32_t, fh.read(4))[0]
                column_name = fh.read(column_name_length).decode()
                schema.append({"column_name": column_name, "column_type": column_type})

            return schema
        except IOError as ex:
            print("Error reading schema: " + ex.args[1])
            return None

    @staticmethod
    def insert(fh, values):
        try:
            fh.write(struct.pack(PydbSimple.uchar_t, 0))

            data = b""

            for (value, type) in values:
                packed_type = struct.pack(PydbSimple.uchar_t, type)
                packed_value = b""
                packed_length = 0

                if type is PydbSimple.INTEGER:
                    packed_value = struct.pack(PydbSimple.uint32_t, value)
                    packed_length = struct.pack(PydbSimple.uint32_t, 4)
                elif type is PydbSimple.STRING:
                    packed_value = value.encode()
                    packed_length = struct.pack(PydbSimple.uint32_t, len(value))

                data += packed_length + packed_value

            fh.write(struct.pack(PydbSimple.uint32_t, len(data)))
            fh.write(data)
        except IOError as ex:
            print("Error inserting: " + ex.args[1])
            return False
        else:
            return True

    @staticmethod
    def select(fh, criteria):
        fh.seek(0, os.SEEK_END)
        file_size = fh.tell()
        fh.seek(0, os.SEEK_SET)
        schema = PydbSimple.read_schema(fh)
        if schema is None:
            print("Error in select: unable to read table schema!")
            return False
        print("File size: ", file_size)
        while fh.tell() < file_size:
            row_deleted = struct.unpack(PydbSimple.uchar_t, fh.read(1))[0]
            row_length = struct.unpack(PydbSimple.uint32_t, fh.read(4))[0]

            if row_deleted:
                print("Skipping row")
                fh.seek(row_length, os.SEEK_CUR)
            else:
                row = OrderedDict()
                for column in schema:
                    column_name = column["column_name"]
                    column_type = column["column_type"]
                    column_value = b""
                    column_length = 0

                    if column_type == PydbSimple.INTEGER:
                        column_length = struct.unpack(PydbSimple.uint32_t, fh.read(4))[0]
                        column_value = struct.unpack(PydbSimple.uint32_t, fh.read(4))[0]
                    elif column_type == PydbSimple.STRING:
                        column_length = struct.unpack(PydbSimple.uint32_t, fh.read(4))[0]
                        column_value = fh.read(column_length).decode()

                    row[column_name] = column_value

                match = 0
                for key in criteria:
                    (column, predicate, value) = key
                    column = column.lower()
                    if column in row.keys():
                        if predicate(row[column], value):
                            match += 1

                if match == len(criteria):
                    #print(row)
                    pass