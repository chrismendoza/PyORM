import time
from expression import *

C = Column

ops = {
    OP_ADD: '+',
    OP_SUB: '-',
    OP_MUL: '*',
    OP_DIV: '/',
    OP_MOD: '%',
    OP_POW: '^',
    OP_AND: 'AND',
    OP_OR: 'OR',
    OP_NE: '!=',
    OP_LT: '<',
    OP_LE: '<=',
    OP_EQ: '=',
    OP_GE: '>=',
    OP_GT: '>',
    OP_NULLNE: 'IS NOT',
    OP_NULLEQ: 'IS',
    OP_OPAR: '(',
    OP_CPAR: ')'}

cache = {}
max_iter = 15000


t = Expression(
        (C.test * 3 * 5) + 4 == 'taco, taco, taco',
        (C.test2 == 3 / C.cheese.cow.field) / 3 * C.loser,
        C.test32 == 'fish',
        C.runner == 1)

cache_start = time.time()
for i in range(0, max_iter):
    if hash(t) in cache:
        pass
    else:
        t.tokens

        tokens = []
        for token in t.tokens:
            if token.type == T_LIT:
                tokens.append('%s')
            elif token.type == T_OPR:
                tokens.append(ops[token.value])
            elif token.type == T_COL:
                if len(token.value._path) > 1:
                    tokens.append('`{0}`.`{1}`'.format('___'.join(token.value._path[:-1]), token.value._path[-1]))
                else:
                    tokens.append('`{0}`'.format(token.value._path[0]))

        cache[hash(t)] = ' '.join(tokens)

cache_end = time.time()

start = time.time()
for i in range(0, max_iter):
    t.tokens

    tokens = []
    for token in t.tokens:
        if token.type == T_LIT:
            tokens.append('%s')
        elif token.type == T_OPR:
            tokens.append(ops[token.value])
        elif token.type == T_COL:
            if len(token.value._path) > 1:
                tokens.append('`{0}`.`{1}`'.format('___'.join(token.value._path[:-1]), token.value._path[-1]))
            else:
                tokens.append('`{0}`'.format(token.value._path[0]))

end = time.time()


print('cache total time: {0} ({1} iterations)'.format(cache_end - cache_start, max_iter))
print('nocache total time: {0} ({1} iterations)'.format(end - start, max_iter))

print(' '.join(tokens))
print(t.literals)
exit()

