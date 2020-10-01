import sys
from collections import namedtuple
from collections.abc import Iterable


class Lexer:
    def __init__(self, file):
        self.file = open(file, 'rb')
        self.value = None
        self.row = 1
        self.symbol = 1
        self.st = self.file.read(1)  # First symbol from file
        self.tokens = []
        self.Token = namedtuple("Token", 'valid, type, row, symbol, value',
                                defaults=(self.value,))

    NUM, ID, INT, FLOAT, LBRA, RBRA, RETURN, LPAR, RPAR, SEMICOLON, NOT, PROD, EOF = range(13)
    SYMBOLS = {'{': LBRA, '}': RBRA, '(': LPAR, ')': RPAR, ';': SEMICOLON, '!': NOT, '*': PROD}
    WORDS = {'int': INT, 'return': RETURN}

    def get(self):
        self.symbol += 1
        self.st = self.file.read(1)
        self.file.seek(self.file.tell())

    def next_token(self):
        self.value = None
        self.symbol = self.symbol
        while True:
            if len(self.st) == 0:
                self.tokens.append(self.Token(True, Lexer.EOF, self.row, self.symbol))
                break
            elif self.st.decode().isspace():
                if self.st == b'\n':
                    self.row += 1
                    self.symbol = 1
                self.get()
            elif self.st.decode() in Lexer.SYMBOLS:
                self.tokens.append(self.Token(True, Lexer.SYMBOLS[self.st.decode()], self.row, self.symbol))
                self.get()
            elif self.st.isdigit():
                k = "int"
                tmp_str = b''
                while True:
                    if self.st.isdigit():
                        tmp_str += self.st
                    elif self.st.decode() == '.' and k == "int":
                        k = "float"
                        tmp_str += self.st
                    elif self.st.decode() == "x" and k == "int":
                        if int(tmp_str) == 0 and len(tmp_str) == 1:
                            k = "hex"
                            tmp_str += self.st
                    elif k == "hex" and self.st in b'abcdef':
                        tmp_str += self.st
                    else:
                        break
                    self.get()
                if k == 'int' and tmp_str.decode()[0] == '0' and len(tmp_str.decode()) > 1:
                    # sys.exit("IDK")
                    self.tokens.append(self.Token(False, None, self.row, self.symbol - len(tmp_str)))
                else:
                    self.tokens.append(
                        self.Token(True, Lexer.NUM, self.row, self.symbol - len(tmp_str), value=[tmp_str, k]))
            elif self.st.decode().isalpha():
                ident = ''
                while self.st.isalnum() or self.st.decode() == "_":
                    ident = ident + self.st.decode()
                    self.get()
                if ident in Lexer.WORDS:
                    self.tokens.append(self.Token(True, Lexer.WORDS[ident], self.row, self.symbol - len(ident)))
                else:
                    self.tokens.append(self.Token(True, Lexer.ID, self.row, self.symbol - len(ident), value=ident))
            else:
                self.tokens.append(self.Token(False, None, self.row, self.symbol))
                self.get()
        return self.tokens


class Node:
    def __init__(self, kind, value=None, name=None, op1=None, op2=None):
        self.kind = kind
        self.value = value
        self.op1 = op1
        self.op2 = op2
        self.name = name
        self.type = type


class Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.token = None

    def next_token(self):
        if self.tokens:
            self.token = self.tokens.pop(0)
            if self.token.valid is False:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg + " invalid value")

        else:
            self.token = None

    # @staticmethod
    # def debug(msg):
    #     print("DEBUG: Create node" + msg)

    VAR, CONST, RET, EXPR, FUNC, UNOP, BINOP, FACTOR, TERM, PROG = range(10)
    names = set()
    arrs = []
    terms = []
    stmts = {}

    @staticmethod
    def error(msg):
        print('Parser error:', msg)
        sys.exit(1)

    def factor(self):
        if self.token.type == Lexer.LPAR:
            n = Node(Parser.EXPR)
            self.next_token()
            tmp = self.factor()
            if tmp is not None:
                n.op1 = tmp
            else:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg)
            self.next_token()
            if self.token.type != Lexer.RPAR:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg)
            return n
        elif self.token.type == Lexer.NOT:
            n = Node(Parser.UNOP)
            k = 1
            while True:
                self.next_token()
                if self.token.type == Lexer.NOT:
                    k += 1
                    continue
                else:
                    break

            if self.token.type == Lexer.NUM:
                if k % 2 != 0:
                    n.value = self.factor().value
                else:
                    n.value = 0 if self.factor().value != 0 else 1
            else:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg)
            return n
        elif self.token.type == Lexer.NUM:
            value, mtype = self.token.value
            tok_val = None
            if mtype == "int":
                tok_val = int(value)
            elif mtype == 'float':
                tok_val = int(float(value))
            elif mtype == 'hex':
                tok_val = int(value, 16)
            n = Node(Parser.CONST, tok_val)
            return n
        else:
            print(self.token.type)
            msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
            self.error(msg)

    def term(self):
        n = Node(Parser.TERM)
        self.terms.append(self.factor())
        self.next_token()
        if self.token.type == Lexer.PROD:
            n.kind = Parser.BINOP
            self.next_token()
            while True:
                self.terms.append(self.factor())
                self.next_token()
                if self.token.type != Lexer.PROD and self.token.type != Lexer.SEMICOLON:
                    msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                    self.error(msg)
                if self.token.type == Lexer.SEMICOLON:
                    n.op1 = self.terms
                    return n
                self.next_token()
        elif self.token.type == Lexer.SEMICOLON:
            n.op1 = self.terms
            return n
        else:
            msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
            self.error(msg)

    def expr(self):
        return self.term()

    #
    # def expr(self):
    #     if self.token.type == Lexer.NUM:
    #         value, mtype = self.token.value
    #         tok_val = None
    #         if mtype == "int":
    #             tok_val = int(value)
    #         elif mtype == 'float':
    #             tok_val = int(float(value))
    #         elif mtype == 'hex':
    #             tok_val = int(value, 16)
    #         n = Node(Parser.CONST, tok_val)
    #         self.next_token()
    #         return n
    #     if self.token.type == Lexer.NOT:
    #         self.next_token()
    #         n = Node(Parser.UNOP, op1=self.expr())
    #         return n
    #     elif self.token.type == Lexer.ID:
    #         n = Node(Parser.VAR, self.token.type)
    #         self.next_token()
    #         return n
    #     else:
    #         msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
    #         self.error(msg)

    def statement(self):
        if self.token.type == Lexer.RETURN:
            n = Node(Parser.RET)
            self.next_token()
            n.op1 = self.expr()
            if n.op1.kind == Parser.VAR:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg + " digit value expected")
            elif self.token.type == Lexer.PROD:
                self.next_token()
                tmp = self.expr()
                if tmp.kind != Parser.UNOP and tmp.kind != Parser.CONST:
                    msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                    self.error(msg)
                else:
                    n.op2 = tmp
            if self.token.type != Lexer.SEMICOLON:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg + " semicolon expected")
            self.next_token()
            if 'return' not in self.stmts.keys():
                self.stmts['return'] = n
            else:
                n = self.stmts['return']
            return n
        else:
            msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
            self.error(msg)

    def function(self):
        if self.token.type == Lexer.INT:
            self.next_token()
            if self.token.type == Lexer.ID:
                name = self.token.value
                if name in self.names:
                    msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                    self.error(msg + " bad identifier")
                self.names.add(name)
                self.next_token()
                if self.token.type == Lexer.LPAR:
                    self.next_token()
                    if self.token.type == Lexer.RPAR:
                        self.next_token()
                        if self.token.type == Lexer.LBRA:
                            self.next_token()
                            n = Node(Parser.FUNC, name=name)
                            self.stmts.clear()
                            while True:
                                n.op1 = self.statement()
                                if self.token.type == Lexer.RBRA:
                                    self.next_token()
                                    break
                                else:
                                    continue
                            self.arrs.append(n)  # make list of Functions

                            if self.token.type == Lexer.EOF and "main" not in self.names:
                                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                                self.error(msg + " no main function")
                            elif self.token.type != Lexer.EOF:
                                self.function()
                            return self.arrs

    def parse(self):
        self.next_token()
        node = Node(Parser.PROG, op1=self.function())
        if self.token.type != Lexer.EOF:
            msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
            self.error(msg)
        return node


