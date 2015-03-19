#ifndef TINY_RECORD_H_
#define TINY_RECORD_H_

#include <stdint.h>
#include <sstream>
#include <map>

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

    typedef std::map<std::string, TinyValue> TinyRecords;
    typedef std::map<std::string, uint8_t> TinySchema;
}

#endif // TINY_RECORD_H_
