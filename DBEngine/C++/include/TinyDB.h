#ifndef TINY_DATABASE_H_
#define TINY_DATABASE_H_

#include <cstdlib>
#include <cstdio>
#include <string.h>
#include <vector>
#include <errno.h>

#include <TinyRecord.h>

namespace Tiny
{
    class TinyDB
    {
        public:
            /**
             *  Default constructor.
             */
            TinyDB();

            /**
             *  Default destructor.
             */
            ~TinyDB();

            /**
             *  \brief Create a table.
             *
             *  Create a table with a given schema. The schema is a string with a format "column_name <space> value_type <space> [constraint]".
             *  The column constraint is optional.
             *  Example: str1k string primary;int1 integer
             *  Separating character is ';'
             *
             *  \param table The name of the table
             *  \param schema A string containing the table schema
             *  \return Returns 1 on success or a nagative value on error
             */
            int CreateTable(const std::string& table,
                            const std::string& schema);

            /**
             *  \brief Delete a table.
             *
             *  \param table Name of the table to delete
             *  \return true of success, false otherwise
             */
            bool DeleteTable(const std::string& table);
            /**
             *  \brief Check if a table exists.
             *
             *  \param table The name of table to check for
             *  \return Returns true if the table exists, false otherwise
             */
            bool TableExists(const std::string& table);

            /**
             *  \brief Set the current table.
             *
             *  All of the functions Insert(), Update(), Delete() and Select() execute for the currently selected table.
             *  If no table is selected the functions give an error.
             *
             *  To select a table use the Open() method. Only one
             *  table can be selected(opened) at any given time. To close a table use the Close() method.
             *
             *  \param table The name of the table to open.
             *  \return Returns true on success and a negative number on failure.
             */
            int Open(const std::string& table);

            /**
             *  \brief Close the currently open table.
             */
            void Close();

            void Select();
            int Insert(const TinyRecords& values);
            int Delete(const TinyRecords& where);
            int Update();

        private:
            FILE* m_currentTable;
            FILE* m_indexFile;

            std::vector<std::string>& split(const std::string &s, char delim,
                                            std::vector<std::string>& elems);
            std::string toLower(const std::string& str);
            bool fileExists (const std::string& name);

            int readSchema(TinySchema& schema);
    };
}

#endif // TINY_DATABASE_H_
