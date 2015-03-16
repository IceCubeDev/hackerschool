#ifndef CDB_H_
#define CDB_H_

#include <cstdlib>
#include <cstdio>
#include <vector>
#include <algorithm>
#include <string>
#include <stdint.h>
#include "Cursor.h"
#include "ContentValues.h"

namespace cdb
{
    class CDatabase
    {
        public:
            CDatabase();
            ~CDatabase();

            bool CreateTable(const std::string& table, const std::string& columns);

            bool Open(const std::string& table);
            void Close();

            Cursor Select(const std::string& table, const ContentValues& where);
            int    Delete(const std::string& table, const ContentValues& where);
            bool   Insert(const std::string& table, const ContentValues& values);
            int    Update(const std::string& table, const ContentValues& where,
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