class Compile:
    def __init__(self):
        print("\n")
        self.program = []
        self.flag = False
        self.name = None
        self.registers = ['eax']

    HEAD = ['.386\n', '.model flat,stdcall\n', 'option casemap:none\n', 'include     D:\masm32\include\windows.inc\n',
            'include     D:\masm32\include\kernel32.inc\n', 'include     D:\masm32\include\masm32.inc\n',
            'includelib    D:\masm32\lib\kernel32.lib\n', 'includelib    D:\masm32\lib\masm32.lib\n',
            'NumbToStr    PROTO: DWORD,:DWORD\n']

    DATA = ['.data\n', 'buff        db 11 dup(?)\n']

    CODE = ['.code\n', 'main:\n']

    CALLS = ['invoke  NumbToStr, ebx, ADDR buff\n', 'invoke  StdOut,eax\n', 'invoke  ExitProcess, 0\n']

    END = ['''NumbToStr PROC uses ebx x:DWORD, buffer:DWORD
    mov     ecx, buffer
    mov     eax, x
    mov     ebx, 10
    add     ecx, ebx
@@:
    xor     edx, edx
    div     ebx
    add     edx, 48              	
    mov     BYTE PTR [ecx],dl   	
    dec     ecx                 	
    test    eax, eax
    jnz     @b
    inc     ecx
    mov     eax, ecx
    ret
NumbToStr ENDP
END main''']

    def iter_compile(self, lst):
        for i in lst:
            self.compile(i)

    def compile(self, node):
        if node.kind == Parser.PROG:
            if isinstance(node.op1, Iterable):
                self.iter_compile(node.op1)
            else:
                self.compile(node.op1)

        elif node.kind == Parser.FUNC:
            self.name = node.name
            if self.name == "main":
                self.compile(node.op1)
            else:
                self.name = 'my_' + self.name
                self.HEAD.append(self.name + '\t')
                self.HEAD.append("PROTO\n")
                self.CALLS.append(self.name + ' proc\n')
                self.compile(node.op1)
                self.CALLS.append(self.name + ' endp\n')

        if node.kind == Parser.TERM:
            self.CODE.append('mov eax, ')
            self.compile(node.op1[0])
        elif node.kind == Parser.BINOP:
            ln = len(node.op1)
            self.CODE.append('mov eax, ')
            self.registers[0] = "eax"
            self.compile(node.op1[ln - 1])
            self.registers[0] = "ecx"
            ln -= 1
            while ln > 0:
                self.CODE.append('mov ecx, ')
                self.compile(node.op1[ln - 1])
                self.CODE.append('mul ecx\n')
                ln -= 1

        elif node.kind == Parser.UNOP:
            self.CODE.append(str(node.value) + '\n')
            self.CODE.append("cmp " + self.registers[0] + ", 0\n sete " + self.registers[0][1] + "l\n")

        if node.kind == Parser.CONST:
            if self.name != 'main':
                self.CALLS.append(str(node.value) + '\n')
            else:
                self.CODE.append(str(node.value) + '\n')

        if node.kind == Parser.EXPR:
            self.compile(node.op1)

        if node.kind == Parser.RET:
            if self.name == "main":
                self.CODE.append("xor eax, eax\n xor ebx, ebx\n xor ecx, ecx\n")
                self.compile(node.op1)
                self.CODE.append("mov ebx, eax\n")
            else:
                self.CALLS.append('    mov ebx, ')
                self.compile(node.op1)
                self.CALLS.append("    ret\n")

    def printer(self):
        f = open('2-27-Python-IV-82-Shkardybarda', 'w')
        self.CODE.extend(self.CALLS)
        self.program += self.HEAD
        self.program += self.DATA
        self.program += self.CODE
        self.program += self.END
        for i in self.program:
            f.write(i)
        f.close()

    def rest(self):
        return self.program


a = Lexer('2-27-Python-IV-82-Shkardybarda.txt')
a = a.next_token()
p = Parser(a)
ast = p.parse()
com = Compile()
com.compile(ast)
com.printer()
# print(a)

# print(ast.op1[0].op1.op1.kind)
# print(ast)
