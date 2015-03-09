__author__ = 'Ivan Dortulov'

import os


class Pydb(object):

    def __init__(self):
        self.current_database = ""
        self.table_fh = None
        self.last_table = ""
        self.reuse_fh = False

    def create_table(self, table, schema):
        if len(self.current_database) == 0:
            print("Error! Unable to create table: No database selected.")
        else:
            try:
                fh = open(os.path.join(self.current_database, table + ".ts"), "wb")
            except IOError as ex:
                pass
            else:
                for column in schema:
                    fh.write()

                fh.close()