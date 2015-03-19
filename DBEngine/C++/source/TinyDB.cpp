#include <TinyDB.h>

namespace Tiny
{
    //---------------------------------------------------------------------------------
    TinyDB::TinyDB()
    {
        m_currentTable = NULL;
    }

    //---------------------------------------------------------------------------------
    TinyDB::~TinyDB()
    {
        if (m_currentTable)
        {
            fclose(m_currentTable);
            m_currentTable = NULL;
        }
    }

    //---------------------------------------------------------------------------------
    int TinyDB::CreateTable(const std::string& table,
                            const std::string& columns)
    {
        std::string path = "Databases/" + toLower(table) + ".td";
        // Create database file
        printf("Creating table '%s' in '%s'\n", toLower(table).c_str(), path.c_str());

        if (fileExists(path))
        {
            printf("Error - Unable to create table '%s': Table already exists.\n",
                   toLower(table).c_str());
            return -1;
        }

        FILE* pFile = fopen(path.c_str(), "wb");
        // Check for errors
        if (!pFile)
        {
            printf("Error - Unable to create table '%s': %s\n", toLower(table).c_str(),
                   strerror(errno));
            return errno;
        }

        // Parse the column definition string
        std::vector<std::string> columns_vector;
        split(columns, ';', columns_vector);

        // Write number of columns
        uint32_t numCols = columns_vector.size();
        fwrite(&numCols, sizeof(uint32_t), 1, pFile);

        // Iterate over each column definition
        std::vector<std::string>::iterator it;
        for (it = columns_vector.begin(); it != columns_vector.end(); ++it)
        {
            std::vector<std::string> tokens;
            split((*it), ' ', tokens);
            // ### DEBUG ###
            printf("%-15s => %s\n", tokens[0].c_str(), tokens[1].c_str());

            std::string columnName = tokens[0];
            std::string columnType = tokens[1];

            // Write column type
            if (columnType == "integer")
            {
                int type = 0;
                fwrite(&type, sizeof(uint8_t), 1, pFile);
            }
            else if (columnType == "string")
            {
                int type = 1;
                fwrite(&type, sizeof(uint8_t), 1, pFile);
            }

            // Write column name length and column name
            int length = columnName.length();
            fwrite(&length, sizeof(uint32_t), 1, pFile);
            fwrite(columnName.c_str(), 1, length, pFile);

            if (ferror (pFile))
            {
                printf("Error - There was an error writing to the table: %s\n",
                        strerror(errno));
                fclose(pFile);
                return false;
            }
        }

        fclose(pFile);
        return true;
    }

    //---------------------------------------------------------------------------------
    bool TinyDB::DeleteTable(const std::string& table)
    {
        std::string path = "Databases/" + toLower(table) + ".td";
        if (fileExists(path))
        {
            if (remove(path.c_str()) == 0)
                return true;

            return false;
        }

        return false;
    }

    //---------------------------------------------------------------------------------
    bool TinyDB::TableExists(const std::string& table)
    {
        std::string path = "Databases/" + toLower(table) + ".td";
        if (fileExists(path))
            return true;

        return false;
    }

    //---------------------------------------------------------------------------------
    int TinyDB::Open(const std::string& table)
    {
        std::string path = "Databases/" + toLower(table) + ".td";
        printf("Opening table '%s' in '%s'\n", toLower(table).c_str(), path.c_str());

        if (!fileExists(path))
        {
            printf("Error - Unable to open table: table '%s' does not exist.\n",
                   toLower(table).c_str());
            return -1;
        }

        m_currentTable = fopen(path.c_str(), "r+b");
        if (!m_currentTable)
        {
            printf("Error - There was an error writing to the table: %s\n",
                        strerror(errno));
            return errno;
        }

        return true;
    }

    //---------------------------------------------------------------------------------
    void TinyDB::Close()
    {
        if (m_currentTable)
        {
            fclose(m_currentTable);
            m_currentTable = NULL;
        }
    }

    //---------------------------------------------------------------------------------
    int TinyDB::Insert(const TinyRecords& values)
    {
        if (m_currentTable == NULL)
        {
            printf("Error - Unable to insert: no table selected.\n");
            return 0;
        }

        // Read the table schema
        TinySchema schema;
        readSchema(schema);
        fseek(m_currentTable, 0, SEEK_END);

        // Write row flags
        uint8_t flags = 0;
        fwrite(&flags, sizeof(uint8_t), 1, m_currentTable);

        // Write values, following the schema
        TinySchema::iterator it;
        TinyRecords::const_iterator cit;
        std::string key;
        for (it = schema.begin(); it != schema.end(); ++it)
        {
            key = it->first;
            cit = values.find(key);
            TinyValue record((*cit).second);

            if (record.type == TinyValue::INTEGER)
            {
                uint32_t len = 4;
                uint32_t val = TinyValue::toInt(record.value);
                fwrite(&len, sizeof(uint32_t), 1, m_currentTable);
                fwrite(&val, sizeof(uint32_t), 1, m_currentTable);
            }
            else if (record.type == TinyValue::STRING)
            {
                uint32_t len = record.value.length();
                fwrite(&len, sizeof(uint32_t), 1, m_currentTable);
                fwrite(record.value.c_str(), 1, len, m_currentTable);
            }

            if (ferror(m_currentTable))
            {
                printf("Error - Unable to insert: %s\n",
                        strerror(errno));
                fclose(m_currentTable);
                return errno;
            }
        }

        return 0;
    }

    //---------------------------------------------------------------------------------
    int TinyDB::readSchema(TinySchema& schema)
    {
        if (m_currentTable != NULL)
        {
            fseek(m_currentTable, 0, SEEK_SET);

            // Read number of columns
            uint32_t numCols = 0;
            fread(&numCols, sizeof(uint32_t), 1, m_currentTable);

            // foreach column
            uint8_t type;
            uint32_t nameLen;
            char* name = NULL;

            for (uint32_t i = 0; i < numCols; i ++)
            {
                // Read the column type
                fread(&type, sizeof(uint8_t), 1, m_currentTable);
                // Read the length of the column name
                fread(&nameLen, sizeof(uint32_t), 1, m_currentTable);
                // Read the column name
                name = new char[nameLen + 1];
                name[nameLen] = '\0';
                fread(name, 1, nameLen, m_currentTable);

                if (ferror (m_currentTable))
                {
                    printf("Error - There was an error reading the table schema: %s\n",
                            strerror(errno));
                    fclose(m_currentTable);
                    return errno;
                }

                schema[name] = type;
                printf("%s => %d\n", name, type);
                delete [] name;
            }

            return numCols;
        }
        else
        {
            printf("Error - No table selected.\n");
            return -1;
        }
    }

    //---------------------------------------------------------------------------------
    std::vector<std::string>& TinyDB::split(const std::string &s, char delim,
                                            std::vector<std::string>& elems)
    {
        std::stringstream ss(s);
        std::string item;
        while (std::getline(ss, item, delim))
        {
            elems.push_back(item);
        }
        return elems;
    }

    //---------------------------------------------------------------------------------
    std::string TinyDB::toLower(const std::string& str)
    {
        std::string lower;
        std::string::const_iterator it;
        for (it = str.begin(); it != str.end(); ++it)
        {
            lower += (int(*it) > 64 && int(*it) < 91 ?
                      int(*it) + 32 : (*it));
        }
        return lower;
    }

    //---------------------------------------------------------------------------------
    bool TinyDB::fileExists (const std::string& name)
    {
        if (FILE *file = fopen(name.c_str(), "r")) {
            fclose(file);
            return true;
        } else {
            return false;
        }
    }
}
