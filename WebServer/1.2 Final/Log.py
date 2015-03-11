__author__ = 'Ivan Dortulov'


class Log(object):

    LOG = False

    @staticmethod
    def d(tag, msg):
        if Log.LOG:
            print("[DEBUG]", tag, "-", msg)

    @staticmethod
    def w(tag, msg):
        if Log.LOG:
            print("[WARN]", tag, "-", msg)

    @staticmethod
    def e(tag, msg):
        if Log.LOG:
            print("[ERROR]", tag, "-", msg)
        raise RuntimeError(msg)
