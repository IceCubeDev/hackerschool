#ifndef CDB_H_
#define CDB_H_

#include <cstdlib>
#include <cstdio>
#include <vector>
#include <string>
#include <stdint.h>

// For stderror
#include <string.h>
#include <errno.h>

#include "Cursor.h"
#include "ContentValues.h"

namespace cdb
{
    class CDatabase
    {
        public:
            CDatabase();
            ~CDatabase();

            /**
             *  This function create a table.
             *
             * \param table The name of the table.
             * \param columns The column definitions in the format 'column_name column_type' where column_type can be either 'integer' or 'string'.
             * \return Returns true on success, false otherwise. The function prints an error string to the standart output.
             */
            bool CreateTable(const std::string& columns);

            /**
             *  Opens a table for reading and writing.
             *
             *  Only one table can be opened at a time. If there is a table already opened, the Open() function will call Close() to
             *  close that talbe.
             *

             * \return Returns true on sucesss, false otherwise. The function prints an error string to the standart output.
             */
            bool Open(const std::string& table);

            /**
             *  Closes the currently open table.
             */
            void Close();

            /**
             * Executes a select query and returns a cursor object to iterate the results.
             *
             * Keep in mind that the data might change while you iterating if other queries are executing.
             *
             * \param where The where clause.
             * \return A Cursor object used to iterate the results.
             */
            Cursor Select(const ContentValues& where);


            int    Delete(const ContentValues& where);
            bool   Insert(const ContentValues& values);
            int    Update(const ContentValues& where,
                          const ContentValues& values);
        private:
            FILE* m_th;

            std::vector<std::string>& split(const std::string &s, char delim,
                                            std::vector<std::string>& elems);
            std::string toLower(const std::string& str);
            bool fileExists (const std::string& name);
    };
}

#endif // CDB_H_
