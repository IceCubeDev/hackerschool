__author__ = 'Ivan Dortulov'

import os
import fcntl
import struct
from collections import OrderedDict


class Pydb(object):

    INTEGER = 0
    STRING = 1
    CONSTRAINT_TYPES = {"not null": 0,
                        "primary key": 1}
    LOGGING = True
    DOCUMENT_ROOT = os.getcwd() + "/Databases/"

    uchar_t = "B"
    uint32_t = "I"

    def __init__(self):
        self.current_database = ""
        self.table_fh = None
        self.last_table = ""
        self.reuse_fh = False

    def create_database(self, database):
        path = Pydb.DOCUMENT_ROOT + database.lower()
        if not os.path.exists(path):
            os.makedirs(path)
            self.current_database = database.lower()

            Pydb.print_dbg_message("CREATE DATABASE")
            return True
        else:
            Pydb.print_dbg_message("[ERROR] Unable to create database: database already exists.")
            return False

    def select_database(self, database):
        path = Pydb.DOCUMENT_ROOT + database.lower()
        if os.path.exists(path):
            self.current_database = database

    def create_table(self, table, schema):
        if len(self.current_database) == 0:
            Pydb.print_dbg_message("Error! Unable to create table: No database selected.")
            return False

        path = os.path.join(Pydb.DOCUMENT_ROOT + self.current_database + "/",
                            table.lower() + ".tb")
        if os.path.exists(path):
            Pydb.print_dbg_message("[ERROR] Unable to create table: table already exists.")
            return False

        try:
            self.table_fh = open(path, "wb")
            fcntl.flock(self.table_fh, fcntl.LOCK_EX)
        except IOError as ex:
            Pydb.print_dbg_message("[ERROR] Unable to create table: " + str(ex.args[1]))
            self.table_fh.close()
            self.table_fh = None
            return False

        try:
            num_columns = len(schema)
            self.table_fh.write(struct.pack(Pydb.uint32_t, num_columns))

            for column in schema:
                self.table_fh.write(struct.pack(Pydb.uchar_t, column["column_type"]))
                self.table_fh.write(struct.pack(Pydb.uint32_t, len(column["column_name"])))
                self.table_fh.write(column["column_name"].encode())

                if column["column_constraints"] is not None:
                    self.table_fh.write(struct.pack(Pydb.uchar_t, 1))
                    self.table_fh.write(struct.pack(Pydb.uchar_t,
                                                    Pydb.CONSTRAINT_TYPES[column["column_constraints"]]))
                else:
                    self.table_fh.write(struct.pack(Pydb.uchar_t, 0))
        except IOError as ex:
            Pydb.print_dbg_message("[ERROR] Error creating table: " + str(ex.args[1]))
            self.table_fh.close()
            self.table_fh = None

        fcntl.flock(self.table_fh, fcntl.LOCK_UN)
        self.table_fh.close()
        self.table_fh = None
        Pydb.print_dbg_message("CREATE TABLE")
        return True

    def read_schema(self):
        schema = OrderedDict()

        if self.table_fh is not None:
            try:
                cur_pos = self.table_fh.seek(0, os.SEEK_END)
                self.table_fh.seek(0, os.SEEK_SET)
                read_chunk = self.table_fh.read(4)
                num_columns = struct.unpack(Pydb.uint32_t, read_chunk)[0]

                for i in range(0, num_columns):
                    column = OrderedDict()

                    column_type = struct.unpack(Pydb.uchar_t, self.table_fh.read(1))[0]
                    column["column_type"] = column_type

                    column_name_length = struct.unpack(Pydb.uint32_t, self.table_fh.read(4))[0]
                    column_name = self.table_fh.read(column_name_length).decode()

                    constraints = struct.unpack(Pydb.uchar_t, self.table_fh.read(1))[0]
                    if constraints:
                        constraint_type = struct.unpack(Pydb.uchar_t, self.table_fh.read(1))[0]
                        column["constraints"] = column_type
                    else:
                        column["constraints"] = None

                    schema[column_name.lower()] = column
            except IOError as ex:
                Pydb.print_dbg_message("[ERROR] Unable to read table schema: " + ex.args[1])
                return None

            self.table_fh.seek(cur_pos, os.SEEK_SET)
            return schema
        else:
            return None

    def insert(self, table, values):
        if len(self.current_database) == 0:
            Pydb.print_dbg_message("Error! Unable to insert: No database selected.")
            return False

        path = os.path.join(Pydb.DOCUMENT_ROOT + self.current_database + "/",
                            table.lower() + ".tb")
        if not os.path.exists(path):
            Pydb.print_dbg_message("[ERROR] Unable to insert: table does not exist.")
            return False

        try:
            self.table_fh = open(path, "r+b")
            fcntl.flock(self.table_fh, fcntl.LOCK_EX)
        except IOError as ex:
            Pydb.print_dbg_message("[ERROR] Error inserting: " + str(ex.args[1]))
            self.table_fh.close()
            self.table_fh = None
            return False

        table_schema = self.read_schema()
        print(table_schema)
        rows = []

        if table_schema is not None:
            for value_dict in values:
                row = []
                print(value_dict)
                for column in value_dict.keys():
                    if column not in table_schema.keys():
                        Pydb.print_dbg_message("[ERROR] Error inserting: Column " +
                                               column + " does not exists in table!")
                        fcntl.flock(self.table_fh, fcntl.LOCK_UN)
                        self.table_fh.close()
                        self.table_fh = None
                        return False
                    else:
                        column_dict = table_schema[column]
                        column_type = struct.pack(Pydb.uchar_t, column_dict["column_type"])
                        if column_dict["column_type"] == Pydb.INTEGER:
                            column_length = struct.pack(Pydb.uint32_t, 4)
                            column_value = struct.pack(Pydb.uint32_t, value_dict[column])
                        else:
                            column_length = struct.pack(Pydb.uint32_t, len(value_dict[column]))
                            column_value = value_dict[column].encode()

                        row.append([column_type, column_length, column_value])
                rows.append(row)

            for row in rows:
                self.table_fh.write(struct.pack(Pydb.uchar_t, 0))
                for value in row:
                    self.table_fh.write(b"".join(value))

            fcntl.flock(self.table_fh, fcntl.LOCK_UN)
            self.table_fh.close()
            self.table_fh = None
            Pydb.print_dbg_message("INSERT")
            return True

        else:
            Pydb.print_dbg_message("[ERROR] Error inserting: Unable to read table schema!")
            fcntl.flock(self.table_fh, fcntl.LOCK_UN)
            self.table_fh.close()
            self.table_fh = None
            return False

    @staticmethod
    def print_dbg_message(message):
        if Pydb.LOGGING:
            print(message)