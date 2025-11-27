"""
Intérprete para el lenguaje B-Minor
====================================
Este módulo implementa un intérprete que ejecuta programas B-Minor
utilizando el patrón de diseño Visitor sobre un AST.

Autor: [Tu nombre]
Versión: 1.0
"""

from collections import ChainMap
from rich import print

from model import *
from errors import error

def _is_truthy(value):
    #Determina si un valor es considerado verdadero en B-Minor.
    
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
       # Retorna el número de parámetros que acepta la función.
        
        return len(self.node.params)

    def __call__(self, interp, *args):
        # Ejecuta la función con los argumentos proporcionados.
        
        # Crear un nuevo entorno para la función
        newenv = interp.env.new_child()
        
        # Vincular parámetros con argumentos
        for param, arg in zip(self.node.params, args):
            newenv[param.name] = arg

        # Guardar el entorno actual y cambiar al entorno de la función
        oldenv = interp.env
        interp.env = newenv
        
        try:
            # Ejecutar todas las instrucciones del cuerpo
            for stmt in self.node.body:
                stmt.accept(interp)
            result = None  # Si no hay return, retornar None
            
        except ReturnException as e:
            # Capturar el valor del return
            result = e.value
            
        finally:
            # Restaurar el entorno original
            interp.env = oldenv
            
        return result

