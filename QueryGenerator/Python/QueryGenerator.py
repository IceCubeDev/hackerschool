__author__ = 'Ivan Dortulov'

import psycopg2
import copy


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
                    self.tables[table_name] = [{"column_name": table_column_name, "nullable": table_column_is_nullable}]
                else:
                    self.tables[table_name].append(
                        {"column_name": table_column_name, "nullable": table_column_is_nullable})

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
        self.fetch_table_information()
        graph = {}

        for table in self.tables.keys():
            graph[table] = {"table_name": table,
                            "visited": 0,
                            "neighbours": []}

        for table in self.tables.keys():
            current_node = graph[table]

            for column in self.tables[table]:
                edge = column.get("references")

                if edge is not None:
                    (foreign_table, foreign_key) = edge
                    current_node["neighbours"].append(
                        (column["column_name"], foreign_table, foreign_key, column["nullable"]))

        print("\n\n[TABLE GRAPH]")
        for table in graph.keys():
            print(table, graph[table])

        return graph

    def print_table_information(self):
        print("[TABLE INFORMATION]")
        for table in self.tables.keys():
            print(table, ":")
            for column in self.tables[table]:
                print("\t", column)

    def generate_query(self, graph, root):
        query = "SELECT * FROM " + root + " AS _" + root + "\n"
        return query + traverse_graph_helper(graph, graph[root], '_' + root, [root]) + ";"


def traverse_graph_helper(g, cur, prev, path):
    cur['visited'] += 1
    if cur['neighbours'] is None:
        return ""

    query = ""
    # print("cur:", cur['name'], ";prev", prev, ";path:", path)
    for edges in cur['neighbours']:
        path_copy = copy.copy(path)
        neighbour = g[edges[1]]

        # We already have visited this node, check if we are in a cycle
        if neighbour['visited'] > 0:
            #print("\tNeighbour ", edges[1], "already visited ", neighbour['visited'], " times!")
            if len(path) > 1:
                if path[0] == edges[1] or path[-1] == edges[1]:
                    #print("\t\tCycle!")
                    if neighbour['visited'] > 2:
                        return ""

        new = "".join(path) + "_" + edges[1]
        # If it is nullable
        if edges[3]:
            query += "LEFT JOIN " + edges[1] + " AS " + new + "\n"
            query += "   ON " + new + "." + edges[2] + " = " + prev + "." + edges[0] + "\n"
        else:
            query += "JOIN " + edges[1] + " AS " + new + "\n"
            query += "   ON " + new + "." + edges[2] + " = " + prev + "." + edges[0] + "\n"

        path_copy.append(edges[1])
        #print("\t", path_copy, new)
        query += traverse_graph_helper(g, neighbour, new, path_copy)

    return query