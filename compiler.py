import sys
import inspect
from collections import namedtuple
from collections.abc import Iterable


#   DECLARATION -- CALLER SHOULD GEN TEXT TOKEN!!!!

def debug(token):
    print(token)
    lxr = ('NUM', 'ID', 'INT', 'FLOAT', 'LBRA', 'RBRA', 'RETURN', 'LPAR', 'RPAR', 'SEMICOLON', 'NOT', 'PROD', 'EOF')
    print("tok type = " + lxr[token.type])


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

    NUM, ID, INT, FLOAT, LBRA, RBRA, RETURN, LPAR, RPAR, SEMICOLON, NOT, PROD, EQUAL, XOR, DIV, EOF = range(16)
    SYMBOLS = {'{': LBRA, '}': RBRA, '(': LPAR, ')': RPAR, ';': SEMICOLON, '!': NOT, '*': PROD, '=': EQUAL, "^": XOR,
               "/": DIV}
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
        self.Token = namedtuple("Token", 'valid, type, row, symbol, value',
                                defaults=(None,))

    def next_token(self):
        if self.tokens:
            self.token = self.tokens.pop(0)
            if self.token.valid is False:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg + " invalid value")
        else:
            self.token = None

    VAR, CONST, RET, EXPR, FUNC, UNOP, BINOP, BIN_PROD, BIN_DIV, BIN_XOR, FACTOR, TERM, DECL, STMT, ID, PROG = range(16)
    names = set()
    arrs = []
    terms = []
    stmts = {}
    var_map = set()

    @staticmethod
    def error(msg):
        print('Parser error:', msg)
        sys.exit(1)

    def factor(self):
        print("Enter factor", inspect.currentframe().f_back)
        if self.token.type == Lexer.LPAR:
            n = Node(Parser.EXPR)
            self.next_token()
            n.op1 = self.term()
            if self.token.type != Lexer.RPAR:
                debug(self.token)
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
            n.op1 = self.factor()
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
        elif self.token.type == Lexer.ID:
            # if self.token.value not in self.var_map:
            #     msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
            #     msg += "Undeclared variable"
            #     self.error(msg)
            return Node(Parser.ID, value=self.token.value)
        else:
            debug(self.token)
            msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
            self.error(msg)

    def term(self):
        # print(self.token)
        # print("Enter term", inspect.currentframe().f_back)
        elem = self.factor()
        # print("/////////", self.token)
        self.next_token()
        # print("**************")
        # print(self.token)
        if self.token.type == Lexer.PROD or self.token.type == Lexer.DIV or self.token.type == Lexer.XOR:
            op = self.token.type
            # current_op = [elem]
            current_op = []
            n = Node(Parser.BINOP)
            daughter = None
            if self.token.type == Lexer.PROD:
                daughter = Node(Parser.BIN_PROD, op1=[])
            elif self.token.type == Lexer.DIV:
                daughter = Node(Parser.BIN_DIV, op1=[])
            else:
                daughter = Node(Parser.BIN_XOR, op1=[])
            daughter.op1.append(elem)
            self.next_token()
            daughter.op1.append(self.factor())
            # current_op.append(self.factor())
            self.next_token()
            while True:
                if self.token.type == op:
                    self.next_token()
                    daughter.op1.append(self.factor())
                    self.next_token()
                    continue
                elif self.token.type == Lexer.PROD:
                    op = Lexer.PROD
                    daughter = Node(Parser.BIN_PROD, op1=[daughter])
                    self.next_token()
                    daughter.op1.append(self.factor())
                    self.next_token()
                    continue
                elif self.token.type == Lexer.DIV:
                    op = Lexer.DIV
                    daughter = Node(Parser.BIN_DIV, op1=[daughter])
                    self.next_token()
                    daughter.op1.append(self.factor())
                    self.next_token()
                    continue
                elif self.token.type == Lexer.XOR:
                    op = Lexer.XOR
                    daughter = Node(Parser.BIN_XOR, op1=[daughter])
                    self.next_token()
                    daughter.op1.append(self.factor())
                    self.next_token()
                    continue
                else:
                    break
            # self.terms.append(current_op)
            n.op1 = daughter
            # print(self.terms)
            return n
        # elif self.token.type == Lexer.DIV:
        #     daughter = Node(Lexer.DIV, op1=[])
        #     while True:

        return elem

    def expr(self):
        print("DEBUG: enter EXPRESSION")
        if self.token.type == Lexer.ID:
            remember = self.token
            self.next_token()
            if self.token.type == Lexer.EQUAL:
                self.next_token()
                return Node(Parser.EXPR, op1=self.expr())
            elif self.token.type == Lexer.SEMICOLON:
                return Node(Parser.ID, value=self.token.value)
            else:
                print("COMMING")
                self.tokens.insert(0, self.token)
                self.token = remember
                print(self.token)
                return self.term()
        else:
            return self.term()

    def statement(self):
        print("DEBUG: enter STATEMENT")
        # IT SEEMS TO BE BROKEN AS I SHOULD JUST CALL EXPRESSION AND PARSE RESULT! -> RETURN STATEMENT
        if self.token.type == Lexer.RETURN:
            n = Node(Parser.RET)
            self.next_token()
            n.op1 = self.expr()
            if self.token.type == Lexer.PROD:
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
            if 'return' not in self.stmts.keys():
                self.stmts['return'] = n
            else:
                n = self.stmts['return']
            return n
        elif self.token.type == Lexer.INT:
            self.next_token()
            if self.token.type == Lexer.ID:
                tok_id = self.factor()  # It should return Node with var name
                self.next_token()
                if self.token.type == Lexer.EQUAL:
                    self.next_token()
                    return Node(Parser.DECL, op1=tok_id, op2=self.expr())
                elif self.token.type == Lexer.SEMICOLON:
                    # if self.token.value not in self.var_map:
                    #     self.var_map.add(self.token.value)
                    # else:
                    #     msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                    #     msg += "Undeclared variable"
                    #     self.error(msg)
                    return Node(Parser.DECL, op1=tok_id)
                else:
                    msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                    self.error(msg)
        # elif self.token.type == Lexer.ID and self.token.value not in self.var_map:
        #     msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
        #     msg += "Undeclared variable"
        #     self.error(msg)
        else:
            return self.expr()

    def function(self):
        print("DEBUG: enter FUNCTION")
        if self.token.type == Lexer.INT:
            self.next_token()
            if self.token.type == Lexer.ID:
                name = self.token.value
                # if name in self.names:  # This means we have the same functions name
                #     msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                #     self.error(msg + " bad identifier")
                self.names.add(name)
                self.next_token()
                if self.token.type == Lexer.LPAR:
                    self.next_token()
                    if self.token.type == Lexer.RPAR:
                        self.next_token()
                        if self.token.type == Lexer.LBRA:
                            self.next_token()
                            statms = []  # We can have many stmst in our function
                            n = Node(Parser.FUNC, name=name)
                            self.stmts.clear()
                            while True:
                                elem = self.statement()
                                # statms.append((elem.kind, elem))    # Make list of statements --- idea of optimization is to ignore all after retuen statement
                                statms.append(elem)
                                self.next_token()
                                print("ALARM_____________", self.token)
                                if self.token.type == Lexer.RBRA:
                                    n.op1 = statms.copy()
                                    self.next_token()
                                    break
                                else:
                                    continue
                            self.arrs.append(n)  # make list of Functions
                            # todo i don't understand logic upper

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
        self.var_map = {}
        self.counter = 0

    HEAD = ['.386\n', '.model flat,stdcall\n', 'option casemap:none\n', 'include     D:\masm32\include\windows.inc\n',
            'include     D:\masm32\include\kernel32.inc\n', 'include     D:\masm32\include\masm32.inc\n',
            'includelib    D:\masm32\lib\kernel32.lib\n', 'includelib    D:\masm32\lib\masm32.lib\n',
            'NumbToStr    PROTO: DWORD,:DWORD\n']

    DATA = ['.data\n', 'buff        db 11 dup(?)\n']

    CODE = ['.code\n', 'main:\n', "\txor eax, eax\n\txor ebx, ebx\n\txor ecx, ecx\n"]

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
        def define(elem):
            if elem.kind == Parser.CONST:
                # self.compile(elem)
                return str(elem.value)
            else:
                self.compile(elem)
                return str('[ebp - {}]'.format(self.var_map[elem.value]))

        if node.kind == Parser.DECL:
            self.CODE.append("\tsub esp, 4\n")
            self.counter += 4
            self.compile(node.op1)
            if node.op2:
                self.compile(node.op2)
                self.CODE.append("\tpop eax\n")
                self.CODE.append("\tmov dword ptr [ebp - {}], eax\n".format(self.counter))
        elif node.kind == Parser.ID:
            self.var_map.update({node.value: self.counter})

        if node.kind == Parser.PROG:
            if isinstance(node.op1, Iterable):
                self.iter_compile(node.op1)
            else:
                self.compile(node.op1)

        elif node.kind == Parser.FUNC:
            self.name = node.name
            if self.name == "main":
                if isinstance(node.op1, Iterable):
                    self.iter_compile(node.op1)
                else:
                    self.compile(node.op1)

            else:
                self.name = 'my_' + self.name
                self.HEAD.append(self.name + '\t')
                self.HEAD.append("PROTO\n")
                self.CALLS.append(self.name + ' proc\n')
                self.compile(node.op1)
                self.CALLS.append(self.name + ' endp\n')

        if node.kind == Parser.TERM:
            self.CODE.append('\tmov eax, ')
            self.compile(node.op1[0])
        elif node.kind == Parser.BINOP:
            self.compile(node.op1)

        elif node.kind == Parser.BIN_PROD:
            if node.op1[0].kind not in [Parser.BIN_XOR, Parser.BIN_DIV]:
                self.CODE.append("\tmov eax, {}\n".format(define(node.op1[0])))
                for i in node.op1[1:]:
                    self.CODE.append('\tmov ecx, {}\n\tmul ecx\n'.format(define(i)))
                self.CODE.append('\tpush eax\n')
            else:
                self.compile(node.op1[0])
                self.CODE.append("\tpop eax\n")
                for i in node.op1[1:]:
                    self.CODE.append('\tmov ecx, {}\n'.format(define(i)))
                    self.CODE.append('\tmul ecx\n')

        elif node.kind == Parser.BIN_DIV:
            if node.op1[0].kind not in [Parser.BIN_XOR, Parser.BIN_PROD]:
                self.CODE.append("\tmov eax, {}\n".format(define(node.op1[0])))
                for i in node.op1[1:]:
                    self.CODE.append('\tmov ecx, {}\ndiv ecx\n\tcdq\n'.format(define(i)))
                self.CODE.append('\tpush eax\n')
            else:
                self.compile(node.op1[0])
                self.CODE.append("\tpop eax\n")
                for i in node.op1[1:]:
                    self.CODE.append('\tmov ecx, {}\n'.format(define(i)))
                    self.CODE.append('\tdiv ecx\n\tcdq\n')
                self.CODE.append("\tpush eax\n")

        elif node.kind == Parser.BIN_XOR:
            if node.op1[0].kind not in [Parser.BIN_PROD, Parser.BIN_DIV]:
                self.CODE.append("\tmov eax, {}\n".format(define(node.op1[0])))
                for i in node.op1[1:]:
                    self.CODE.append('\tmov ecx, {}\nxor eax, ecx\n'.format(define(i)))
                self.CODE.append('\tpush eax\n')
            else:
                self.compile(node.op1[0])
                self.CODE.append("\tpop eax\n")
                for i in node.op1[1:]:
                    self.CODE.append('\tmov ecx, {}\n'.format(define(i)))
                    self.CODE.append('\txor eax, ecx\n')
                self.CODE.append('\tpush eax\n')
        elif node.kind == Parser.UNOP:
            self.CODE.append(str(node.value) + '\n')
            self.CODE.append("\tcmp " + self.registers[0] + ", 0\n sete " + self.registers[0][1] + "l\n")

        if node.kind == Parser.CONST:
            if self.name != 'main':
                self.CODE.append('\tpush {}\n'.format(node.value))
            else:
                self.CODE.append('\tpush {}\n'.format(node.value))

        if node.kind == Parser.EXPR:
            self.compile(node.op1)

        if node.kind == Parser.RET:
            if self.name == "main":
                self.compile(node.op1)
                self.CODE.append("\tmov ebx, eax\n")
            else:
                self.CALLS.append('\tmov ebx, ')
                self.compile(node.op1)
                self.CALLS.append("\tret\n")

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

# a = Lexer('lab1.c')
# a = a.next_token()
# p = Parser(a)
# ast = p.parse()
#
# com = Compile()
# com.compile(ast)
# com.printer()

# TODO
#   1) Continue working with code generator it is nearly good but still far (xor don't work and other
#   operations should be checked)
#   2) Parser is really good but it should have other level for XOR operation
#   3) In code generator variable map isn't used it should be fixed
#   4) XOR has lover priority then PRODUCT
#   5) 22 isn't work
