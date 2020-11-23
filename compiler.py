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

    NUM, ID, INT, FLOAT, LBRA, RBRA, RETURN, LPAR, RPAR, SEMICOLON, NOT, PROD, EQUAL, XOR, DIV, EOF, QUESTION, COLON, \
    COMMA = range(19)
    SYMBOLS = {'{': LBRA, '}': RBRA, '(': LPAR, ')': RPAR, ';': SEMICOLON, '!': NOT, '*': PROD, '=': EQUAL, "^": XOR,
               "/": DIV, "?": QUESTION, ":": COLON, ",": COMMA}
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
    def __init__(self, kind, value=None, ttype=None, op1=None, op2=None, op3=None, err=None, args=None):
        self.kind = kind
        self.value = value
        self.op1 = op1
        self.op2 = op2
        self.op3 = op3
        self.ttype = ttype
        self.err = err
        self.args = args


class Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.token = None
        self.blocks = []

    def next_token(self):
        if self.tokens:
            self.token = self.tokens.pop(0)
            if self.token.valid is False:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                self.error(msg)
        else:
            msg = "there are no tokens -> list is empty"
            self.error(msg)

    VAR, CONST, RET, EXPR, FUNC, UNOP, BINOP, BIN_PROD, BIN_DIV, BIN_XOR, FACTOR, TERM, DECL, STMT, ID, TERNARY, \
    BLOCK, ANNOUNCEMENT, CALL, EXOR, PROG = range(21)
    names = set()
    arrs = []
    terms = []
    stmts = {}
    var_map = set()

    @staticmethod
    def error(msg):
        print('Error:', msg)
        sys.exit(1)

    def function_call(self):
        if self.token.type == Lexer.ID:
            name = self.token.value
            if self.tokens[0].type == Lexer.LPAR:
                n = Node(Parser.CALL)
                params = []
                self.next_token()
                self.next_token()
                while True:
                    if self.token.type == Lexer.RPAR:
                        break
                    else:
                        elem = self.expr()
                        params.append(elem)
                        self.next_token()
                        if self.token.type == Lexer.COMMA:
                            if self.tokens[0].type == Lexer.RPAR:
                                sys.exit("138")
                            else:
                                self.next_token()
                                continue
                n.args = params
                n.value = name
                return n
            else:
                return None
        else:
            return None

    def factor(self):
        call = self.function_call()
        if call is not None:
            return call
        elif self.token.type == Lexer.LPAR:
            # TODO: DO I REALLY NEED TO CREATE SEPARATE NODE EXPR? Now i just mute it for a check -- seems to be good\
            #  decision
            # n = Node(Parser.EXPR)
            self.next_token()
            # n.op1 = self.expr()
            n = self.expr()
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

    def xor(self):
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
        e1 = self.xor()
        if self.tokens[0].type == Lexer.QUESTION:
            self.next_token()
            self.next_token()
            e2 = self.expr()
            self.next_token()
            if self.token.type != Lexer.COLON:
                msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                msg += "\ncolumn (:) expected"
                self.error(msg)
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
            # var = self.token.value
            # var = self.cond_expr()  # should return id node
            # todo it is really broken -- if we run self.cond_epr it wont work but I would like it to be done
            var = Node(Parser.ID, value=self.token.value)
            err = (self.token.row, self.token.symbol)
            if self.tokens[0].type == Lexer.EQUAL:
                self.next_token()
                self.next_token()
                return Node(Parser.EXPR, op2=self.expr(), op1=var, err=err)
            elif self.tokens[0].type == Lexer.XOR:
                self.next_token()
                self.next_token()
                if self.token.type == Lexer.EQUAL:
                    self.next_token()
                    return Node(Parser.EXOR, op1=self.expr(), value=var, err=err)
                else:
                    sys.exit("279")
            else:
                return self.cond_expr()
        else:
            return self.cond_expr()

    def declaration(self):
        if self.token.type in (Lexer.INT, Lexer.FLOAT):
            ttype = self.token.type
            self.next_token()
            if self.token.type == Lexer.ID:
                # tok_id = self.factor()  # It should return Node with var name ---------- IT IS BROKEN
                tok_id = Node(Parser.ID, value=self.token.value)
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
            return n
        elif self.token.type == Lexer.LBRA:
            self.next_token()
            lst_of_elem = []
            while True:
                if self.token.type == Lexer.RBRA:
                    break
                elem = self.block_item()
                lst_of_elem.append(elem)
                self.next_token()
            if lst_of_elem:
                n = Node(Parser.BLOCK)
                n.op1 = lst_of_elem
                return n
            else:
                return
        else:
            n = self.expr()
            self.next_token()
            if self.token.type != Lexer.SEMICOLON:
                msg = "Raise error in 366 line\n"
                msg += "row: " + str(self.token.row - 1)
                self.error(msg + ' semicolon expected ')
            else:
                return n

    def block_item(self):
        # todo it is simple fix but it is not the best variant cuz in declaration is the same code
        if self.token.type in (Lexer.FLOAT, Lexer.INT):
            return self.declaration()
        else:
            return self.statement()

    def function(self):
        if self.token.type == Lexer.INT:
            self.next_token()
            if self.token.type == Lexer.ID:
                name = self.token.value
                self.names.add(name)
                self.next_token()
                if self.token.type == Lexer.LPAR:
                    self.next_token()
                    args = []
                    # todo it this eta i don't understand which format i should use to store info about arguments
                    while True:
                        if self.token.type in (Lexer.FLOAT, Lexer.INT):
                            ttype = self.token.type
                            self.next_token()
                            if self.token.type == Lexer.ID:
                                args.append((self.token.value, ttype))
                                self.next_token()
                                if self.token.type == Lexer.COMMA:
                                    if self.tokens[0].type not in (Lexer.FLOAT, Lexer.INT):
                                        sys.exit('368')
                                    else:
                                        self.next_token()
                                        continue
                                elif self.token.type != Lexer.RPAR:
                                    sys.exit('373')
                                else:
                                    continue
                            else:
                                sys.exit('371')
                        elif self.token.type == Lexer.RPAR:
                            self.next_token()
                            break
                        else:
                            sys.exit('376')
                    # if self.token.type == Lexer.RPAR:
                    #     self.next_token()
                    if self.token.type == Lexer.LBRA:
                        self.next_token()
                        blocks = []  # We can have many blocks in our function
                        n = Node(Parser.FUNC, value=name)
                        while True:
                            elem = self.block_item()
                            blocks.append(elem)
                            self.next_token()
                            if self.token.type == Lexer.RBRA:
                                n.op1 = blocks
                                n.value = name
                                n.args = args  # it is temporary fix
                                break
                            else:
                                continue
                        # # todo IDK what in this code does
                        # self.arrs.append(n)  # make list of Functions
                        # # if self.token.type == Lexer.EOF and "main" not in self.names:
                        # #     msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
                        # #     self.error(msg + " no main function")
                        # # elif self.token.type != Lexer.EOF:
                        # #     self.function()
                        # tmp = self.arrs[0]
                        # self.arrs.clear()
                        return n
                    elif self.token.type == Lexer.SEMICOLON:
                        n = Node(Parser.ANNOUNCEMENT, args=args, value=name)
                        return n
                    else:
                        return None

    def parse(self):
        node = Node(Parser.PROG)
        functions = []
        self.next_token()  # get first token
        while True:
            if self.token.type == Lexer.EOF:
                break
            elem = self.function()
            if elem:
                functions.append(elem)
            else:
                sys.exit("428")
            self.next_token()
        if self.token.type != Lexer.EOF:
            msg = "row: " + str(self.token.row) + " symbol: " + str(self.token.symbol)
            self.error(msg)
        node.op1 = functions
        return node


