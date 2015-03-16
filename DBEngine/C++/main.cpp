#include <iostream>
#include "cdb.h"

int main()
{
    cdb::CDatabase db;
    db.CreateTable("TeSt", "int1 integer;int2 integer;int3 integer;int4 integer;int5 integer;str1k string;str10k string;str100k string");
    db.Open("test");
    db.Close();
    return 0;
}
