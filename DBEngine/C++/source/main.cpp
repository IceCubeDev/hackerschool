#include <TinyDB.h>

using namespace Tiny;

int main()
{
    TinyDB db;
    db.CreateTable("test_table", "int1 integer;int2 integer");
    return 0;
}