class Interpreter(Visitor):
    #    Implementa el patrón Visitor para recorrer y ejecutar el AST.
    
    def __init__(self):
        """Inicializa el intérprete con un entorno vacío."""
        self.env = ChainMap()

    def _check_numeric_operands(self, node, left, right):
        # Verifica que dos operandos sean números (int o float).
        
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return True
        else:
            error(f"En '{node.op}' los operandos deben ser numeros", node.lineno)
            raise BminorExit()

    def _check_numeric_operand(self, node, value):
        #Verifica que un operando sea número (int o float).
        
        if isinstance(value, (int, float)):
            return True
        else:
            error(f"En '{node.op}' el operando debe ser un numero", node.lineno)
            raise BminorExit()

    def _set_variable(self, name, value):
        # Asigna un valor a una variable, buscando en los scopes disponibles.   Si la variable no existe, la crea en el scope actual.
        
        # Buscar en qué scope existe la variable
        for scope in self.env.maps:
            if name in scope:
                scope[name] = value
                return
                
        # Si no existe, crear en el scope actual
        self.env[name] = value

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

    @multimethod
    def visit(self, node: Program):
        
        for decl in node.body:
            decl.accept(self)

    @multimethod
    def visit(self, node: FunctionDeclaration):
        
        func = Function(node, self.env)
        self.env[node.name] = func

    @multimethod
    def visit(self, node: Declaration):
        
        if node.value:
            # Si hay valor inicial, evaluarlo
            expr = node.value.accept(self)
        else:
            # Asignar valor por defecto según tipo
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
            # Determinar el tamaño evaluando la expresión
            size = 0
            if node.size_expr:
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

    @multimethod
    def visit(self, node: PrintStatement):
        
        for expr in node.expressions:
            value = expr.accept(self)
            
            # Procesar secuencias de escape en strings
            if isinstance(value, str):
                value = value.replace('\\n', '\n')
                value = value.replace('\\t', '\t')
                
            print(value, end='')

    @multimethod
    def visit(self, node: WhileStmt):
        """
        Ejecuta un bucle while.
        Continúa mientras la condición sea verdadera.
        """
        while _is_truthy(node.condition.accept(self)):
            try:
                node.body.accept(self)
            except BreakException:
                # Salir del bucle
                return
            except ContinueException:
                # Continuar a la siguiente iteración
                continue

    @multimethod
    def visit(self, node: DoWhileStmt):
        
        # Primera iteración (siempre se ejecuta)
        try:
            node.body.accept(self)
        except BreakException:
            return
        except ContinueException:
            pass
        
        # Iteraciones siguientes (mientras la condición sea verdadera)
        while _is_truthy(node.condition.accept(self)):
            try:
                node.body.accept(self)
            except BreakException:
                return
            except ContinueException:
                continue

    @multimethod
    def visit(self, node: IfStatement):
        """
        Ejecuta una sentencia condicional if-else.
        """
        expr = node.condition.accept(self)
        
        if _is_truthy(expr):
            # Ejecutar rama then
            node.then_branch.accept(self)
        elif node.else_branch:
            # Ejecutar rama else (si existe)
            node.else_branch.accept(self)

    @multimethod
    def visit(self, node: ForStatement):
        
        # Ejecutar inicialización (si existe)
        if node.init:
            node.init.accept(self)
        
        # Bucle principal
        while True:
            # Verificar condición (si existe)
            if node.condition:
                if not _is_truthy(node.condition.accept(self)):
                    break
            
            # Ejecutar cuerpo del bucle
            try:
                node.body.accept(self)
            except BreakException:
                break
            except ContinueException:
                pass
            
            # Ejecutar actualización (si existe)
            if node.update:
                node.update.accept(self)

    @multimethod
    def visit(self, node: ReturnStatement):
        
        value = None if not node.value else node.value.accept(self)
        raise ReturnException(value)

    @multimethod
    def visit(self, node: BlockStatement):
        
        # Crear nuevo scope hijo
        newenv = self.env.new_child()
        oldenv = self.env
        self.env = newenv
        
        try:
            # Ejecutar todas las sentencias del bloque
            for stmt in node.statements:
                stmt.accept(self)
        finally:
            # Restaurar el scope anterior
            self.env = oldenv

    @multimethod
    def visit(self, node: BinaryOp):
        
        # Evaluar operandos
        left = node.left.accept(self)
        right = node.right.accept(self)

        # Operador suma (aritmética o concatenación de strings)
        if node.op == '+':
            if isinstance(left, str) and isinstance(right, str):
                return left + right  # Concatenación
            self._check_numeric_operands(node, left, right)
            return left + right

        # Operador resta
        elif node.op == '-':
            self._check_numeric_operands(node, left, right)
            return left - right

        # Operador multiplicación
        elif node.op == '*':
            self._check_numeric_operands(node, left, right)
            return left * right

        # Operador división
        elif node.op == '/':
            self._check_numeric_operands(node, left, right)
            # División entera si ambos operandos son enteros
            if isinstance(left, int) and isinstance(right, int):
                return left // right
            return left / right

        # Operador módulo
        elif node.op == '%':
            self._check_numeric_operands(node, left, right)
            return left % right

        # Operador potencia
        elif node.op == '^':
            self._check_numeric_operands(node, left, right)
            return left ** right

        # Operador igualdad
        elif node.op == '==':
            return left == right

        # Operador desigualdad
        elif node.op == '!=':
            return left != right

        # Operador menor que
        elif node.op == '<':
            self._check_numeric_operands(node, left, right)
            return left < right

        # Operador mayor que
        elif node.op == '>':
            self._check_numeric_operands(node, left, right)
            return left > right

        # Operador menor o igual
        elif node.op == '<=':
            self._check_numeric_operands(node, left, right)
            return left <= right

        # Operador mayor o igual
        elif node.op == '>=':
            self._check_numeric_operands(node, left, right)
            return left >= right

        # Operador AND lógico
        elif node.op == '&&':
            return _is_truthy(left) and _is_truthy(right)

        # Operador OR lógico
        elif node.op == '||':
            return _is_truthy(left) or _is_truthy(right)

        else:
            raise NotImplementedError(f"Operador no implementado: {node.op}")

    @multimethod
    def visit(self, node: UnaryOp):
        
        value = node.expr.accept(self)
        
        if node.op == '-':
            # Negación numérica
            self._check_numeric_operand(node, value)
            return -value
        elif node.op == '!':
            # Negación lógica
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
        return value  # Retorna el valor antes del incremento

    @multimethod
    def visit(self, node: PostDec):
        
        var_name = node.expr.name
        value = self.env[var_name]
        self._check_numeric_operand(node, value)
        self._set_variable(var_name, value - 1)
        return value  # Retorna el valor antes del decremento

    @multimethod
    def visit(self, node: Assignment):
        
        # Evaluar el valor a asignar
        value = node.value.accept(self)
        
        if isinstance(node.target, Variable):
            # Asignación a variable simple
            self._set_variable(node.target.name, value)
            
        elif isinstance(node.target, ArrayAccess):
            # Asignación a elemento de array
            array = self.env[node.target.name]
            index = node.target.index.accept(self)
            
            # Verificar que el índice sea entero
            if not isinstance(index, int):
                error(f"Índice debe ser entero", node.lineno)
                raise BminorExit()
            
            # Verificar límites del array
            if index < 0 or index >= len(array):
                error(f"Índice {index} fuera de rango [0, {len(array)-1}]", node.lineno)
                raise BminorExit()
            
            # Realizar la asignación
            array[index] = value
        
        return value

    @multimethod
    def visit(self, node: FunctionCall):
        
        # Obtener la función del entorno
        callee = self.env.get(node.name)
        if not callable(callee):
            error(f"'{node.name}' no es invocable", node.lineno)
            raise BminorExit()

        # Evaluar todos los argumentos
        args = [arg.accept(self) for arg in node.args]

        # Verificar número de argumentos (-1 significa variadic)
        if callee.arity != -1 and len(args) != callee.arity:
            error(f"Esperado {callee.arity} argumentos", node.lineno)
            raise BminorExit()

        # Ejecutar la función
        return callee(self, *args)


    @multimethod
    def visit(self, node: Integer):
        # Retorna el valor del literal entero.
        return node.value

    @multimethod
    def visit(self, node: Float):
        # Retorna el valor del literal flotante.
        return node.value

    @multimethod
    def visit(self, node: Char):
        # Retorna el valor del literal carácter.
        return node.value

    @multimethod
    def visit(self, node: String):
        # Retorna el valor del literal string.
        return node.value

    @multimethod
    def visit(self, node: Boolean):
        # Retorna el valor del literal booleano.
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
        
        # Obtener el array del entorno
        array = self.env.get(node.name)
        if array is None:
            error(f"Array '{node.name}' no definido", node.lineno)
            raise BminorExit()
        
        # Evaluar el índice
        index = node.index.accept(self)
        if not isinstance(index, int):
            error(f"Índice debe ser entero", node.lineno)
            raise BminorExit()
        
        # Verificar límites
        if index < 0 or index >= len(array):
            error(f"Índice {index} fuera de rango [0, {len(array)-1}]", node.lineno)
            raise BminorExit()
        
        return array[index]

def interpret_program(ast):
    interpreter = Interpreter()
    interpreter.interpret(ast)

if __name__ == "__main__":
    from parser import parse
    import sys
    
    # Verificar argumentos
    if len(sys.argv) != 2:
        print("Uso: python src/interp.py <archivo.bminor>")
        sys.exit(1)
        
    # Obtener nombre del archivo
    filename = sys.argv[1]
    
    # Leer el código fuente
    with open(filename, 'r') as f:
        source = f.read()
    
    # Parsear a AST
    ast = parse(source)
    
    # Interpretar el programa
    interpret_program(ast)