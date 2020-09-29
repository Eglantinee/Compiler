import sys
from collections import namedtuple
from collections.abc import Iterable


class Lexer:
    def __init__(self, file):
        self.file = open(file, 'rb')
        self.value = None
        self.sym = None
        self.row = 0
        self.st = self.file.read(1)  # First symbol from file
        self.tokens = []
        self.Token = namedtuple("Token", 'valid, type, row, symbol, value',
                                defaults=(self.row, self.file.read(), self.value))

    @staticmethod
    def debug(msg):
        print("DEBUG: Create node" + msg)

    NUM, ID, INT, FLOAT, LBRA, RBRA, RETURN, LPAR, RPAR, SEMICOLON, EOF = range(11)
    SYMBOLS = {'{': LBRA, '}': RBRA, '(': LPAR, ')': RPAR, ';': SEMICOLON}
    WORDS = {'int': INT, 'return': RETURN}

    def get(self):
        self.st = self.file.read(1)
        self.file.seek(self.file.tell())

    def next_token(self):
        self.sym = None
        self.value = None
        while self.sym is None:
            if len(self.st) == 0:
                self.tokens.append(self.Token(True, Lexer.EOF))
            elif self.st.decode().isspace():
                if self.st.decode() == '\n':
                    self.row += 1
                self.get()
            elif self.st.decode() in Lexer.SYMBOLS:
                self.tokens.append(self.Token(True, Lexer.SYMBOLS[self.st.decode()]))
                # self.sym = Lexer.SYMBOLS[self.st.decode()]
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
                # if k == "int":
                #     self.value = int(tmp_str)
                # elif k == "float":
                #     self.value = float(tmp_str)
                # else:
                #     self.value = int(tmp_str, 16)
                self.tokens.append(self.Token(True, Lexer.NUM, value=tmp_str))
                # self.sym = Lexer.NUM
                # # ZAGLUSHKA
                # self.value = int(tmp_str, 16)
            elif self.st.decode().isalpha():
                ident = ''
                while self.st.isalnum() or self.st.decode() == "_":
                    ident = ident + self.st.decode()
                    self.get()

                if ident in Lexer.WORDS:
                    self.tokens.append(self.Token(True, Lexer.WORDS[ident]))
                    self.sym = 'exit'
                else:
                    self.tokens.append(self.Token(True, Lexer.ID, value=ident))
                    break
                    # self.sym = Lexer.ID
                    # self.value = ident
            else:
                self.tokens.append(self.Token(False, None))
                break
                # self.error('Unexpected symbol: ' + self.st.decode())
                None
    def printer(self):
        self.next_token()
        # self.next_token()
        print(self.tokens)

class Node:
    def __init__(self, kind, value=None, name=None, op1=None, op2=None, op3=None):
        self.kind = kind
        self.value = value
        self.op1 = op1
        self.op2 = op2
        self.op3 = op3
        self.name = name
        self.type = type


class Parser(Lexer):
    VAR, CONST, RET, SEQ, FUNC, PROG = range(6)
    names = set()
    arrs = []

    def error(self, msg):
        print('Parser error:', msg)
        sys.exit(1)

    def expr(self):
        if self.sym == Lexer.NUM:
            n = Node(Parser.CONST, self.value)
            self.debug("CONST")
            self.next_token()
            return n
        elif self.sym == Lexer.ID:
            n = Node(Parser.VAR, self.sym)  # value == name of ID
            self.next_token()
            self.debug("ID")
            return n
        else:

            self.error("unknown expr")

    def statement(self):
        print("ENTER STMT")
        if self.sym == Lexer.RETURN:
            n = Node(Parser.RET)
            self.next_token()
            n.op1 = self.expr()
            if self.sym != Lexer.SEMICOLON:
                sys.exit("RETURN ERROR")
            self.next_token()
            return n
        else:
            print(self.sym)
            self.error("unknown statement")

    def function(self):
        if self.sym == Lexer.INT:
            self.next_token()
            if self.sym == Lexer.ID:
                name = self.value
                if name in self.names:
                    self.error("bad identifier")
                self.names.add(name)
                self.next_token()
                if self.sym == Lexer.LPAR:
                    self.next_token()
                    if self.sym == Lexer.RPAR:
                        self.next_token()
                        if self.sym == Lexer.LBRA:
                            self.next_token()
                            self.debug("FUNC")
                            n = Node(Parser.FUNC, name=name)
                            while True:
                                print("CALL", self.sym)
                                n.op1 = self.statement()
                                if self.sym == Lexer.RBRA:
                                    self.next_token()
                                    break
                                else:
                                    self.next_token()
                                    continue
                            self.arrs.append(n)  # make list of Functions

                            if self.sym == Lexer.EOF and "main" not in self.names:
                                sys.exit("main is apsent")
                            elif self.sym != Lexer.EOF:
                                self.function()
                            return self.arrs
        else:
            self.error("invalid syntax")

    def parse(self):
        self.next_token()
        self.debug("PROG")
        node = Node(Parser.PROG, op1=self.function())
        if self.sym != Lexer.EOF:
            self.error("Invalid statement syntax")
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
            print("Compiler in PROG")
            if isinstance(node.op1, Iterable):
                self.iter_compile(node.op1)
            else:
                self.compile(node.op1)

        elif node.kind == Parser.FUNC:
            print("Compiler FUNC")
            self.name = node.name
            print("FUNC", self.name)
            if self.name == "main":
                self.compile(node.op1)
            else:
                self.HEAD.append(self.name + '\t')
                self.HEAD.append("PROTO\n")
                self.CALLS.append(self.name + ' proc\n')
                self.compile(node.op1)
                self.CALLS.append(self.name + ' endp\n')
            # self.CODE.extend(self.CALLS)

        if node.kind == Parser.CONST:
            print("Compiler in CONST")
            print(node.value)
            if self.name != 'main':
                self.CALLS.append(str(node.value) + '\n')
            else:
                self.CODE.append(str(node.value) + '\n')

        if node.kind == Parser.SEQ:
            print("Compiler in SEQ")
            print(node.op1.kind)
            self.compile(node.op1)

        if node.kind == Parser.RET:
            print("RET ", self.name)
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
        print(self.program)
        for i in self.program:
            f.write(i)
        f.close()

    def rest(self):
        return self.program


# p = Parser('lab1.c')
# ast = p.parse()
# com = Compile()
# com.compile(ast)
# com.printer()
# #
a = Lexer('lab1.c')
a.printer()
# while a.sym != Lexer.EOF:
#     print(a.sym)
#     a.next_token()

# while True:
#     print(ast.kind)
# for i in ast.op1:
#     print(i.kind)
# print(i for i in  ast.op1)

# TODO bug with comment
