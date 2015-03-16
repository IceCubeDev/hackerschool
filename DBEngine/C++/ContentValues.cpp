#include "ContentValues.h"

namespace cdb
{
    ContentValues::ContentValues()
    {

    }

    ContentValues::~ContentValues()
    {
        m_values.clear();
    }

    void ContentValues::putInt(const std::string& key, int value)
    {
        record_t record;
        record.type = INTEGER;
        std::stringstream ss;
        ss << value;
        record.value = ss.str();
        m_values[key] = record;
    }

    void ContentValues::putString(const std::string& key, const std::string& value)
    {
        record_t record;
        record.type = STRING;
        record.value = value;
        m_values[key] = record;
    }

    int ContentValues::getInt(const std::string& key)
    {
        std::map<std::string, record_t>::iterator it;
        it = m_values.find(key);
        assert(it != m_values.end());
        std::stringstream ss(it->second.value);
        int int_value;
        ss >> int_value;
        return int_value;
    }

    std::string ContentValues::getString(const std::string& key)
    {
        std::map<std::string, record_t>::iterator it;
        it = m_values.find(key);
        assert(it != m_values.end());
        return it->second.value;
    }
}
