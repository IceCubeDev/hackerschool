#include <TinyDB.h>

namespace Tiny
{
    //---------------------------------------------------------------------------------
    TinyDB::TinyDB()
    {
        m_currentTable = NULL;
        m_indexFile = NULL;
    }

    //---------------------------------------------------------------------------------
    TinyDB::~TinyDB()
    {
        Close();
    }

    //---------------------------------------------------------------------------------
    int TinyDB::CreateTable(const std::string& table,
                            const std::string& columns)
    {
        // Table and index file paths
        std::string tablePath = "Databases/" + toLower(table) + ".td";
        std::string indexPath = "Databases/" + toLower(table) + ".index";
        printf("Creating table '%s' in '%s'\n", toLower(table).c_str(), tablePath.c_str());

        // Check if table exists
        if (fileExists(tablePath))
        {
            printf("Error - Unable to create table '%s': Table already exists.\n",
                   toLower(table).c_str());
            return -1;
        }

        // Create index file
        FILE* pFile = fopen(indexPath.c_str(), "wb");
        // Check for errors
        if (!pFile)
        {
            printf("Error - Unable to create table '%s': %s\n", toLower(table).c_str(),
                   strerror(errno));
            return errno;
        }
        fclose(pFile);
        pFile = NULL;

        // Create the table file
        pFile = fopen(tablePath.c_str(), "wb");
        // Check for errors
        if (!pFile)
        {
            printf("Error - Unable to create table '%s': %s\n", toLower(table).c_str(),
                   strerror(errno));
            remove(indexPath.c_str());
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
            uint8_t constraint = 0;

            // Check if constraints are present
            if (tokens.size() > 2)
            {
                std::string columnConstraint = tokens[2];
                if (columnConstraint == "primary")
                    constraint = 1;
            }

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

            // Write the column constraints
            fwrite(&constraint, sizeof(uint8_t), 1, pFile);

            // Write column name length and column name
            int length = columnName.length();
            fwrite(&length, sizeof(uint32_t), 1, pFile);
            fwrite(columnName.c_str(), 1, length, pFile);

            // Check for errors
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
        std::string tablePath = "Databases/" + toLower(table) + ".td";
        std::string indexPath = "Databases/" + toLower(table) + ".index";

        // Delete the actual table (if it exists)
        if (fileExists(tablePath))
        {
            if (remove(tablePath.c_str()) != 0)
                return false;
        } else
        {
            return false;
        }

        // Delete the index file (if it exists)
        if (fileExists(indexPath))
        {
            if (remove(indexPath.c_str()) != 0)
                return false;
        }

        return true;
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
        // Path to table
        std::string tablePath = "Databases/" + toLower(table) + ".td";
        std::string indexPath = "Databases/" + toLower(table) + ".index";
        printf("Opening table '%s' in '%s'\n", toLower(table).c_str(), tablePath.c_str());

        // Check if table exists
        if (!fileExists(tablePath))
        {
            printf("Error - Unable to open table: table '%s' does not exist.\n",
                   toLower(table).c_str());
            return -1;
        }

        // Open table and index file
        m_currentTable = fopen(tablePath.c_str(), "r+b");
        if (!m_currentTable)
        {
            printf("Error - There was an error writing to the table: %s\n",
                        strerror(errno));
            return errno;
        }

        // Just open the index file. If there is an error, either the index does not
        // exists or there is another error. In either case we just won't use
        // indexing for searching
        m_indexFile = fopen(indexPath.c_str(), "r+b");

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

        if (m_indexFile)
        {
            fclose(m_indexFile);
            m_indexFile = NULL;
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
        printf("Inserting ...\n");

        // Read the table schema
        TinySchema schema;
        readSchema(schema);
        fseek(m_currentTable, 0, SEEK_END);

        // Write row flags (lock the row)
        size_t rowStart = ftell(m_currentTable);
        uint8_t flags = TinyValue::ROW_LOCKED;
        // Get the position in the file where this row starts.
        // We will come back here later to unlock the row
        fwrite(&flags, sizeof(uint8_t), 1, m_currentTable);

        // Write values, following the schema
        std::vector<std::string>::iterator it;
        TinyRecords::const_iterator cit;
        std::string key;
        TinyColumn column;

        for (it = schema.keys().begin(); it != schema.keys().end(); ++it)
        {
            key = (*it);
            column = schema.get(key);
            cit = values.find(key);
            TinyValue record((*cit).second);

            // If we need to write an integer
            if (record.type == TinyValue::INTEGER)
            {
                uint32_t len = 4;
                uint32_t val = TinyValue::toInt(record.value);
                fwrite(&len, sizeof(uint32_t), 1, m_currentTable);
                fwrite(&val, sizeof(uint32_t), 1, m_currentTable);
                printf("Wrote: %d bytes\n", len);

                // Index this bish, but only if it is a primary key
                // TODO: Binary TREEEEEE
                if (m_indexFile != NULL)
                {
                    fwrite(&val, sizeof(uint32_t), 1, m_indexFile);
                    fwrite(&rowStart, sizeof(uint32_t), 1, m_indexFile);
                }
            }
            // If we need to write a string
            else if (record.type == TinyValue::STRING)
            {
                uint32_t len = record.value.length();
                fwrite(&len, sizeof(uint32_t), 1, m_currentTable);
                fwrite(record.value.c_str(), 1, len, m_currentTable);
                printf("Wrote: %d bytes\n", len);
            }

            // Check for errors
            if (ferror(m_currentTable))
            {
                printf("Error - Unable to insert: %s\n",
                        strerror(errno));
                return errno;
            }
        }

        // We reached the end of the row, we need to unlock it
        size_t rowEnd = ftell(m_currentTable);
        fseek(m_currentTable, rowStart, SEEK_SET);
        flags = 0;
        fwrite(&flags, sizeof(uint8_t), 1, m_currentTable);
        fseek(m_currentTable, rowEnd, SEEK_SET);

        return 1;
    }

    //---------------------------------------------------------------------------------
    int TinyDB::Delete(const TinyRecords& where)
    {
        if (m_currentTable == NULL)
        {
            printf("Error - Unable to delete: no table selected.\n");
            return 0;
        }

        // Read the table schema
        TinySchema schema;
        readSchema(schema);

        // Read each row and search for values
        uint8_t flags;
        std::string key;
        TinyValue columnValue;
        TinyColumn column;
        TinyRecords records;
        uint32_t len;
        std::vector<std::string>::iterator it;

        while (!feof(m_currentTable))
        {
            size_t rowStart = ftell(m_currentTable);
            fread(&flags, sizeof(uint8_t), 1, m_currentTable);
            if (flags & TinyValue::ROW_LOCKED)
                break;

            for (it = schema.keys().begin(); it != schema.keys().end(); ++it)
            {
                key = (*it);
                column = schema.get(key);

                if (column.type == TinyValue::INTEGER)
                {
                    uint32_t value;
                    fread(&len, sizeof(uint32_t), 1, m_currentTable);
                    fread(&value, sizeof(uint32_t), 1, m_currentTable);
                    records[key] = TinyValue(column.type, TinyValue::toString(value));
                    printf("Read %d bytes.\n", len);
                }
                else if (column.type == TinyValue::STRING)
                {
                    char* value;
                    fread(&len, sizeof(uint32_t), 1, m_currentTable);
                    value = new char[len + 1];
                    value[len + 1] = '\0';
                    fread(value, 1, len, m_currentTable);
                    records[key] = TinyValue(column.type, value);
                    printf("Read %d bytes.\n", len);
                    delete [] value;
                }

                if (ferror(m_currentTable))
                {
                    printf("Error - Unable to insert: %s\n",
                        strerror(errno));
                    return errno;
                }
            }

            uint16_t criteria = 0;
            TinyRecords::const_iterator cit;
            for (cit = where.begin(); cit != where.end(); ++cit)
            {
                if (cit->second.value == records[cit->first].value)
                {
                    criteria ++;
                }
            }

            if (criteria == where.size())
            {
                printf("Match found!\n");
                size_t rowEnd = ftell(m_currentTable);
                fseek(m_currentTable, rowStart, SEEK_SET);
                uint8_t flags = TinyValue::ROW_DELETED;
                fwrite(&flags, sizeof(uint8_t), 1, m_currentTable);
            }
        }
    }

    //---------------------------------------------------------------------------------
    int TinyDB::readSchema(TinySchema& schema)
    {
        if (m_currentTable != NULL)
        {
            printf("Reading schema ...\n");
            fseek(m_currentTable, 0, SEEK_SET);

            // Read number of columns
            uint32_t numCols = 0;
            fread(&numCols, sizeof(uint32_t), 1, m_currentTable);

            // foreach column
            uint8_t type;
            uint8_t constraint;
            uint32_t nameLen;
            char* name = NULL;

            for (uint32_t i = 0; i < numCols; i ++)
            {
                // Read the column type
                fread(&type, sizeof(uint8_t), 1, m_currentTable);
                // Read the column constraint
                fread(&constraint, sizeof(uint8_t), 1, m_currentTable);
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
                    return errno;
                }

                schema.set(name, TinyColumn(type, constraint));
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
