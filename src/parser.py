import logging
import sly
from rich import print
import os
import sys

# Agrega el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importa los módulos correctamente
from lexer import Lexer
from errors import error
from model import *

def _L(node, lineno):
    node.lineno = lineno
    return node

class Parser(sly.Parser):
    log = logging.getLogger()
    log.setLevel(logging.ERROR)
    expected_shift_reduce = 1
    debugfile = 'grammar.txt'

    tokens = Lexer.tokens

    precedence = (
        ('right', '='),
        ('left', 'OR'),
        ('left', 'AND'),
        ('nonassoc', 'IGUAL', 'NO_IGUAL', 'MENOR_QUE', 'MENOR_IGUAL', 'MAYOR_QUE', 'MAYOR_IGUAL'),
        ('left', '+', '-'),
        ('left', '*', '/', '%'),
        ('right', '^'),
        ('right', 'UMINUS', 'NOT'),
    )

    # ==================== PROGRAM ====================
    @_("decl_list")
    def prog(self, p):
        return Program(p.decl_list)

    # ==================== DECLARATIONS ====================
    @_("decl decl_list")
    def decl_list(self, p):
        return [p.decl] + p.decl_list

    @_("empty")
    def decl_list(self, p):
        return []

    @_("ID ':' type_name ';'")
    def decl(self, p):
        return Declaration(p.ID, p.type_name, lineno=p.lineno)
    
    @_("ID ':' type_name '=' expr ';'")
    def decl(self, p):
        return Declaration(p.ID, p.type_name, p.expr, lineno=p.lineno)

    @_("ID ':' array_type ';'")
    def decl(self, p):
        array_type, size_expr, elem_type = p.array_type
        return ArrayDeclaration(p.ID, elem_type, size_expr, lineno=p.lineno)  # size_expr -> size

    @_("ID ':' function_type ';'")
    def decl(self, p):
        return_type, params = p.function_type
        return FunctionDeclaration(p.ID, return_type, params, [], lineno=p.lineno)

    @_("ID ':' array_type '=' '{' opt_expr_list '}' ';'")
    def decl_init(self, p):
        array_type, size_expr, elem_type = p.array_type
        return ArrayDeclaration(p.ID, elem_type, size_expr, p.opt_expr_list, lineno=p.lineno)

    @_("ID ':' function_type '=' '{' opt_stmt_list '}'")
    def decl_init(self, p):
        return_type, params = p.function_type
        return FunctionDeclaration(p.ID, return_type, params, p.opt_stmt_list, lineno=p.lineno)

    @_("decl_init")
    def decl(self, p):
        return p.decl_init
    
    # ==================== TYPES (SIMPLIFICADOS) ====================
    @_("INTEGER")
    def type_name(self, p):
        return 'integer'

    @_("FLOAT")
    def type_name(self, p):
        return 'float'

    @_("BOOLEAN")
    def type_name(self, p):
        return 'boolean'

    @_("CHAR")
    def type_name(self, p):
        return 'char'

    @_("STRING")
    def type_name(self, p):
        return 'string'

    @_("VOID")
    def type_name(self, p):
        return 'void'

    @_("ARRAY '[' ']' type_name")
    def array_type(self, p):
        return ('array', None, p.type_name)

    @_("ARRAY '[' expr ']' type_name")
    def array_type(self, p):
        return ('array', p.expr, p.type_name)

    @_("FUNCTION type_name '(' opt_param_list ')'")
    def function_type(self, p):
        return (p.type_name, p.opt_param_list)

    @_("empty")
    def opt_param_list(self, p):
        return []

    @_("param_list")
    def opt_param_list(self, p):
        return p.param_list

    @_("param_list ',' param")
    def param_list(self, p):
        return p.param_list + [p.param]

    @_("param")
    def param_list(self, p):
        return [p.param]
    
    @_("ID ':' type_name")
    def param(self, p):
        return Param(p.ID, p.type_name, lineno=p.lineno)

    @_("ID ':' array_type")
    def param(self, p):
        array_type, size_expr, elem_type = p.array_type
        return Param(p.ID, elem_type, size_expr, lineno=p.lineno)
    # ==================== STATEMENTS ====================
    @_("stmt_list")
    def opt_stmt_list(self, p):
        return p.stmt_list

    @_("empty")
    def opt_stmt_list(self, p):
        return []

    @_("stmt stmt_list")
    def stmt_list(self, p):
        return [p.stmt] + p.stmt_list

    @_("stmt")
    def stmt_list(self, p):
        return [p.stmt]

    # ==================== WHILE STATEMENTS ====================
    @_("WHILE '(' expr ')' stmt")
    def stmt(self, p):
        return WhileStmt(p.expr, p.stmt, lineno=p.lineno)

    @_("DO stmt WHILE '(' expr ')' ';'")
    def stmt(self, p):
        return DoWhileStmt(p.expr, p.stmt, lineno=p.lineno)

    # ==================== IF STATEMENTS ====================
    # CORRECCIÓN: Eliminé %prec IFX
    @_("IF '(' expr ')' stmt")
    def stmt(self, p):
        return IfStatement(p.expr, p.stmt, lineno=p.lineno)

    @_("IF '(' expr ')' stmt ELSE stmt")
    def stmt(self, p):
        return IfStatement(p.expr, p.stmt0, p.stmt1, lineno=p.lineno)

    # ==================== FOR STATEMENTS ====================
    @_("FOR '(' opt_expr ';' opt_expr ';' opt_expr ')' stmt")
    def stmt(self, p):
        return ForStatement(p.opt_expr0, p.opt_expr1, p.opt_expr2, p.stmt, lineno=p.lineno)

    # ==================== SIMPLE STATEMENTS ====================
    @_("print_stmt")
    def stmt(self, p):
        return p.print_stmt

    @_("return_stmt")
    def stmt(self, p):
        return p.return_stmt

    @_("block_stmt")
    def stmt(self, p):
        return p.block_stmt

    @_("decl")
    def stmt(self, p):
        return p.decl

    @_("expr ';'")
    def stmt(self, p):
        return p.expr

    @_("PRINT opt_expr_list ';'")
    def print_stmt(self, p):
        return PrintStatement(p.opt_expr_list, lineno=p.lineno)
        
    @_("RETURN opt_expr ';'")
    def return_stmt(self, p):
        return ReturnStatement(p.opt_expr, lineno=p.lineno)

    @_("'{' stmt_list '}'")
    def block_stmt(self, p):
        return BlockStatement(p.stmt_list, lineno=p.lineno)
    
    # ==================== EXPRESSIONS ====================
    @_("empty")
    def opt_expr_list(self, p):
        return []

    @_("expr_list")
    def opt_expr_list(self, p):
        return p.expr_list
        
    @_("expr ',' expr_list")
    def expr_list(self, p):
        return [p.expr] + p.expr_list
        
    @_("expr")
    def expr_list(self, p):
        return [p.expr]

    @_("empty")
    def opt_expr(self, p):
        return None

    @_("expr")
    def opt_expr(self, p):
        return p.expr

    @_("lval '=' expr")
    def expr(self, p):
        return Assignment(p.lval, p.expr, lineno=p.lineno)

    @_("expr OR expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '||', p.expr1, lineno=p.lineno)

    @_("expr AND expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '&&', p.expr1, lineno=p.lineno)

    @_("expr IGUAL expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '==', p.expr1, lineno=p.lineno)

    @_("expr NO_IGUAL expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '!=', p.expr1, lineno=p.lineno)

    @_("expr MENOR_QUE expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '<', p.expr1, lineno=p.lineno)

    @_("expr MENOR_IGUAL expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '<=', p.expr1, lineno=p.lineno)

    @_("expr MAYOR_QUE expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '>', p.expr1, lineno=p.lineno)

    @_("expr MAYOR_IGUAL expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '>=', p.expr1, lineno=p.lineno)
    
    @_("expr INC %prec UMINUS")
    def expr(self, p):
        return PostInc(p.expr, lineno=p.lineno)
        
    @_("expr DEC %prec UMINUS")
    def expr(self, p):
        return PostDec(p.expr, lineno=p.lineno)

    @_("expr '+' expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '+', p.expr1, lineno=p.lineno)

    @_("expr '-' expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '-', p.expr1, lineno=p.lineno)

    @_("expr '*' expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '*', p.expr1, lineno=p.lineno)

    @_("expr '/' expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '/', p.expr1, lineno=p.lineno)

    @_("expr '%' expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '%', p.expr1, lineno=p.lineno)

    @_("expr '^' expr")
    def expr(self, p):
        return BinaryOp(p.expr0, '^', p.expr1, lineno=p.lineno)

    @_("'-' expr %prec UMINUS")
    def expr(self, p):
        return UnaryOp('-', p.expr, lineno=p.lineno)
        
    @_("NOT expr")
    def expr(self, p):
        return UnaryOp('!', p.expr, lineno=p.lineno)
        
    # ==================== OPERADORES UNARIOS (++ y --) ====================
    @_("INC expr %prec UMINUS")
    def expr(self, p):
        return PreInc(p.expr, lineno=p.lineno)
        
    @_("DEC expr %prec UMINUS")
    def expr(self, p):
        return PreDec(p.expr, lineno=p.lineno)
        
    @_("'(' expr ')'")
    def expr(self, p):
        return p.expr
        
    @_("ID '(' opt_expr_list ')'")
    def expr(self, p):
        return FunctionCall(p.ID, p.opt_expr_list, lineno=p.lineno)

    @_("ID '[' expr ']'")
    def expr(self, p):
        return ArrayAccess(p.ID, p.expr, lineno=p.lineno)
    
    @_("ID")
    def expr(self, p):
        return Variable(p.ID, lineno=p.lineno)

    @_("INTEGER_CONST")
    def expr(self, p):
        return _L(Integer(int(p.INTEGER_CONST)), p.lineno)

    @_("FLOAT_CONST")
    def expr(self, p):
        return _L(Float(float(p.FLOAT_CONST)), p.lineno)

    @_("CHAR_CONST")
    def expr(self, p):
        return _L(Char(p.CHAR_CONST), p.lineno)
        
    @_("STRING_CONST")
    def expr(self, p):
        return _L(String(p.STRING_CONST), p.lineno)
        
    @_("TRUE")
    def expr(self, p):
        return _L(Boolean(True), p.lineno)

    @_("FALSE")
    def expr(self, p):
        return _L(Boolean(False), p.lineno)

    # ==================== LVAL ====================
    @_("ID")
    def lval(self, p):
        return Variable(p.ID, lineno=p.lineno)

    @_("ID '[' expr ']'")
    def lval(self, p):
        return ArrayAccess(p.ID, p.expr, lineno=p.lineno)

    @_("")
    def empty(self, p):
        pass

    def error(self, p):
        lineno = p.lineno if p else 'EOF'
        value = repr(p.value) if p else 'EOF'
        error(f'Syntax error at {value}', lineno)
        
def parse(txt):
    l = Lexer()
    p = Parser()
    return p.parse(l.tokenize(txt))

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python parser.py <filename>")

    filename = sys.argv[1]
    txt = open(filename, encoding='utf-8').read()
    ast = parse(txt)
    
    print(ast)