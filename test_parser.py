from compiler import Lexer, Parser
from collections.abc import Iterable

nodes = ['VAR', 'CONST', 'RET', 'EXPR', 'FUNC', 'UNOP', 'BINOP', 'FACTOR', 'TERM',  'DECL', 'STMT', 'ID', 'PROG']

file = 'lab1.c'
lex = Lexer(file)
lexems = lex.next_token()
# pars = Parser(lexems)
# ast = pars.parse()

print("#" * 30)
for i in lexems:
    print(i)

# def iter_prt(ast):
#     if ast is None:
#         return
#     print(ast.kind)
#     iter_prt(ast.op1)



def tree_ast(ast, n):
    if ast is None:
        return
    print(' ' * 2 * n, nodes[ast.kind], end=" ")
    if ast.kind == Parser.CONST:
        print(ast.value)
    else:
        print(" ")
    if isinstance(ast.op1, Iterable):
        for i in ast.op1:
            tree_ast(i, n + 1)
    else:
        tree_ast(ast.op1, n + 1)


# tree_ast(ast, 1)

