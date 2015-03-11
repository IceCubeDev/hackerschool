__author__ = 'Ivan Dortulov'

from PydbSimple import PydbSimple
import fcntl
import time


def gte(x,y):
    if x < y: return False
    return True


def select_test_data(db):
    db.select([("int1", gte, 0)], False)


def main():
    start = time.time()
    fh = open("test_table.td", "rb")
    fcntl.flock(fh, fcntl.LOCK_EX)
    db = PydbSimple(fh)
    select_test_data(db)
    fcntl.flock(fh, fcntl.LOCK_UN)
    fh.close()
    end = time.time()
    print("Elapsed time: ", end - start)


if __name__ == "__main__":
    main()