class Compile:
    def __init__(self):
        self.if_counter = 0
        self.nested = [False, 0]
        self.program = []
        self.name = None
        self.var_map = {}
        self.func_map = {}
        self.announcement = {}
        self.scope = []
        self.counter = 0
        self.ttype = None
        self.current_var = None  # we need it just to make correct errors! and it is all!

    HEAD = ['.386\n', '.model flat,stdcall\n', 'option casemap:none\n', 'include     D:\masm32\include\windows.inc\n',
            'include     D:\masm32\include\kernel32.inc\n', 'include     D:\masm32\include\masm32.inc\n',
            'includelib    D:\masm32\lib\kernel32.lib\n', 'includelib    D:\masm32\lib\masm32.lib\n',
            'NumbToStr    PROTO: DWORD,:DWORD\n']

    DATA = ['.data\n', 'zero_div_msg db \'zero division\', 0\n', 'buff        db 11 dup(?)\n']

    CODE = ['.code\n']  # , 'main:\n', "\txor eax, eax\n\txor ebx, ebx\n\txor ecx, ecx\n\tpush ebp\n\tmov ebp, esp\n"]

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
        def get_type(id):
            if id not in self.var_map.keys():
                if self.scope:
                    for i in self.scope[::-1]:
                        if id in i.keys():
                            var_type = i[id][1]
                            index = i[id][0]
                            return var_type
                else:
                    sys.exit("529")
            elif id in self.var_map:
                return self.var_map[id][1]
            else:
                sys.exit("533")

        def define(elem):
            # This function should be called just for CONST and ID
            if elem.kind == Parser.CONST:
                if self.ttype not in (Lexer.FLOAT, None) and elem.ttype == Lexer.FLOAT:
                    print("cant assign int var {} to float".format(self.current_var))
                    print('Error: row {}, symbol {}'.format(self.var_map[self.current_var][2][0],
                                                            self.var_map[self.current_var][2][1]))
                    sys.exit(1)
                return str(elem.value)
            else:
                var_type = None
                index = 0
                if elem.value not in self.var_map.keys():
                    if self.scope:
                        for i in self.scope[::-1]:
                            if elem.value in i.keys():
                                var_type = i[elem.value][1]
                                index = i[elem.value][0]
                                break
                                # return str('[ebp - {}]'.format(i[elem.value][0]))
                    if var_type is None:
                        print('Use var {} before assignment'.format(elem.value))
                        print('Error: row {}, symbol {}'.format(elem.err[0], elem.err[1]))
                        sys.exit(1)
                else:
                    var_type = self.var_map[elem.value][1]
                    index = self.var_map[elem.value][0]
                    # todo define if None is really neccessary
                if self.ttype not in (Lexer.FLOAT, None) and var_type == Lexer.FLOAT:
                    print("cant assign int var {} to float".format(self.current_var))
                    print('Error: row {}, symbol {}'.format(elem.err[0], elem.err[1]))
                    sys.exit(1)
                return str('[ebp - {}]'.format(index))

        if node.kind == Parser.PROG:
            if isinstance(node.op1, Iterable):
                self.iter_compile(node.op1)
            else:
                self.compile(node.op1)

        elif node.kind == Parser.FUNC:
            func_name = node.value
            self.var_map = {}
            self.counter = 0
            if func_name not in self.func_map.keys():
                if func_name in self.announcement.keys():
                    if len(node.args) != len(self.announcement[func_name]):
                        sys.exit("args don't equals")
                    elif node.args:
                        for i in range(len(node.args)):
                            if node.args[i][1] != self.announcement[func_name][i][1]:
                                sys.exit("bad types in announcement ")
                self.func_map.update({node.value: node.args})
                ########################################

                if func_name == 'main':
                    self.CODE.append('{}:\n'.format(func_name))
                    self.CODE.append('\txor eax, eax\n'
                                     '\txor ebx, ebx\n'
                                     '\txor ecx, ecx\n')
                    self.iter_compile(node.op1)
                else:
                    self.CODE.append('my_{}:\n'.format(func_name))
                    self.CODE.append('\tpush ebp\n'
                                     '\tmov ebp, esp\n')
                    self.iter_compile(node.op1)
                    self.CODE.append('\tmov ebp, esp\n'
                                     '\tpop ebp\n'
                                     '\tret\n')
            else:
                sys.exit("604")

        elif node.kind == Parser.ANNOUNCEMENT:
            if node.value not in self.announcement.keys():
                self.announcement.update({node.value: node.args})
            else:
                sys.exit("586")

        elif node.kind == Parser.CALL:
            func_name = node.value
            if func_name not in self.func_map.keys():
                if func_name not in self.announcement.keys():
                    sys.exit("call unknown function")
                else:
                    if len(node.args) != len(self.announcement[func_name]):
                        sys.exit("args don't equals")
                    elif node.args:
                        for i in range(len(node.args)):
                            if node.args[i][1] != self.announcement[func_name][i][1]:
                                sys.exit("bad types in announcement ")
            else:
                if len(node.args) != len(self.func_map[func_name]):
                    sys.exit("args don't equals")
                elif node.args:
                    for i in range(len(node.args)):
                        if node.args[i].kind == Parser.CONST:
                            t_type = node.args[i].ttype
                        elif node.args[i].kind == Parser.ID:
                            t_type = get_type(node.args[i].value)
                        else:
                            sys.exit("args should be const or var")
                        if t_type != self.func_map[func_name][i][1]:
                            sys.exit("bad types in call")
            ####################################
            num = len(node.args) * 4
            if node.args:
                for i in node.args[::-1]:
                    self.CODE.append("\tpush {}\n".format(define(i)))
            # if node.value == "main"    -------------------- just to think
            
            self.CODE.append('\tcall my_{}\n'.format(node.value))
            self.CODE.append('\tadd esp, {}\n'.format(num))

            # if self.name == "main":
            #     ret = False
            #     for i in node.op1:
            #         if i.kind == Parser.RET:
            #             ret = True
            #             break
            #     if not ret:
            #         self.CALLS = self.CALLS[2:]
            #     self.iter_compile(node.op1)
            # else:
            #     self.name = 'my_' + self.name
            #     self.HEAD.append(self.name + '\t')
            #     self.HEAD.append("proto\n")
            #     self.CALLS.append(self.name + ' proc\n')
            #     self.compile(node.op1)
            #     self.CALLS.append(self.name + ' endp\n')

        # elif node.kind == Parser.EXPR:
        #     index = None
        #     if node.value:
        #         if node.value not in self.var_map.keys():
        #             if self.scope:
        #                 print(self.scope, self.var_map)
        #                 for i in self.scope[-1:]:
        #                     print(i)
        #                     if node.value not in i.keys():
        #                         print("Use var {} before assignment".format(node.value))
        #                         print('Error: row {}, symbol {}'.format(node.err[0], node.err[1]))
        #                         sys.exit(1)
        #                     else:
        #                         self.ttype = i[node.value][1]
        #                         index = i[node.value][0]
        #                         break
        #             else:
        #                 print("Use var {} before assignment".format(node.value))
        #                 print('Error: row {}, symbol {}'.format(node.err[0], node.err[1]))
        #                 sys.exit(1)
        #         else:
        #             index = self.var_map[node.value][0]
        #             self.ttype = self.var_map[node.value][1]
        #         self.current_var = node.value
        #         self.compile(node.op1)
        #         self.CODE.append('\tpop eax\n\tmov dword ptr [ebp - {}], eax\n'.format(index))
        #         self.ttype = None
        #         self.current_var = None
        #     else:
        #         self.compile(node.op1)

        elif node.kind == Parser.EXPR:
            if node.op1.kind != Parser.ID:
                self.compile(node.op1)
            else:
                store_type = self.ttype
                self.current_var = node.op1.value
                self.ttype = get_type(node.op1.value)
                # todo define is really good but sometimes it is not best decision to use
                if node.op2.kind == Parser.ID:
                    self.CODE.append("\tmov eax, {}\n\tpush eax\n".format(define(node.op2)))
                else:
                    self.compile(node.op2)
                self.ttype = None
                self.current_var = None
                self.CODE.append('\tpop eax\n\tmov dword ptr {}, eax\n'.format(define(node.op1)))

        elif node.kind == Parser.DECL:
            self.CODE.append("\tsub esp, 4\n")
            self.counter += 4
            # node ttype is a TYPE of declaration but it should store in var_map -> Node.ID should have it
            node.op1.ttype = node.ttype
            self.current_var = node.op1.value
            self.compile(node.op1)  # Add var into var_map
            if node.op2:
                self.ttype = node.ttype
                if node.op2.kind == Parser.ID:
                    self.CODE.append('\tmov eax, {}\n'.format(define(node.op2)))
                    self.CODE.append("\tmov dword ptr [ebp - {}], eax\n".format(self.counter))
                else:
                    self.compile(node.op2)
                    self.current_var = None
                    self.CODE.append("\tpop eax\n")
                    self.CODE.append("\tmov dword ptr [ebp - {}], eax\n".format(self.counter))
                self.ttype = None
            else:
                self.CODE.append("\tmov dword ptr [ebp - {}], 0\n".format(self.counter))

        elif node.kind == Parser.BLOCK:
            outer = self.var_map.copy()
            self.scope.append(outer)
            self.var_map = {}
            self.iter_compile(node.op1)
            self.var_map = self.scope.pop()

        elif node.kind == Parser.TERNARY:
            self.if_counter += 1
            counter = self.if_counter
            if self.nested[0] is False:
                self.CODE.append("my_if{}:\n".format(counter))
                self.nested[1] = self.if_counter
            if node.op1.kind in (Parser.CONST, Parser.ID):
                self.CODE.append('\tmov eax, {}\n\tcmp eax, 0\n\tjle else{}\n'.format(define(node.op1), counter))
            else:
                self.compile(node.op1)
                self.CODE.append("\tpop eax\n\tcmp eax, 0\n\tjle else{}\n".format(counter))
            self.CODE.append("then{}:\n".format(counter))
            if node.op2.kind == Parser.TERNARY:
                self.nested[0] = True
                self.nested[1] = self.if_counter
            if node.op2.kind in (Parser.CONST, Parser.ID):
                self.CODE.append('\tmov eax, {}\n\tpush eax\n'.format(define(node.op2)))
                self.CODE.append("\tjmp end_if{}\n".format(self.nested[1]))
            else:
                self.compile(node.op2)
                self.CODE.append("\tjmp end_if{}\n".format(self.nested[1]))
            self.CODE.append("else{}:\n".format(counter))
            if self.nested[1] == counter:
                self.nested[0] = False
            if node.op3.kind == Parser.TERNARY:
                self.nested[0] = True
                self.nested[1] = self.if_counter
            if node.op3.kind in (Parser.CONST, Parser.ID):
                print(node.op3.kind)
                self.CODE.append('\tmov eax, {}\n\tpush eax\n'.format(define(node.op3)))
            else:
                self.compile(node.op3)
            if self.nested[1] == counter:
                self.nested[0] = False
            print(self.nested)
            if self.nested[0] is False:
                self.CODE.append("end_if{}:\n".format(counter))
            counter -= 1

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


if __name__ == '__main__':
    a = Lexer('lab1.c')
    a = a.next_token()
    p = Parser(a)
    ast = p.parse()

    com = Compile()
    com.compile(ast)
    com.printer()

# TODO
#   1) make function for (xor, div, prod) -> same code coping
#   2) error messages are ugly through all code, many bugs
#   3) If there are more then one return statement
#   4) make real tests cause if some hotfixes is needed it should be tested fast.
#   5) should found better solution to parse TERNARY into CODE GEN
#   6) !(a=0) and !(a) works ugly -- IT IS WORKING FINE but extra POP (or less push) --> cant reproduce today
#   7) ugly type checking  float == int; !!!!!!!!!!!!!!!!!!!! ---> FIX IT but wanna check more
#   8) we should always "return" only int --> just think about it
#   ------------------------------------------------------------------------------
#   9) "main" function with no params and it shouldnt be called
#   10) bad work of 'return' -> it should always move result in eax and after main is end we should move ebx, eax
#   11) if we have no DIV dont use error in asm for it
#   12) check if it just work
