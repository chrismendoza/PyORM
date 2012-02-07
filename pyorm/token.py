class Token(object):
    class __metaclass__(type):
        tokens = [
            'Literal',
            'Column',
            'Operator',
            'Keyword',
            'Helper',
            'Alias',
            'Model'
        ]

        def __getattr__(cls, attr):
            return cls.tokens.index(attr)

        def gettype(cls, index):
            return cls.tokens[index]
