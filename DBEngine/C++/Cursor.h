#ifndef CURSOR_H_
#define CURSOR_H_

namespace cdb
{
    class Cursor
    {
        public:
            Cursor();
            ~Cursor();

            bool hasNext();
            void moveToNext();
            void moveToLast();
            void moveToFirst();

        private:

    };
}

#endif // CURSOR_H_
