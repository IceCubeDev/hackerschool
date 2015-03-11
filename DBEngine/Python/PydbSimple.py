__author__ = 'IvanDortulov'

import struct
import os
import fcntl
from collections import OrderedDict


class PydbSimple(object):

    # Common variable types
    uint8_t = "B"
    uint16_t = "H"
    uint32_t = "I"

    # Column value types
    INTEGER = 0
    STRING = 1

    LOG = False

    def __init__(self, fh=None):
        self.table_handle = fh

    def insert(self, values):
        if self.write_record(values):
            #print("INSERT(1)")
            pass
        else:
            print("Insert failed.")

    def select(self, criteria, print_result=True):
        if self.table_handle is not None:
            self.table_handle.seek(0, os.SEEK_END)
            file_size = self.table_handle.tell()
            self.table_handle.seek(0, os.SEEK_SET)
            schema = self.read_schema()
            if schema is None:
                print("Select failed.")
                return False

            while self.table_handle.tell() < file_size:
                row = self.read_record(schema)

                # Row was deleted so we need to skip it
                if len(row.keys()) == 0:
                    continue

                if self.match_record(row, criteria):
                    if print_result:
                        print(row)
        else:
            return False

    def delete(self, criteria):
        if self.table_handle is not None:

            self.table_handle.seek(0, os.SEEK_END)
            file_size = self.table_handle.tell()
            self.table_handle.seek(0, os.SEEK_SET)

            schema = self.read_schema()
            if schema is None:
                print("Delete failed.")
                return False

            delete_count = 0

            while self.table_handle.tell() < file_size:
                current_position = self.table_handle.tell()
                row = self.read_record(schema)

                if self.match_record(row, criteria):
                    next_record_position = self.table_handle.tell()
                    self.table_handle.seek(current_position)
                    self.table_handle.write(struct.pack(PydbSimple.uint8_t, 1))
                    self.table_handle.seek(next_record_position)
                    delete_count += 1

            print("DELETE(", delete_count, ")")
            return True
        else:
            return False

    def update(self, criteria, new_values):
        if self.table_handle is not None:

            self.table_handle.seek(0, os.SEEK_END)
            file_size = self.table_handle.tell()
            self.table_handle.seek(0, os.SEEK_SET)

            schema = self.read_schema()
            if schema is None:
                print("Select failed.")
                return False

            update_count = 0

            while self.table_handle.tell() < file_size:
                current_position = self.table_handle.tell()
                row = self.read_record(schema)
                return_position = self.table_handle.tell()

                # this row has already been deleted, skip it
                if len(row.keys()) == 0:
                    continue

                if self.match_record(row, criteria):
                    # Mark row as deleted
                    self.table_handle.seek(current_position, os.SEEK_SET)
                    self.table_handle.write(struct.pack(PydbSimple.uint8_t, 1))

                    # Append new row to the end of the file
                    self.table_handle.seek(0, os.SEEK_END)

                    new_row = []
                    for column in schema:
                        column_name = column["column_name"]
                        column_type = column["column_type"]

                        if column_name in new_values.keys():
                            new_value = new_values[column_name]
                        else:
                            new_value = row[column_name]

                        new_row.append((new_value, column_type))

                    self.write_record(new_row)
                    self.table_handle.seek(return_position, os.SEEK_SET)
                    update_count += 1

            print("UPDATE(", update_count, ")")
            return True
        else:
            return False

    def create_table(self, table_name, schema):
        try:
            # Create the table file
            path = table_name.lower() + ".td"
            self.table_handle = open(path, "wb")
            fcntl.flock(self.table_handle, fcntl.LOCK_EX)

            self.print_dbg_message("create_table",
                                   "Creating table '" + table_name + "' in '" + path + "'")

            # Get the number of columns in the table
            num_columns = len(schema)
            packed_num_columns = struct.pack(PydbSimple.uint32_t, num_columns)
            self.table_handle.write(packed_num_columns)

            self.print_dbg_message("create_table",
                                   "Wrote number of columns - " + str(num_columns) +
                                   " Position: " + str(self.table_handle.tell()))

            # Write the table header (schema)
            for column in schema:
                column_type = column["column_type"]
                column_name = column["column_name"]
                column_name_length = len(column_name)

                packed_column_type = struct.pack(PydbSimple.uint8_t, column_type)
                packed_column_name_length = struct.pack(PydbSimple.uint32_t, column_name_length)

                bytes = self.table_handle.write(packed_column_type)
                self.print_dbg_message("create_table",
                                       "Wrote column type - " + str(column_type) + " (" + str(bytes) + " bytes)"
                                       " Position: " + str(self.table_handle.tell()))

                bytes = self.table_handle.write(packed_column_name_length)
                self.print_dbg_message("create_table",
                                       "Wrote column name length - " + str(column_name_length) + " (" + str(bytes) + " bytes)"
                                       "Position: " + str(self.table_handle.tell()))
                bytes = self.table_handle.write(column_name.encode())
                self.print_dbg_message("create_table",
                                       "Wrote column name - " + column_name + " (" + str(bytes) + " bytes)"
                                       " Position: " + str(self.table_handle.tell()))

            # Unlock and close the file
            fcntl.flock(self.table_handle, fcntl.LOCK_UN)
            self.table_handle.close()
            self.table_handle = None

            print("CREATE TABLE")
            return True
        except IOError as ex:
            print("Unable to create table: " + str(ex.args[1]))
            return False

    def read_schema(self):
        if self.table_handle is not None:
            try:
                schema = []
                # Read 4 byte unsigned integer at beginning of file (the table schema)
                num_columns = struct.unpack(PydbSimple.uint32_t, self.table_handle.read(4))[0]
                self.print_dbg_message("read_schema",
                                       "Read number of columns - " + str(num_columns) +
                                       " Position: " + str(self.table_handle.tell()))

                # Read information about the columns
                for i in range(0, num_columns):
                    column_type = struct.unpack(PydbSimple.uint8_t, self.table_handle.read(1))[0]
                    self.print_dbg_message("read_schema",
                                           "Read column type - " + str(column_type) +
                                           " Position: " + str(self.table_handle.tell()))

                    column_name_length = struct.unpack(PydbSimple.uint32_t, self.table_handle.read(4))[0]
                    self.print_dbg_message("read_schema",
                                           "Read column name length - " + str(column_name_length) +
                                           " Position: " + str(self.table_handle.tell()))

                    column_name = self.table_handle.read(column_name_length).decode()
                    self.print_dbg_message("read_schema",
                                           "Read column name - " + str(column_name) +
                                           " Position: " + str(self.table_handle.tell()))
                    schema.append({"column_name": column_name, "column_type": column_type})


                return schema
            except IOError as ex:
                print("Error reading schema: " + str(ex.args[1]))
                return None
        return None

    def read_record(self, schema):
        if self.table_handle is not None:
            try:
                row_deleted = struct.unpack(PydbSimple.uint8_t, self.table_handle.read(1))[0]
                self.print_dbg_message("read_record",
                                       "Read row deleted flag - " + str(row_deleted) +
                                       " Position: " + str(self.table_handle.tell()))
                row_length = struct.unpack(PydbSimple.uint32_t, self.table_handle.read(4))[0]
                self.print_dbg_message("read_record",
                                       "Read row length - " + str(row_length) +
                                       " Position: " + str(self.table_handle.tell()))

                if row_deleted:
                    self.table_handle.seek(row_length, os.SEEK_CUR)
                    self.print_dbg_message("read_record",
                                           "Row is deleted, skipping to " + str(row_length) +
                                           " Position: " + str(self.table_handle.tell()))
                    return OrderedDict()
                else:
                    row = OrderedDict()
                    for column in schema:
                        column_name = column["column_name"]
                        column_type = column["column_type"]
                        column_value = b""
                        column_length = 0

                        if column_type == PydbSimple.INTEGER:
                            column_length = struct.unpack(PydbSimple.uint32_t, self.table_handle.read(4))[0]
                            self.print_dbg_message("read_record",
                                                   "Read column data length - " + str(column_length) +
                                                   " Position: " + str(self.table_handle.tell()))

                            column_value = struct.unpack(PydbSimple.uint32_t, self.table_handle.read(column_length))[0]
                            self.print_dbg_message("read_record",
                                                   "Read column value - " + str(column_value) +
                                                   " Position: " + str(self.table_handle.tell()))
                        elif column_type == PydbSimple.STRING:
                            column_length = struct.unpack(PydbSimple.uint32_t, self.table_handle.read(4))[0]
                            self.print_dbg_message("read_record",
                                                   "Read column data length - " + str(column_length) +
                                                   " Position: " + str(self.table_handle.tell()))
                            column_value = self.table_handle.read(column_length).decode()
                            self.print_dbg_message("read_record",
                                                   "Read column value - " + str(column_value) +
                                                   " Position: " + str(self.table_handle.tell()))

                        row[column_name] = column_value
                    return row
            except IOError as ex:
                print("Error reading record" + str(ex.args[1]))
                return None
        return None

    def write_record(self, row):
        if self.table_handle is not None:
            try:
                delete_flag = struct.pack(PydbSimple.uint8_t, 0)
                bytes = self.table_handle.write(delete_flag)
                self.print_dbg_message("write_record",
                                       "Wrote row deleted flag - " + str(delete_flag) + " (" + str(bytes) + " bytes)"
                                       " Position: " + str(self.table_handle.tell()))
                data = b""

                for (value, type) in row:
                    packed_value = b""
                    packed_length = 0

                    if type == PydbSimple.INTEGER:
                        packed_length = struct.pack(PydbSimple.uint32_t, 4)
                        packed_value = struct.pack(PydbSimple.uint32_t, value)
                        self.print_dbg_message("write_record", "Adding " + str((4, value)))
                    elif type == PydbSimple.STRING:
                        packed_length = struct.pack(PydbSimple.uint32_t, len(value))
                        packed_value = value.encode()
                        self.print_dbg_message("write_record", "Adding " + str((len(value), value)))

                    data += packed_length + packed_value

                bytes = self.table_handle.write(struct.pack(PydbSimple.uint32_t, len(data)))
                self.print_dbg_message("write_record",
                                       "Wrote row length - " + str(len(data)) + " (" + str(bytes) + " bytes)"
                                       " Position: " + str(self.table_handle.tell()))
                bytes = self.table_handle.write(data)
                self.print_dbg_message("write_record",
                                       "Wrote row data (" + str(bytes) + " bytes)"
                                       " Position: " + str(self.table_handle.tell()))
                return True
            except IOError as ex:
                print("Error writing record: " + str(ex.args[1]))
                return False
        return False

    def match_record(self, row, criteria):
        match = 0
        for key in criteria:
            (column, predicate, value) = key
            column = column.lower()
            if column in row.keys():
                if predicate(row[column], value):
                    match += 1

        if match == len(criteria):
            return True
        else:
            return False

    def print_dbg_message(self, tag, msg):
        if PydbSimple.LOG:
            print("[", tag, "]", msg)