from dataclasses import dataclass, field
from multimethod import multimethod
from typing import List, Union, Optional

# =====================================================================
# Clases Abstractas
# =====================================================================
class Visitor:
    @multimethod
    def visit(self, node, *args, **kwargs):
        raise NotImplementedError(f"No se implementó visit para {type(node).__name__}")

class Node:
    def __init__(self, lineno=0):
        self.lineno = lineno
    
    def accept(self, v: Visitor, *args, **kwargs):
        return v.visit(self, *args, **kwargs)
    
    def __repr__(self):
        attrs = ', '.join(f"{k}={v!r}" for k, v in self.__dict__.items() 
                         if not k.startswith('_'))
        return f"{self.__class__.__name__}({attrs})"

class Statement(Node):
    pass

class Expression(Node):          
    pass

# =====================================================================
# Definiciones
# =====================================================================
class Program(Node):
    def __init__(self, body=None, lineno=0):
        super().__init__(lineno)
        self.body = body or []

class Literal(Expression):
    def __init__(self, value, type=None, lineno=0):
        super().__init__(lineno)
        self.value = value
        self.type = type

class Integer(Literal):
    def __init__(self, value, lineno=0):
        super().__init__(value, 'integer', lineno)
        assert isinstance(value, int), "Value debe ser integer"

class Float(Literal):
    def __init__(self, value, lineno=0):
        super().__init__(value, 'float', lineno)
        assert isinstance(value, float), "Value debe ser float"

class Char(Literal):
    def __init__(self, value, lineno=0):
        super().__init__(value, 'char', lineno)
        assert isinstance(value, str) and len(value) == 1, "Value del char debe ser string de 1 caracter"

class String(Literal):
    def __init__(self, value, lineno=0):
        super().__init__(value, 'string', lineno)
        assert isinstance(value, str), "Value debe ser string"

class Boolean(Literal):
    def __init__(self, value, lineno=0):
        super().__init__(value, 'boolean', lineno)
        assert isinstance(value, bool), "Value debe ser boolean"

class Variable(Expression):
    def __init__(self, name, lineno=0):
        super().__init__(lineno)
        self.name = name

class ArrayAccess(Expression):
    def __init__(self, name, index, lineno=0):
        super().__init__(lineno)
        self.name = name
        self.index = index

class BinaryOp(Expression):
    def __init__(self, left, op, right, lineno=0):
        super().__init__(lineno)
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(Expression):
    def __init__(self, op, expr, lineno=0):
        super().__init__(lineno)
        self.op = op
        self.expr = expr

class PreInc(Expression):
    def __init__(self, expr, lineno=0):
        super().__init__(lineno)
        self.expr = expr

class PreDec(Expression):
    def __init__(self, expr, lineno=0):
        super().__init__(lineno)
        self.expr = expr
        
class PostInc(Expression):
    def __init__(self, expr, lineno=0):
        super().__init__(lineno)
        self.expr = expr

class PostDec(Expression):
    def __init__(self, expr, lineno=0):
        super().__init__(lineno)
        self.expr = expr

class WhileStmt(Statement):
    def __init__(self, condition, body, lineno=0):
        super().__init__(lineno)
        self.condition = condition
        self.body = body

class DoWhileStmt(Statement):
    def __init__(self, condition, body, lineno=0):
        super().__init__(lineno)
        self.condition = condition
        self.body = body

class FunctionCall(Expression):
    def __init__(self, name, args=None, lineno=0):
        super().__init__(lineno)
        self.name = name
        self.args = args or []

class Assignment(Expression):
    def __init__(self, target, value, lineno=0):
        super().__init__(lineno)
        self.target = target
        self.value = value

class Declaration(Statement):
    def __init__(self, name, type, value=None, lineno=0):
        super().__init__(lineno)
        self.name = name
        self.type = type
        self.value = value

class ArrayDeclaration(Statement):
    def __init__(self, name, type, size_expr=None, values=None, lineno=0):  
        super().__init__(lineno)
        self.name = name
        self.type = type
        self.size_expr = size_expr  
        self.values = values or []

class FunctionDeclaration(Statement):
    def __init__(self, name, return_type, params=None, body=None, lineno=0):
        super().__init__(lineno)
        self.name = name
        self.return_type = return_type
        self.params = params or []
        self.body = body or []

class Param(Node):
    def __init__(self, name, type, size_expr=None, lineno=0):
        super().__init__(lineno)
        self.name = name
        self.type = type
        self.size_expr = size_expr

class IfStatement(Statement):
    def __init__(self, condition, then_branch, else_branch=None, lineno=0):
        super().__init__(lineno)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

class ForStatement(Statement):
    def __init__(self, init, condition, update, body, lineno=0):
        super().__init__(lineno)
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body

class PrintStatement(Statement):
    def __init__(self, expressions=None, lineno=0):
        super().__init__(lineno)
        self.expressions = expressions or []

class ReturnStatement(Statement):
    def __init__(self, value=None, lineno=0):
        super().__init__(lineno)
        self.value = value

class BlockStatement(Statement):
    def __init__(self, statements=None, lineno=0):
        super().__init__(lineno)
        self.statements = statements or []