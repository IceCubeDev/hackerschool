#include <TinyDB.h>

using namespace Tiny;

int main()
{
    TinyDB db;
    db.CreateTable("test_table", "int1 integer;int2 integer");
    TinyRecords values;
    values["int1"] = TinyValue(TinyValue::INTEGER,
                               "1");
    values["int2"] = TinyValue(TinyValue::INTEGER,
                               "2");
    if (!db.Open("test_table"))
    {
        return -1;
    }
    db.Insert(values);
    db.Close();

    return 0;
}
