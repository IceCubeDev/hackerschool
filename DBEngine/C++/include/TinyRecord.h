#ifndef TINY_RECORD_H_
#define TINY_RECORD_H_

#include <vector>
#include <stdint.h>
#include <sstream>
#include <tr1/unordered_map>

namespace Tiny
{
    struct TinyValue
    {
        TinyValue();
        TinyValue(uint8_t type, const std::string& value);
        TinyValue(const TinyValue& other);

        uint8_t type;
        std::string value;

        static const uint8_t INTEGER = 0;
        static const uint8_t STRING = 1;

        static const uint8_t ROW_DELETED = 1;
        static const uint8_t ROW_LOCKED = 1 << 1;

        static uint32_t toInt(const std::string& value);
        static std::string toString(const uint32_t value);
    };

    typedef struct column
    {
        column(uint8_t type, uint8_t constraint)
        {
            this->type = type;
            this->constraint = constraint;
        }

        uint8_t type;
        uint8_t constraint;
    } TinyColumn;

    typedef std::tr1::unordered_map<std::string, TinyValue> TinyRecords;

    class TinySchema
    {
        public:
            TinyColumn get(const std::string& key);
            void set(const std::string& key, TinyColumn column);

            std::vector<std::string>& keys() { return m_keys; }
            std::vector<TinyColumn>& values() { return m_values; }

        private:
            std::vector<std::string> m_keys;
            std::vector<TinyColumn> m_values;
    };
}

#endif // TINY_RECORD_H_
