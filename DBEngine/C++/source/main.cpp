#include <TinyDB.h>

using namespace Tiny;

void buildTestData(TinyRecords& values,
                   int a, int b, int c, int d, int e,
                   char f, char g, char h);

int main()
{
    TinyDB db;
    db.CreateTable("test_table", "int1 integer;int2 integer;int3 integer;int4 integer;int5 integer;str1k string;str10k string;str100k string");

    TinyRecords values;
    buildTestData(values, 1, 2, 3, 4, 5, 'a', 'b', 'c');

    if (!db.Open("test_table"))
    {
        return -1;
    }
    db.Insert(values);
    db.Close();

    return 0;
}

void buildTestData(TinyRecords& values,
                   int a, int b, int c, int d, int e,
                   char f, char g, char h)
{
    values.clear();
    std::string str1k = "";
    std::string str10k = "";
    std::string str100k = "";

    values["int1"] = TinyValue(TinyValue::INTEGER,
                               TinyValue::toString(a));
    values["int2"] = TinyValue(TinyValue::INTEGER,
                               TinyValue::toString(b));
    values["int3"] = TinyValue(TinyValue::INTEGER,
                               TinyValue::toString(c));
    values["int4"] = TinyValue(TinyValue::INTEGER,
                               TinyValue::toString(d));
    values["int5"] = TinyValue(TinyValue::INTEGER,
                               TinyValue::toString(e));

    for(int i = 0; i < 100000; i ++)
    {
        if (i < 1000)
            str1k += f;
        if (i < 10000)
            str10k += g;
        str100k += h;
    }

    values["str1k"] = TinyValue(TinyValue::STRING,
                               str1k);
    values["str10k"] = TinyValue(TinyValue::STRING,
                               str10k);
    values["str100k"] = TinyValue(TinyValue::STRING,
                               str100k);
}
