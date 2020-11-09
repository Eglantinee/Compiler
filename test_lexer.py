from compiler import Lexer

names = (
    'NUM', 'ID', 'INT', 'FLOAT', 'LBRA', 'RBRA', 'RETURN', 'LPAR', 'RPAR', 'SEMICOLON', 'NOT', 'PROD', 'EQUAL', 'XOR',
    'DIV', 'EOF', 'QUESTION', 'COLON')

file = 'lab1.c'
lex = Lexer(file)
lexems = lex.next_token()

for i in lexems:
    print('{:<13}'.format(names[i.type]) + "-> ", end=" ")
    print(i)