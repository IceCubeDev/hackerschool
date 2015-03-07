__author__ = 'Ivan Dortulov'

import xlrd


def extract_data_from_xls(file, table, schema, columns_map):
    book = xlrd.open_workbook("ekatte_xls/" + file)
    sh = book.sheet_by_index(0)
    columns = sh.row(0)

    column_names = list()
    for i in range(0, len(columns)):
        column_names.append(columns[i].value)

    rows = list()
    for i in range(1, sh.nrows):
        row = sh.row(i)
        row_dict = dict()
        for j in range(0, len(row)):
            row_dict[column_names[j]] = row[j].value
        rows.append(row_dict)

    query = ""
    if schema is not None:
        query = "DROP TABLE IF EXISTS " + table + ";\n"
        query += "CREATE TABLE " + table + "(\n"

        i = 0
        for (key, value) in schema.items():
            if i < len(schema.keys()) - 1:
                query += "\t" + key + " " + value + ",\n"
            elif i == len(schema.keys()) - 1:
                query += "\t" + key + " " + value + "\n"
            i += 1
        query += ");\n"

    for row in rows:
        query += "INSERT INTO " + table + "("
        i = 0
        for (column, new_name) in columns_map.items():
            if i < len(columns_map.values()) - 1:
                query += new_name + ","
            elif i == len(columns_map.values()) - 1:
                query += new_name
            i += 1

        query += ") VALUES ("

        i = 0
        for (column, new_name) in columns_map.items():
            if i < len(columns_map.values()) - 1:
                query += "'" + row[column] + "', "
            elif i == len(columns_map.values()) - 1:
                query += "'" + row[column] + "'"
            i += 1
        query += ");\n"

    return query

sql = open("schema.sql", "w")
sql.write(extract_data_from_xls("Ek_atte.xls", "ekatte",
    {"id"            : "int NOT NULL auto_increment",
     "ekatte"        : "varchar(5) NOT NULL",
     "grad_selo"     : "varchar(3) NOT NULL",
     "naseleno_mqsto": "varchar(36) NOT NULL",
     "oblast"        : "varchar(3) NOT NULL",
     "obshtina"      : "varchar(5) NOT NULL",
     "kmetstvo"      : "varchar(8) NOT NULL",
     "PRIMARY KEY"   :  "(id)"},
    {"abc"     : "id",
     "ekatte"  : "ekatte",
     "t_v_m"   : "grad_selo",
     "name"    : "naseleno_mqsto",
     "oblast"  : "oblast",
     "obstina" : "obshtina",
     "kmetstvo": "kmetstvo"}))

sql.write(extract_data_from_xls("Ek_obl.xls", "oblast",
    {"id"            : "int NOT NULL auto_increment",
     "oblast"        : "varchar(3) NOT NULL",
     "ekatte"        : "varchar(5) NOT NULL",
     "oname"         : "varchar(128) NOT NULL",
     "region"        : "varchar(4) NOT NULL",
     "PRIMARY KEY"   : "(id)"},
    {"abc"     : "id",
     "oblast"  : "oblast",
     "ekatte"  : "ekatte",
     "name"    : "oname",
     "region"  : "region"}))

sql.write(extract_data_from_xls("Ek_reg1.xls", "region",
    {"id"            : "int NOT NULL auto_increment",
     "rname"         :  "varchar(128) NOT NULL",
     "region"        : "varchar(3) NOT NULL",
     "PRIMARY KEY"   : "(id)"},
    {"region"  : "region",
     "name"    : "rname"}))

sql.write(extract_data_from_xls("Ek_reg2.xls", "region", None,
    {"region"  : "region",
     "name"    : "rname"}))

sql.write(extract_data_from_xls("Ek_kmet.xls", "kmetstvo",
    {"kmetstvo"      : "varchar(8) NOT NULL",
     "ekatte"        :  "varchar(5) NOT NULL",
     "kname"         : "varchar(128) NOT NULL",
     "PRIMARY KEY"   : "(kmetstvo)"},
    {"kmetstvo"  : "kmetstvo",
     "ekatte"    : "ekatte",
     "name"      : "kname"}))

sql.write(extract_data_from_xls("Ek_obst.xls", "obshtina",
    {"id"            : "int NOT NULL auto_increment",
     "ekatte"        :  "varchar(5) NOT NULL",
     "obshtina"      : "varchar(5) NOT NULL",
     "obname"        : "varchar(128) NOT NULL",
     "PRIMARY KEY"   : "(id)"},
    {"abc"     : "id",
     "ekatte"  : "ekatte",
     "name"    : "obname",
     "obstina" : "obshtina"}))

sql.close()