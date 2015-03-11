__author__ = 'Ivan Dortulov'

from PydbSimple import PydbSimple
import fcntl


def gte(x,y):
    if x < y: return False
    return True


def update_test_data(db):
    db.update([("int1", gte, 0)], {"str1k": "d" * 1000,
                                   "str10k": "e" * 10000,
                                   "str100k": "f" * 100000})

def main():
    fh = open("test_table.td", "r+b")
    fcntl.flock(fh, fcntl.LOCK_EX)
    db = PydbSimple(fh)
    update_test_data(db)
    fcntl.flock(fh, fcntl.LOCK_UN)
    fh.close()


if __name__ == "__main__":
    main()
