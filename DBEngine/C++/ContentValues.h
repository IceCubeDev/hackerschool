#ifndef CONTENT_VALUES_H_
#define CONTENT_VALUES_H_

#include <map>
#include <sstream>
#include <assert.h>

namespace cdb
{
    typedef struct
    {
        int type;
        std::string value;
    } record_t;

    class ContentValues
    {
        public:
            ContentValues();
            ~ContentValues();

            void putInt(const std::string& key, int value);
            void putString(const std::string& key, const std::string& value);

            int getInt(const std::string& key);
            std::string getString(const std::string& key);

            static const int INTEGER = 0;
            static const int STRING = 1;
        private:
            std::map<std::string, record_t> m_values;
    };
}

#endif // CONTENT_VALUES_H_
