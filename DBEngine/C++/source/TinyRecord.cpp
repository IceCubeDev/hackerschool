#include <TinyRecord.h>

namespace Tiny
{

    //---------------------------------------------------------------------------------
    TinyValue::TinyValue()
    {
        this->type = INTEGER;
        this->value = "0";
    }

    //---------------------------------------------------------------------------------
    TinyValue::TinyValue(uint8_t type, const std::string& value)
    {
        this->type = type;
        this->value = value;
    }

    //---------------------------------------------------------------------------------
    TinyValue::TinyValue(const TinyValue& other)
    {
        this->type = other.type;
        this->value = other.value;
    }

    //---------------------------------------------------------------------------------
    uint32_t TinyValue::toInt(const std::string& value)
    {
        std::stringstream ss(value);
        uint32_t val;
        ss >> val;
        return val;
    }

    //---------------------------------------------------------------------------------
    std::string TinyValue::toString(const uint32_t value)
    {
        std::stringstream ss;
        ss << value;
        return ss.str();
    }

    //---------------------------------------------------------------------------------
    TinyColumn TinySchema::get(const std::string& key)
    {
        std::vector<std::string>::iterator it;
        for (size_t i = 0; i < key.size(); i ++)
        {
            if (m_keys[i] == key)
                return m_values[i];
        }

        return TinyColumn(255, 255);
    }

    //---------------------------------------------------------------------------------
    void TinySchema::set(const std::string& key, TinyColumn column)
    {
        m_keys.push_back(key);
        m_values.push_back(column);
    }
}
