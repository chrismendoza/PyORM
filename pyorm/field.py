class Field(object):
    def __init__(self, default=None, null=False, primary_key=False, autoincrement=False):
        pass

    def to_python(self, value):
        return value

    def to_db(self, value):
        return value
