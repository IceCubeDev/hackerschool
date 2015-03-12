__author__ = "Ivan Dortulov"

from PydbSimple import PydbSimple
import argparse


def read_schema(schema_file):
    try:
        schema_fh = open(schema_file, "r")
        schema_string = schema_fh.read().split('\n')

        schema = []
        for column in schema_string:
            tokens = column.split()
            column_name = tokens[0]
            column_type = tokens[1]

            if column_type == "int":
                column_type = PydbSimple.INTEGER
            elif column_type == "string":
                column_type = PydbSimple.STRING
            else:
                column_type = 0

            schema.append({"column_name": column_name,
                           "column_type": column_type})

        return schema

    except IOError as ex:
        print("Unable to read table schema: ", ex.args[1])
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c',
                        metavar=('table_name', 'schema_file'),
                        nargs=2,
                        dest='table_name',
                        help='Create a new table named table_name')

    args = vars(parser.parse_args())
    db = PydbSimple()

    if args["table_name"] is not None:
        table_name = args["table_name"][0]
        schema_file = args["table_name"][1]

        schema = read_schema(schema_file)
        db.create_table(table_name, schema)

if __name__ == "__main__":
    main()