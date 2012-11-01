import collections


#Token types
T_LIT = 0
T_COL = 1
T_OPR = 2
T_KWD = 3
T_HLP = 4
T_MOD = 5
T_EXP = 6
T_EQU = 7

# Operator types
OP_ADD = 0
OP_SUB = 1
OP_MUL = 2
OP_DIV = 3
OP_MOD = 4
OP_POW = 5

OP_AND = 6
OP_OR = 7

OP_NE = 8
OP_LT = 9
OP_LE = 10
OP_EQ = 11
OP_GE = 12
OP_GT = 13

OP_NULLNE = 14
OP_NULLEQ = 15

OP_SW = 16
OP_EW = 17
OP_CT = 18
OP_BT = 19

OP_OPAR = 20
OP_CPAR = 21


Token = collections.namedtuple('Token', ('type', 'value'))
