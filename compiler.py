import sys
import inspect
from collections import namedtuple
from collections.abc import Iterable


#   DECLARATION -- CALLER SHOULD GEN TEXT TOKEN!!!!
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

    NUM, ID, INT, FLOAT, LBRA, RBRA, RETURN, LPAR, RPAR, SEMICOLON, NOT, PROD, EQUAL, XOR, DIV, EOF, QUESTION, COLON = range(
        18)
    SYMBOLS = {'{': LBRA, '}': RBRA, '(': LPAR, ')': RPAR, ';': SEMICOLON, '!': NOT, '*': PROD, '=': EQUAL, "^": XOR,
               "/": DIV, "?": QUESTION, ":": COLON}
    WORDS = {'int': INT, 'return': RETURN, 'float': FLOAT}

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
                    self.symbol = 0
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
                ident = str()
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
    def __init__(self, kind, value=None, ttype=None, op1=None, op2=None, op3=None, err=None):
        self.kind = kind
        self.value = value
        self.op1 = op1
        self.op2 = op2
        self.op3 = op3
        self.ttype = ttype
        self.err = err


class Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.token = None

    def next_token(self):
        if self.tokens:
            self.token = self.tokens.pop(0)
            if self.token.valid is False:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg)
        else:
            msg = "there are no tokens -> list is empty"
            self.error(msg)

    VAR, CONST, RET, EXPR, FUNC, UNOP, BINOP, BIN_PROD, BIN_DIV, BIN_XOR, FACTOR, TERM, DECL, STMT, ID, TERNARY, PROG = range(17)
    names = set()
    arrs = []
    terms = []
    stmts = {}
    var_map = set()

    @staticmethod
    def error(msg):
        print('Error:', msg)
        sys.exit(1)

    def factor(self):
        if self.token.type == Lexer.LPAR:
            # TODO: DO I REALLY NEED TO CREATE SEPARATE NODE EXPR?
            n = Node(Parser.EXPR)
            self.next_token()
            n.op1 = self.expr()
            self.next_token()
            if self.token.type != Lexer.RPAR:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg)
            return n
        elif self.token.type == Lexer.NOT:
            n = Node(Parser.UNOP)
            k = 1
            while True:
                if self.tokens[0].type == Lexer.NOT:
                    self.next_token()
                    k += 1
                    continue
                else:
                    break
            if k % 2 == 0:
                n.op1 = self.factor()
                return n
            self.next_token()
            n.op1 = self.factor()
            return n
        elif self.token.type == Lexer.NUM:
            value, mtype = self.token.value
            tok_val = None
            if mtype == "int":
                tok_val = int(value)
                mtype = Lexer.INT
            elif mtype == 'float':
                tok_val = int(float(value))
                print("Successful adduction {} to int".format(value.decode()))
                mtype = Lexer.FLOAT
            elif mtype == 'hex':
                print("Successful adduction {} to int".format(value.decode()))
                tok_val = int(value, 16)
                mtype = Lexer.INT
            n = Node(Parser.CONST, value=tok_val, ttype=mtype, err=(self.token.row, self.token.symbol))
            return n
        elif self.token.type == Lexer.ID:
            return Node(Parser.ID, value=self.token.value, err=(self.token.row, self.token.symbol))
        else:
            msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
            self.error(msg)

    def term(self):
        elem = self.factor()
        if self.tokens[0].type in (Lexer.PROD, Lexer.DIV):
            self.next_token()
            op = self.token.type
            daughter = None
            if self.token.type == Lexer.PROD:
                daughter = Node(Parser.BIN_PROD, op1=[])
            elif self.token.type == Lexer.DIV:
                daughter = Node(Parser.BIN_DIV, op1=[], err=(self.token.row, self.token.symbol))
            daughter.op1.append(elem)
            self.next_token()
            daughter.op1.append(self.factor())
            while True:
                if self.tokens[0].type == op:
                    self.next_token()
                    self.next_token()
                    daughter.op1.append(self.factor())
                    continue
                elif self.tokens[0].type == Lexer.PROD:
                    op = Lexer.PROD
                    daughter = Node(Parser.BIN_PROD, op1=[daughter])
                    self.next_token()
                    self.next_token()
                    daughter.op1.append(self.factor())
                    continue
                elif self.tokens[0].type == Lexer.DIV:
                    op = Lexer.DIV
                    daughter = Node(Parser.BIN_DIV, op1=[daughter])
                    self.next_token()
                    daughter.err = (self.token.row, self.token.symbol)
                    self.next_token()
                    daughter.op1.append(self.factor())
                    continue
                else:
                    break
            return daughter
        return elem

    def bit_op(self):
        elem = self.term()
        if self.tokens[0].type == Lexer.XOR:
            self.next_token()
            n = Node(Parser.BIN_XOR, op1=[elem])
            self.next_token()
            n.op1.append(self.term())
            while True:
                if self.tokens[0].type == Lexer.XOR:
                    self.next_token()
                    self.next_token()
                    n.op1.append(self.term())
                else:
                    break
            return n
        return elem

    def cond_expr(self):
        e1 = self.bit_op()
        if self.tokens[0].type == Lexer.QUESTION:
            self.next_token()
            self.next_token()
            e2 = self.expr()
            self.next_token()
            self.next_token()
            # sys.exit(self.token)
            e3 = self.cond_expr()
            # if self.tokens[0].type != Lexer.SEMICOLON:
            #     self.next_token()
            # self.next_token()
            # if self.token.type != Lexer.SEMICOLON:
            #     return self.error("COND_EXPR")
            # print("Create Ternary ", e1.kind, e2.kind, e3.kind)
            return Node(Parser.TERNARY, op1=e1, op2=e2, op3=e3)
        else:
            return e1

    def expr(self):
        if self.token.type == Lexer.ID:
            var = self.token.value
            err = (self.token.row, self.token.symbol)
            if self.tokens[0].type == Lexer.EQUAL:
                self.next_token()
                self.next_token()
                return Node(Parser.EXPR, op1=self.expr(), value=var, err=err)
            else:
                return self.cond_expr()
        else:
            return self.cond_expr()

    def statement(self):
        if self.token.type == Lexer.RETURN:
            n = Node(Parser.RET)
            self.next_token()
            n.op1 = self.expr()
            self.next_token()
            if self.token.type != Lexer.SEMICOLON:
                msg = "Raise error in 263 line\n"
                msg += "row: " + str(self.token.row - 1)
                self.error(msg + " semicolon expected")
            if 'return' not in self.stmts.keys():
                self.stmts['return'] = n
            else:
                n = self.stmts['return']
            return n
        elif self.token.type in (Lexer.INT, Lexer.FLOAT):
            ttype = self.token.type
            self.next_token()
            if self.token.type == Lexer.ID:
                tok_id = self.factor()  # It should return Node with var name
                self.next_token()
                if self.token.type == Lexer.EQUAL:
                    self.next_token()
                    n = Node(Parser.DECL, op1=tok_id, op2=self.expr(), ttype=ttype)
                    self.next_token()
                    if self.token.type != Lexer.SEMICOLON:
                        msg = "Raise error in 281 line\n"
                        msg += "row: " + str(self.token.row - 1)
                        self.error(msg + ' semicolon expected ')
                    else:
                        return n
                elif self.token.type == Lexer.SEMICOLON:
                    return Node(Parser.DECL, op1=tok_id, ttype=ttype)
                else:
                    msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                    self.error(msg)
            else:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg)
        else:
            n = self.expr()
            self.next_token()
            if self.token.type != Lexer.SEMICOLON:
                msg = "Raise error in 299 line\n"
                msg += "row: " + str(self.token.row - 1)
                self.error(msg + ' semicolon expected ')
            else:
                return n

    def function(self):
        if self.token.type == Lexer.INT:
            self.next_token()
            if self.token.type == Lexer.ID:
                name = self.token.value
                self.names.add(name)
                self.next_token()
                if self.token.type == Lexer.LPAR:
                    self.next_token()
                    if self.token.type == Lexer.RPAR:
                        self.next_token()
                        if self.token.type == Lexer.LBRA:
                            self.next_token()
                            statms = []  # We can have many stmst in our function
                            n = Node(Parser.FUNC, value=name)
                            self.stmts.clear()
                            while True:
                                elem = self.statement()
                                # statms.append((elem.kind, elem))    # Make list of statements --- idea of optimization is to ignore all after retuen statement
                                statms.append(elem)
                                self.next_token()
                                if self.token.type == Lexer.RBRA:
                                    n.op1 = statms.copy()
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
        self.name = None
        self.var_map = {}
        self.counter = 0
        self.ttype = None
        self.current_var = None

    HEAD = ['.386\n', '.model flat,stdcall\n', 'option casemap:none\n', 'include     D:\masm32\include\windows.inc\n',
            'include     D:\masm32\include\kernel32.inc\n', 'include     D:\masm32\include\masm32.inc\n',
            'includelib    D:\masm32\lib\kernel32.lib\n', 'includelib    D:\masm32\lib\masm32.lib\n',
            'NumbToStr    PROTO: DWORD,:DWORD\n']

    DATA = ['.data\n', 'zero_div_msg db \'zero division\', 0\n', 'buff        db 11 dup(?)\n']

    CODE = ['.code\n', 'main:\n', "\txor eax, eax\n\txor ebx, ebx\n\txor ecx, ecx\n\tpush ebp\n\tmov ebp, esp\n"]

    CALLS = ['\tmov esp, ebp\n\tpop ebp\ninvoke  NumbToStr, ebx, ADDR buff\n', 'invoke  StdOut,eax\n',
             'invoke  ExitProcess, 0\n', '\nerror:\n\tinvoke StdOut, addr zero_div_msg\n\tinvoke ExitProcess, 1\n\n']

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
                if self.ttype not in (Lexer.FLOAT, None) and elem.ttype == Lexer.FLOAT:
                    print("cant assign int var {} to float".format(self.current_var))
                    print('Error: row {}, symbol {}'.format(self.var_map[self.current_var][2][0],
                                                            self.var_map[self.current_var][2][1]))
                    sys.exit(1)
                return str(elem.value)
            else:
                if elem.value not in self.var_map.keys():
                    print('Use var {} before assignment'.format(elem.value))
                    print('Error: row {}, symbol {}'.format(elem.err[0], elem.err[1]))
                    sys.exit(1)
                if self.ttype not in (Lexer.FLOAT, None) and self.var_map[elem.value][1] == Lexer.FLOAT:
                    print("cant assign int var {} to float".format(self.current_var))
                    print('Error: row {}, symbol {}'.format(elem.err[0], elem.err[1]))
                    sys.exit(1)
                return str('[ebp - {}]'.format(self.var_map[elem.value][0]))

        if node.kind == Parser.PROG:
            if isinstance(node.op1, Iterable):
                self.iter_compile(node.op1)
            else:
                self.compile(node.op1)

        elif node.kind == Parser.FUNC:
            self.name = node.value
            if self.name == "main":
                ret = False
                for i in node.op1:
                    if i.kind == Parser.RET:
                        ret = True
                        break
                if not ret:
                    self.CALLS = self.CALLS[2:]
                self.iter_compile(node.op1)
            else:
                self.name = 'my_' + self.name
                self.HEAD.append(self.name + '\t')
                self.HEAD.append("proto\n")
                self.CALLS.append(self.name + ' proc\n')
                self.compile(node.op1)
                self.CALLS.append(self.name + ' endp\n')

        elif node.kind == Parser.EXPR:
            if node.value:
                if node.value not in self.var_map.keys():
                    print("Use var {} before assignment".format(node.value))
                    print('Error: row {}, symbol {}'.format(node.err[0], node.err[1]))
                    sys.exit(1)
                self.ttype = self.var_map[node.value][1]
                self.current_var = node.value
                self.compile(node.op1)
                self.CODE.append('\tpop eax\n\tmov dword ptr [ebp - {}], eax\n'.format(self.var_map[node.value][0]))
                self.ttype = None
                self.current_var = None
            else:
                self.compile(node.op1)

        elif node.kind == Parser.DECL:
            self.CODE.append("\tsub esp, 4\n")
            self.counter += 4
            node.op1.ttype = node.ttype
            self.current_var = node.op1.value
            self.compile(node.op1)  # Add var into var_map
            if node.op2:

                if node.op2.kind == Parser.ID:
                    # sys.exit(str(node.op2.kind))
                    self.ttype = node.ttype
                    self.CODE.append('\tmov eax, {}'.format(define(node.op2)))
                    self.CODE.append("\tmov dword ptr [ebp - {}], eax\n".format(self.counter))
                else:
                    self.ttype = node.ttype
                    self.compile(node.op2)
                    self.ttype = None
                    self.current_var = None
                    self.CODE.append("\tpop eax\n")
                    self.CODE.append("\tmov dword ptr [ebp - {}], eax\n".format(self.counter))
            else:
                self.CODE.append("\tmov dword ptr [ebp - {}], 0\n".format(self.counter))

        elif node.kind == Parser.RET:
            if self.name == "main":
                if node.op1.kind not in (Parser.CONST, Parser.ID):
                    self.compile(node.op1)
                    self.CODE.append('\tpop ebx\n')
                else:
                    self.CODE.append("\tmov ebx, {}\n".format(define(node.op1)))
            else:
                self.CALLS.append('\tmov ebx, ')
                self.compile(node.op1)
                self.CALLS.append("\tret\n")

        elif node.kind == Parser.BIN_PROD:
            def multiple():
                self.CODE.append('\tpop ecx\n\tpop eax\n\tmul ecx\n\tpush eax\n')

            k = 0
            for i in node.op1:
                if i.kind in (Parser.CONST, Parser.ID):
                    self.CODE.append('\tmov eax, {}\n\tpush eax\n'.format(define(i)))
                    k += 1
                else:
                    self.compile(i)
                    k += 1
                if k >= 2:
                    multiple()

        elif node.kind == Parser.BIN_DIV:
            def multiple():
                self.CODE.append('\tpop ecx\n\tcmp ecx, 0\n\tje error\n\tpop eax\n\tcdq\n\tidiv ecx\n\tpush eax\n')

            err = node.err
            k = 0
            for i in node.op1:
                if i.kind in (Parser.CONST, Parser.ID):
                    if self.ttype not in (Lexer.FLOAT, None):
                        print("var {} was declared as int but DIV was called".format(self.current_var))
                        print('Error: row {}, symbol {}'.format(err[0], err[1]))
                        sys.exit(1)
                    self.CODE.append('\tmov eax, {}\n\tpush eax\n'.format(define(i)))
                    k += 1
                else:
                    self.compile(i)
                    k += 1
                if k >= 2:
                    multiple()

        elif node.kind == Parser.BIN_XOR:
            def multiple():
                self.CODE.append('\tpop ecx\n\tpop eax\n\txor eax, ecx\n\tpush eax\n')

            k = 0
            for i in node.op1:
                if i.kind in (Parser.CONST, Parser.ID):
                    self.CODE.append('\tmov eax, {}\n\tpush eax\n'.format(define(i)))
                    k += 1
                else:
                    self.compile(i)
                    k += 1
                if k >= 2:
                    multiple()
        elif node.kind == Parser.UNOP:
            if node.op1.kind not in (Parser.CONST, Parser.ID):
                self.compile(node.op1)
                self.CODE.append('\tpop eax\n')
                self.CODE.append("\tcmp eax, 0\n\tsete al\n")
            else:
                self.CODE.append('\tmov eax, {}\n'.format(define(node.op1)))
                self.CODE.append("\tcmp eax, 0\n\tsete al\n")
            self.CODE.append('\tpush eax\n')

        elif node.kind == Parser.CONST:
            if node.ttype == Lexer.FLOAT and self.ttype != Lexer.FLOAT:
                print("cant assign int var {} to float".format(self.current_var))
                print('Error: row {}, symbol {}'.format(node.err[0], node.err[1]))
                sys.exit(1)
            self.CODE.append('\tpush {}\n'.format(node.value))

        elif node.kind == Parser.ID:
            # THIS SHOULD BE CALLED JUST FOR DECLARATION!!!
            if node.value not in self.var_map.keys():
                self.var_map.update({node.value: (self.counter, node.ttype, node.err)})
            else:
                print("repeatable assign of {}".format(node.value))
                print('Error: row {}, symbol {}'.format(node.err[0], node.err[1]))
                sys.exit(1)

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

# TODO
#   1) make function for (xor, div, prod) -> same code coping   --------------------------------------------SKIPP IT
#   2) maybe make more comfortable error messages (use norm errors in code gen)
#   3) If there are more then one return statement  --------------------------------------------------------HOTFIX
#   4) make real tests cause if some hotfixes is needed it should be tested fast.
#   5) Make norm compiler py -> use if sys.argv == 'main' -> run and it is no need in generator test only if we nedd Outup > /dev/null
