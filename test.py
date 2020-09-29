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

    # @staticmethod
    # def debug(msg):
    #     print("DEBUG: Create node" + msg)

    NUM, ID, INT, FLOAT, LBRA, RBRA, RETURN, LPAR, RPAR, SEMICOLON, EOF = range(11)
    SYMBOLS = {'{': LBRA, '}': RBRA, '(': LPAR, ')': RPAR, ';': SEMICOLON}
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
                if k == 'int' and tmp_str.decode()[0] == '0':
                    self.tokens.append(self.Token(False, None, self.row, self.symbol - len(tmp_str)))
                else:
                    self.tokens.append(self.Token(True, Lexer.NUM, self.row, self.symbol - len(tmp_str), value=[tmp_str, k]))
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
    def __init__(self, kind, value=None, name=None, op1=None):
        self.kind = kind
        self.value = value
        self.op1 = op1
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

    VAR, CONST, RET, SEQ, FUNC, PROG = range(6)
    names = set()
    arrs = []
    stmts = {}

    @staticmethod
    def error(msg):
        print('Parser error:', msg)
        sys.exit(1)

    def expr(self):
        if self.token.type == Lexer.NUM:
            value, mtype = self.token.value
            tok_val = None
            if mtype == "int":
                tok_val = int(value)
            elif mtype == 'float':
                tok_val = int(float(value))
            elif mtype == 'hex':
                tok_val = int(value, 16)
            n = Node(Parser.CONST, tok_val)
            # self.debug("CONST")
            self.next_token()
            return n
        elif self.token.type == Lexer.ID:
            n = Node(Parser.VAR, self.token.type)
            self.next_token()
            # self.debug("ID")
            return n
        else:
            msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
            self.error(msg)

    def statement(self):
        if self.token.type == Lexer.RETURN:
            n = Node(Parser.RET)
            self.next_token()
            n.op1 = self.expr()
            if n.op1.kind == Parser.VAR:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg + " digit value expected")
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
            print(self.token)
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
        self.program = []
        self.flag = False
        self.name = None

    HEAD = ['.386\n', '.model flat,stdcall\n', 'option casemap:none\n', 'include     E:\masm32\include\windows.inc\n',
            'include     E:\masm32\include\kernel32.inc\n', 'include     E:\masm32\include\masm32.inc\n',
            'includelib    E:\masm32\lib\kernel32.lib\n', 'includelib    E:\masm32\lib\masm32.lib\n',
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

        if node.kind == Parser.CONST:
            if self.name != 'main':
                self.CALLS.append(str(node.value) + '\n')
            else:
                self.CODE.append(str(node.value) + '\n')

        if node.kind == Parser.SEQ:
            self.compile(node.op1)

        if node.kind == Parser.RET:
            if self.name == "main":
                self.CODE.append("    mov ebx, ")
                self.compile(node.op1)
            else:
                self.CALLS.append('    mov ebx, ')
                self.compile(node.op1)
                self.CALLS.append("    ret\n")

    def printer(self):
        f = open('output.asm', 'w')
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


a = Lexer('lab1.c')
a = a.next_token()
p = Parser(a)
ast = p.parse()
com = Compile()
com.compile(ast)
com.printer()