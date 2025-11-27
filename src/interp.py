from collections import ChainMap
from rich import print

from model import *
from errors import error

# Veracidad en bminor
def _is_truthy(value):
    if isinstance(value, bool):
        return value
    elif value is None:
        return False
    else:
        return True

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

class BminorExit(BaseException):
    pass

class Function:
    def __init__(self, node, env):
        self.node = node
        self.env = env

    @property
    def arity(self) -> int:
        return len(self.node.params)

    def __call__(self, interp, *args):
        newenv = interp.env.new_child()
        for param, arg in zip(self.node.params, args):
            newenv[param.name] = arg

        oldenv = interp.env
        interp.env = newenv
        try:
            for stmt in self.node.body:
                stmt.accept(interp)
            result = None
        except ReturnException as e:
            result = e.value
        finally:
            interp.env = oldenv
        return result

class Interpreter(Visitor):
    def __init__(self):
        self.env = ChainMap()

    def _check_numeric_operands(self, node, left, right):
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return True
        else:
            error(f"En '{node.op}' los operandos deben ser numeros", node.lineno)
            raise BminorExit()

    def _check_numeric_operand(self, node, value):
        if isinstance(value, (int, float)):
            return True
        else:
            error(f"En '{node.op}' el operando debe ser un numero", node.lineno)
            raise BminorExit()

    def _set_variable(self, name, value):
        # Buscar en qué scope existe la variable
        for scope in self.env.maps:
            if name in scope:
                scope[name] = value
                return
        # Si no existe, crear en el scope actual
        self.env[name] = value

    # Punto de entrada alto-nivel
    def interpret(self, ast):
        try:
            # Primero cargar todas las declaraciones globales y funciones
            ast.accept(self)
            
            # Luego buscar y ejecutar main()
            if 'main' in self.env:
                main_func = self.env['main']
                if callable(main_func):
                    main_func(self)
                else:
                    error("'main' debe ser una función", 0)
            else:
                error("No se encontró la función main()", 0)
                
        except BminorExit:
            pass

    # Program
    @multimethod
    def visit(self, node: Program):
        for decl in node.body:
            decl.accept(self)

    # Declarations
    @multimethod
    def visit(self, node: FunctionDeclaration):
        func = Function(node, self.env)
        self.env[node.name] = func

    @multimethod
    def visit(self, node: Declaration):
        if node.value:
            expr = node.value.accept(self)
        else:
            # Valor por defecto según tipo
            if node.type == 'integer':
                expr = 0
            elif node.type == 'float':
                expr = 0.0
            elif node.type == 'boolean':
                expr = False
            elif node.type == 'char':
                expr = '\0'
            else:
                expr = None
        self.env[node.name] = expr

    @multimethod
    def visit(self, node: ArrayDeclaration):
        # Calcular el tamaño del array
        if node.values:
            # Si hay valores iniciales, usar esa longitud
            array = [val.accept(self) for val in node.values]
        else:
            # Determinar el tamaño
            size = 0
            if node.size_expr:
                # CORRECCIÓN: Evaluar la expresión para obtener el tamaño
                size_value = node.size_expr.accept(self)
                if isinstance(size_value, int):
                    size = size_value
                else:
                    error(f"Tamaño de array debe ser entero", node.lineno)
                    raise BminorExit()
            
            # Inicializar array con valores por defecto según el tipo
            if node.type == 'integer':
                array = [0] * size
            elif node.type == 'float':
                array = [0.0] * size
            elif node.type == 'boolean':
                array = [False] * size
            elif node.type == 'char':
                array = ['\0'] * size
            else:
                array = [None] * size
        
        self.env[node.name] = array

    # Statements
    @multimethod
    def visit(self, node: PrintStatement):
        for expr in node.expressions:
            value = expr.accept(self)
            if isinstance(value, str):
                value = value.replace('\\n', '\n')
                value = value.replace('\\t', '\t')
            print(value, end='')

    @multimethod
    def visit(self, node: WhileStmt):
        while _is_truthy(node.condition.accept(self)):
            try:
                node.body.accept(self)
            except BreakException:
                return
            except ContinueException:
                continue

    @multimethod
    def visit(self, node: DoWhileStmt):
        try:
            node.body.accept(self)
        except BreakException:
            return
        except ContinueException:
            pass
        
        while _is_truthy(node.condition.accept(self)):
            try:
                node.body.accept(self)
            except BreakException:
                return
            except ContinueException:
                continue

    @multimethod
    def visit(self, node: IfStatement):
        expr = node.condition.accept(self)
        if _is_truthy(expr):
            node.then_branch.accept(self)
        elif node.else_branch:
            node.else_branch.accept(self)

    @multimethod
    def visit(self, node: ForStatement):
        if node.init:
            node.init.accept(self)
        
        while True:
            if node.condition:
                if not _is_truthy(node.condition.accept(self)):
                    break
            
            try:
                node.body.accept(self)
            except BreakException:
                break
            except ContinueException:
                pass
            
            if node.update:
                node.update.accept(self)

    @multimethod
    def visit(self, node: ReturnStatement):
        value = None if not node.value else node.value.accept(self)
        raise ReturnException(value)

    @multimethod
    def visit(self, node: BlockStatement):
        newenv = self.env.new_child()
        oldenv = self.env
        self.env = newenv
        try:
            for stmt in node.statements:
                stmt.accept(self)
        finally:
            self.env = oldenv

    # Expressions
    @multimethod
    def visit(self, node: BinaryOp):
        left = node.left.accept(self)
        right = node.right.accept(self)

        if node.op == '+':
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            self._check_numeric_operands(node, left, right)
            return left + right

        elif node.op == '-':
            self._check_numeric_operands(node, left, right)
            return left - right

        elif node.op == '*':
            self._check_numeric_operands(node, left, right)
            return left * right

        elif node.op == '/':
            self._check_numeric_operands(node, left, right)
            if isinstance(left, int) and isinstance(right, int):
                return left // right
            return left / right

        elif node.op == '%':
            self._check_numeric_operands(node, left, right)
            return left % right

        elif node.op == '^':
            self._check_numeric_operands(node, left, right)
            return left ** right

        elif node.op == '==':
            return left == right

        elif node.op == '!=':
            return left != right

        elif node.op == '<':
            self._check_numeric_operands(node, left, right)
            return left < right

        elif node.op == '>':
            self._check_numeric_operands(node, left, right)
            return left > right

        elif node.op == '<=':
            self._check_numeric_operands(node, left, right)
            return left <= right

        elif node.op == '>=':
            self._check_numeric_operands(node, left, right)
            return left >= right

        elif node.op == '&&':
            return _is_truthy(left) and _is_truthy(right)

        elif node.op == '||':
            return _is_truthy(left) or _is_truthy(right)

        else:
            raise NotImplementedError(f"Operador no implementado: {node.op}")

    @multimethod
    def visit(self, node: UnaryOp):
        value = node.expr.accept(self)
        
        if node.op == '-':
            self._check_numeric_operand(node, value)
            return -value
        elif node.op == '!':
            return not _is_truthy(value)
        else:
            raise NotImplementedError(f"Operador unario no implementado: {node.op}")

    @multimethod
    def visit(self, node: PreInc):
        var_name = node.expr.name
        value = self.env[var_name]
        self._check_numeric_operand(node, value)
        new_value = value + 1
        self._set_variable(var_name, new_value)
        return new_value

    @multimethod
    def visit(self, node: PreDec):
        var_name = node.expr.name
        value = self.env[var_name]
        self._check_numeric_operand(node, value)
        new_value = value - 1
        self._set_variable(var_name, new_value)
        return new_value

    @multimethod
    def visit(self, node: PostInc):
        var_name = node.expr.name
        value = self.env[var_name]
        self._check_numeric_operand(node, value)
        self._set_variable(var_name, value + 1)
        return value

    @multimethod
    def visit(self, node: PostDec):
        var_name = node.expr.name
        value = self.env[var_name]
        self._check_numeric_operand(node, value)
        self._set_variable(var_name, value - 1)
        return value

    @multimethod
    def visit(self, node: Assignment):
        value = node.value.accept(self)
        
        if isinstance(node.target, Variable):
            self._set_variable(node.target.name, value)
        elif isinstance(node.target, ArrayAccess):
            array = self.env[node.target.name]
            index = node.target.index.accept(self)
            
            # Verificar límites del array
            if not isinstance(index, int):
                error(f"Índice debe ser entero", node.lineno)
                raise BminorExit()
            
            if index < 0 or index >= len(array):
                error(f"Índice {index} fuera de rango [0, {len(array)-1}]", node.lineno)
                raise BminorExit()
            
            array[index] = value
        
        return value

    @multimethod
    def visit(self, node: FunctionCall):
        callee = self.env.get(node.name)
        if not callable(callee):
            error(f"'{node.name}' no es invocable", node.lineno)
            raise BminorExit()

        args = [arg.accept(self) for arg in node.args]

        if callee.arity != -1 and len(args) != callee.arity:
            error(f"Esperado {callee.arity} argumentos", node.lineno)
            raise BminorExit()

        return callee(self, *args)

    # Literals
    @multimethod
    def visit(self, node: Integer):
        return node.value

    @multimethod
    def visit(self, node: Float):
        return node.value

    @multimethod
    def visit(self, node: Char):
        return node.value

    @multimethod
    def visit(self, node: String):
        return node.value

    @multimethod
    def visit(self, node: Boolean):
        return node.value

    @multimethod
    def visit(self, node: Variable):
        if node.name in self.env:
            return self.env[node.name]
        else:
            error(f"Variable '{node.name}' no definida", node.lineno)
            raise BminorExit()

    @multimethod
    def visit(self, node: ArrayAccess):
        array = self.env.get(node.name)
        if array is None:
            error(f"Array '{node.name}' no definido", node.lineno)
            raise BminorExit()
        
        index = node.index.accept(self)
        if not isinstance(index, int):
            error(f"Índice debe ser entero", node.lineno)
            raise BminorExit()
        
        if index < 0 or index >= len(array):
            error(f"Índice {index} fuera de rango [0, {len(array)-1}]", node.lineno)
            raise BminorExit()
        
        return array[index]


def interpret_program(ast):
    """Interpreta un programa B-Minor"""
    interpreter = Interpreter()
    interpreter.interpret(ast)

if __name__ == "__main__":
    from parser import parse
    import sys
    if len(sys.argv) != 2:
        print("Uso: python src/interp.py <archivo.bminor>")
        sys.exit(1)
    filename = sys.argv[1]
    with open(filename, 'r') as f: # Abrir el archivo
        source = f.read() # Leer el código fuente
    ast = parse(source) # Parsear a AST
    interpret_program(ast)