#include <iostream>
#include <cstdlib>
#include <cstdio>

using namespace std;

int main(int argc, char* argv[])
{
    if (argc > 1)
    {
        for (int i = 1; i < argc; i ++)
        {
            FILE* pFile = fopen(argv[i], "rb");
            if (!pFile)
                std::cout << "Unable to open file!\n";

            uint16_t num_columns;
            fread(&num_columns, sizeof(uint16_t), 1, pFile);
            std::cout << "Table: " << argv[1] << std::endl;
            std::cout << "Column#: " << num_columns << std::endl;

            for (int j = 0; j < num_columns; j ++)
            {
                uint16_t len;
                fread(&len, sizeof(uint16_t), 1, pFile);

                char *name = new char[len + 1];
                fread(name, len, 1, pFile);
                name[len] = '\0';
                if (j == num_columns - 1)
                    std::cout << name << std::endl;
                else
                    std::cout << name << ",";

                delete [] name;
            }

            fclose(pFile);
        }
    }

    char c;
    cin >> c;
    return 0;
}
