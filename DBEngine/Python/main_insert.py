__author__ = 'Ivan Dortulov'

from PydbSimple import PydbSimple
import fcntl
import time


def insert_test_data(db, num_rows):
    # db.insert([(1, PydbSimple.INTEGER),
    #            (2, PydbSimple.INTEGER),
    #            (3, PydbSimple.INTEGER),
    #            (4, PydbSimple.INTEGER),
    #            (5, PydbSimple.INTEGER),
    #            ('a', PydbSimple.STRING),
    #            ('b', PydbSimple.STRING),
    #            ('c', PydbSimple.STRING)])
    for i in range(0, num_rows):
        db.insert([(i, PydbSimple.INTEGER),
                   (i + 2, PydbSimple.INTEGER),
                   (i % 2, PydbSimple.INTEGER),
                   (int(i / 6), PydbSimple.INTEGER),
                   (i * 2, PydbSimple.INTEGER),
                   ("a" * 1000, PydbSimple.STRING),
                   ("b" * 10000, PydbSimple.STRING),
                   ("c" * 100000, PydbSimple.STRING)])


def main():
    start = time.time()
    fh = open("test_table.td", "ab")
    fcntl.flock(fh, fcntl.LOCK_EX)
    db = PydbSimple(fh)
    insert_test_data(db, 100000)
    fcntl.flock(fh, fcntl.LOCK_UN)
    fh.close()
    end = time.time()
    print("Elapsed time: ", end - start)


if __name__ == "__main__":
    main()