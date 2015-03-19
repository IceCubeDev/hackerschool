#ifndef TINY_DATABASE_H_
#define TINY_DATABASE_H_

#include <cstdlib>
#include <cstdio>
#include <string.h>
#include <vector>

#include <TinyRecord.h>

namespace Tiny
{
    class TinyDB
    {
        public:
            TinyDB();
            ~TinyDB();

            int CreateTable(const std::string& table,
                            const std::string& columns);
            bool DeleteTable(const std::string& table);
            bool TableExists(const std::string& table);

            int Open(const std::string& table);
            void Close();

            void Select();
            int Insert(const TinyRecords& values);
            int Delete();
            int Update();

        private:
            FILE* m_currentTable;

            std::vector<std::string>& split(const std::string &s, char delim,
                                            std::vector<std::string>& elems);
            std::string toLower(const std::string& str);
            bool fileExists (const std::string& name);

            int readSchema(TinySchema& schema);
    };
}

#endif // TINY_DATABASE_H_
