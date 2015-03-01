__author__ = 'Ivan Dortulov'

import psycopg2

class QueryGenerator(object):

    def __init__(self, db_server, db_database, db_user, db_pass):
        self.db_connection = None
        self.db_server = db_server
        self.db_database = db_database
        self.db_user = db_user
        self.db_password = db_pass
        self.db_cursor = None

        self.tables = {}

        con_string = "host='" + str(self.db_server) + "' dbname='" + str(self.db_database) + "' " + \
                     "user='" + str(self.db_user) + "' password='" + str(self.db_password) + "'"

        try:
            self.db_connection = psycopg2.connect(con_string)
        except Exception as ex:
            print("[ERROR] Connection to the database has failed: ", ex)
        else:
            print("[INFO] Connected established with", db_server, "...")
            self.db_cursor = self.db_connection.cursor()

    def fetch_table_information(self):
        # Clear any previous information
        self.tables = {}

        # Query to fetch all tables and their respective columns
        table_fetch_query = \
            """
                SELECT
                    tbl.table_name,
                    cls.column_name,
                    cls.is_nullable
                FROM
                    information_schema.tables AS tbl
                LEFT JOIN
                    information_schema.columns AS cls ON tbl.table_name = cls.table_name
                WHERE
                    tbl.table_type = 'BASE TABLE' AND
                    tbl.table_schema NOT IN ('pg_catalog', 'information_schema');
            """

        foreign_key_fetch_query = \
            """
                SELECT DISTINCT
                    tc.TABLE_NAME, kcu.column_name,
                    ccu.TABLE_NAME AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    cols.is_nullable AS is_nullable
                FROM
                    information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage
                        AS kcu ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage
                        AS ccu ON ccu.constraint_name = tc.constraint_name
                    JOIN information_schema.COLUMNS
                        AS cols ON cols.TABLE_NAME = ccu.TABLE_NAME
                WHERE constraint_type = 'FOREIGN KEY';
            """

        # Obtain the names of all the tables, as well as their columns and store
        # that information in a hash
        try:
            self.db_cursor.execute(table_fetch_query)
        except Exception as ex:
            print("[ERROR] Unable to fetch table information: ", ex)
        else:
            tables = self.db_cursor.fetchall()

            for table in tables:
                table_name = table[0]
                table_column_name = table[1]
                table_column_is_nullable = table[2]

                if table_name not in self.tables.keys():
                    self.tables[table_name] = [{"column_name": table_column_name, "nullable":table_column_is_nullable}]
                else:
                    self.tables[table_name].append({"column_name": table_column_name, "nullable":table_column_is_nullable})

        # Obtain the names of all the foreign keys, as well as their relation
        # to other tables
        try:
            self.db_cursor.execute(foreign_key_fetch_query)
        except Exception as ex:
            print("[ERROR] Unable to fetch information about foreign keys: ", ex)
        else:
            foreign_keys = self.db_cursor.fetchall()

            for fkey in foreign_keys:
                table_name = fkey[0]
                column_name = fkey[1]
                foreign_table_name = fkey[2]
                foreign_table_column = fkey[3]
                nullable = fkey[4]

                if table_name in self.tables.keys():
                    columns = self.tables[table_name]

                    for column in columns:
                        if column_name == column["column_name"]:
                            column["references"] = (foreign_table_name, foreign_table_column)
                            column["nullable"] = nullable

    def build_table_graph(self):
        graph = {}

        for table in self.tables.keys():
            graph[table] = {"visited": False,
                            "neighbours": []}

        for table in self.tables.keys():
            current_node = graph[table]

            for column in self.tables[table]:
                edge = column.get("references")

                if edge is not None:
                    (foreign_table, foreign_key) = edge
                    current_node["neighbours"].append((column["column_name"], foreign_table, foreign_key))
                    node = graph[foreign_table]
                    node["neighbours"].append((foreign_key, table, column["column_name"]))

        print("\n\n[TABLE GRAPH]")
        for table in graph.keys():
            print(table, graph[table])

        return graph


    def print_table_information(self):
        print("[TABLE INFORMATION]")
        for table in self.tables.keys():
            print(table,":")
            for column in self.tables[table]:
                print("\t", column)

    def traverse_table_graph(self, graph, root):
        stack = [root]
        query = "SELECT\n\t*\nFROM\n\t" + str(root) + " AS " + root + '\n'

        while len(stack) > 0:
            table_name = stack.pop()
            current_node = graph[table_name]
            current_node["visited"] = True

            for neighbour in current_node["neighbours"]:
                (column_name, foreign_table_name, foreign_column_name) = neighbour
                node = graph[foreign_table_name]

                if node["visited"]:
                    continue
                else:
                    for column in self.tables[foreign_table_name]:
                        if column["column_name"] == foreign_column_name:
                            if column["nullable"]:
                                query += "LEFT JOIN\n\t" + foreign_table_name + " AS " + foreign_table_name
                                query += " ON " + table_name + "." + column_name + " = " + foreign_table_name + "." + foreign_column_name + "\n"
                            else:
                                query += "JOIN\n\t" + foreign_table_name + " AS " + foreign_table_name
                                query += " ON " + table_name + "." + column_name + " = " + foreign_table_name + "." + foreign_column_name + "\n"

                    stack.append(foreign_table_name)

        query += ";"
        return query

    def generate_query(self, start):
        self.fetch_table_information()
        self.print_table_information()
        graph = (self.build_table_graph())
        print("\n\n[GENERATED QUERY]")
        print(self.traverse_table_graph(graph, start))