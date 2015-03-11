__author__ = 'Ivan Dortulov'

from PydbSimple import PydbSimple
import fcntl
import time


def gte(x,y):
    if x < y: return False
    return True


def delete_test_data(db):
    db.delete([("int5", gte, 5)])


def main():
    start = time.time()
    fh = open("test_table.td", "r+b")
    fcntl.flock(fh, fcntl.LOCK_EX)
    db = PydbSimple(fh)
    delete_test_data(db)
    fcntl.flock(fh, fcntl.LOCK_UN)
    fh.close()
    end = time.time()
    print("Elapsed time: ", end - start)


if __name__ == "__main__":
    main()
