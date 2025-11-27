from rich import print
from typing import Union, List
from multimethod import multimethod

from errors import error, errors_detected
from model import *
from symtab import Symtab
from typesys import typenames, check_binop, check_unaryop, CheckError


class Check(Visitor):
    @classmethod
    def checker(cls, n: Program):
        checker = cls()

        # Crear una nueva tabla de símbolos global
        env = Symtab('global')

        # Agregar funciones built-in
        checker.add_builtins(env)

        # Visitar todas las declaraciones
        for s in n.body:
            s.accept(checker, env)
        return env
    
    def add_builtins(self, env: Symtab):
        """Agregar funciones predefinidas del lenguaje"""
        # array_length: function integer (arr: array [] any_type)
        array_length_decl = FunctionDeclaration(
            name='array_length',
            return_type='integer',
            params=[
                Param(name='arr', type='integer', size_expr=None)
            ],
            body=[],
            lineno=0
        )
        array_length_decl.is_builtin = True
        env.add('array_length', array_length_decl)
    
    # ==================== DECLARACIONES ====================
    
    @multimethod
    def visit(self, n: Declaration, env: Symtab):
        """Declaracion simple de variable"""
        # Verificar que el tipo sea valido
        if n.type not in typenames:
            error(f"Tipo '{n.type}' no reconocido", n.lineno)
            return
        
        # Guardar n.name en el contexto actual
        try:
            env.add(n.name, n)
        except Symtab.SymbolDefinedError:
            error(f"La variable '{n.name}' ya esta definida", n.lineno)
        except Symtab.SymbolConflictError:
            error(f"La variable '{n.name}' ya esta definida con tipo de datos diferente", n.lineno)
        
        # Verificar valor inicial si existe
        if n.value:
            n.value.accept(self, env)
            if hasattr(n.value, 'type') and n.type != n.value.type:
                error(f"La variable '{n.name}' se le esta asignando un tipo de datos erroneo: "
                      f"esperado '{n.type}', recibido '{n.value.type}'", n.lineno)

    @multimethod
    def visit(self, n: ArrayDeclaration, env: Symtab):
        """Declaracion de array"""
        # Verificar que el tipo base sea valido
        if n.type not in typenames:
            error(f"Tipo '{n.type}' no reconocido para array", n.lineno)
            return
        
        # Verificar si ya existe
        try:
            env.add(n.name, n)
        except Symtab.SymbolDefinedError:
            error(f"El array '{n.name}' ya esta definido", n.lineno)
        except Symtab.SymbolConflictError:
            error(f"El array '{n.name}' ya esta definido con tipo diferente", n.lineno)
        
        # Verificar expresion de tamaño si existe
        if n.size_expr:
            n.size_expr.accept(self, env)
            if hasattr(n.size_expr, 'type') and n.size_expr.type != 'integer':
                error(f"Tamaño de array debe ser integer, no '{n.size_expr.type}'", n.lineno)
        
        # Verificar valores iniciales si existen
        if n.values:
            for val in n.values:
                val.accept(self, env)
                if hasattr(val, 'type') and val.type != n.type:
                    error(f"Tipo incompatible en inicializacion de array '{n.name}': "
                          f"esperado '{n.type}', recibido '{val.type}'", n.lineno)

    @multimethod
    def visit(self, n: FunctionDeclaration, env: Symtab):
        """Declaracion de funcion"""
        # Verificar tipo de retorno
        if n.return_type not in typenames and n.return_type != 'void':
            error(f"Tipo de retorno '{n.return_type}' no reconocido", n.lineno)
            return
        
        # Agregar la funcion a la tabla de símbolos
        try:
            env.add(n.name, n)
        except Symtab.SymbolDefinedError:
            error(f"La funcion '{n.name}' ya esta definida", n.lineno)
            return
        except Symtab.SymbolConflictError:
            error(f"La funcion '{n.name}' ya esta definida y con tipo de dato diferente", n.lineno)
            return

        # Crear una tabla de símbolos para la funcion
        func_env = Symtab(f"function:{n.name}", parent=env)

        # Agregar parametros al scope de la funcion
        for param in n.params:
            param.accept(self, func_env)

        # Verificar cuerpo de la funcion
        for stmt in n.body:
            stmt.accept(self, func_env)
    
    @multimethod
    def visit(self, n: Param, env: Symtab):
        """Parametro de funcion"""
        # Verificar tipo
        if n.type not in typenames:
            error(f"Tipo '{n.type}' no reconocido para parametro '{n.name}'", n.lineno)
            return
        
        # Agregar a la tabla de símbolos
        try:
            env.add(n.name, n)
        except Symtab.SymbolDefinedError:
            error(f"Parametro '{n.name}' duplicado", n.lineno)
        except Symtab.SymbolConflictError:
            error(f"Conflicto de tipos en parametro '{n.name}'", n.lineno)
    
    # ==================== STATEMENTS ====================
    
    @multimethod
    def visit(self, n: WhileStmt, env: Symtab):
        """While statement"""
        n.condition.accept(self, env)
        if hasattr(n.condition, 'type') and n.condition.type != 'boolean':
            error(f"Condicion de while debe ser boolean, no '{n.condition.type}'", n.lineno)
        
        # Crear scope solo si el cuerpo no es un BlockStatement (que crea su propio scope)
        if not isinstance(n.body, BlockStatement):
            while_env = Symtab('while', parent=env)
            n.body.accept(self, while_env)
        else:
            n.body.accept(self, env)
    
    @multimethod
    def visit(self, n: DoWhileStmt, env: Symtab):
        """Do-while statement"""
        # Crear scope solo si el cuerpo no es un BlockStatement
        if not isinstance(n.body, BlockStatement):
            do_env = Symtab('do-while', parent=env)
            n.body.accept(self, do_env)
        else:
            n.body.accept(self, env)
        
        n.condition.accept(self, env)
        if hasattr(n.condition, 'type') and n.condition.type != 'boolean':
            error(f"Condicion de do-while debe ser boolean, no '{n.condition.type}'", n.lineno)
    
    @multimethod
    def visit(self, n: IfStatement, env: Symtab):
        """If statement"""
        n.condition.accept(self, env)
        if hasattr(n.condition, 'type') and n.condition.type != 'boolean':
            error(f"Condicion de if debe ser boolean, no '{n.condition.type}'", n.lineno)
        
        # Crear scope para then_branch si no es un BlockStatement
        if not isinstance(n.then_branch, BlockStatement):
            then_env = Symtab('if-then', parent=env)
            n.then_branch.accept(self, then_env)
        else:
            n.then_branch.accept(self, env)
        
        # Crear scope para else_branch si existe y no es un BlockStatement ni otro IfStatement
        if n.else_branch:
            if not isinstance(n.else_branch, (BlockStatement, IfStatement)):
                else_env = Symtab('if-else', parent=env)
                n.else_branch.accept(self, else_env)
            else:
                n.else_branch.accept(self, env)
    
    @multimethod
    def visit(self, n: ForStatement, env: Symtab):
        """For statement - crear scope que incluya init"""
        # Crear nuevo scope para el for (incluye init, condition, update, body)
        for_env = Symtab('for', parent=env)
        
        if n.init:
            n.init.accept(self, for_env)
        if n.condition:
            n.condition.accept(self, for_env)
            if hasattr(n.condition, 'type') and n.condition.type != 'boolean':
                error(f"Condicion de for debe ser boolean, no '{n.condition.type}'", n.lineno)
        if n.update:
            n.update.accept(self, for_env)
        
        # usar el mismo scope del for para evitar anidamiento innecesario
        if isinstance(n.body, BlockStatement):
            for stmt in n.body.statements:
                stmt.accept(self, for_env)
        else:
            n.body.accept(self, for_env)
    
    @multimethod
    def visit(self, n: PrintStatement, env: Symtab):
        """Print statement"""
        for expr in n.expressions:
            expr.accept(self, env)
    
    @multimethod
    def visit(self, n: ReturnStatement, env: Symtab):
        """Return statement"""
        if n.value:
            n.value.accept(self, env)
    
    @multimethod
    def visit(self, n: BlockStatement, env: Symtab):
        """Block statement - crear nuevo scope"""
        block_env = Symtab('block', parent=env)  #Crea el scope
        for stmt in n.statements:
            stmt.accept(self, block_env)  # Visita statements en el scope correcto
    
    # ==================== EXPRESSIONS ====================
    
    @multimethod
    def visit(self, n: Assignment, env: Symtab):
        """Asignacion"""
        n.target.accept(self, env)
        n.value.accept(self, env)
        
        if hasattr(n.target, 'type') and hasattr(n.value, 'type'):
            if n.target.type != n.value.type:
                error(f"Tipos incompatibles en asignacion: '{n.target.type}' y '{n.value.type}'", n.lineno)
            n.type = n.target.type
    
    @multimethod
    def visit(self, n: BinaryOp, env: Symtab):
        """Operacion binaria"""
        n.left.accept(self, env)
        n.right.accept(self, env)
        
        if hasattr(n.left, 'type') and hasattr(n.right, 'type'):
            result_type = check_binop(n.op, n.left.type, n.right.type)
            if result_type is None:
                error(f"Operacion '{n.op}' no soportada entre '{n.left.type}' y '{n.right.type}'", n.lineno)
                n.type = 'integer'  # tipo por defecto
            else:
                n.type = result_type
    
    @multimethod
    def visit(self, n: UnaryOp, env: Symtab):
        """Operacion unaria"""
        n.expr.accept(self, env)
        
        if hasattr(n.expr, 'type'):
            result_type = check_unaryop(n.op, n.expr.type)
            if result_type is None:
                error(f"Operacion unaria '{n.op}' no soportada para '{n.expr.type}'", n.lineno)
                n.type = n.expr.type
            else:
                n.type = result_type
    
    @multimethod
    def visit(self, n: PreInc, env: Symtab):
        """Pre-incremento ++expr"""
        n.expr.accept(self, env)
        if hasattr(n.expr, 'type'):
            if n.expr.type not in ('integer', 'float'):
                error(f"Incremento no soportado para tipo '{n.expr.type}'", n.lineno)
            n.type = n.expr.type
    
    @multimethod
    def visit(self, n: PreDec, env: Symtab):
        """Pre-decremento --expr"""
        n.expr.accept(self, env)
        if hasattr(n.expr, 'type'):
            if n.expr.type not in ('integer', 'float'):
                error(f"Decremento no soportado para tipo '{n.expr.type}'", n.lineno)
            n.type = n.expr.type
    
    @multimethod
    def visit(self, n: PostInc, env: Symtab):
        """Post-incremento expr++"""
        n.expr.accept(self, env)
        if hasattr(n.expr, 'type'):
            if n.expr.type not in ('integer', 'float'):
                error(f"Incremento no soportado para tipo '{n.expr.type}'", n.lineno)
            n.type = n.expr.type
    
    @multimethod
    def visit(self, n: PostDec, env: Symtab):
        """Post-decremento expr--"""
        n.expr.accept(self, env)
        if hasattr(n.expr, 'type'):
            if n.expr.type not in ('integer', 'float'):
                error(f"Decremento no soportado para tipo '{n.expr.type}'", n.lineno)
            n.type = n.expr.type
    
    @multimethod
    def visit(self, n: Variable, env: Symtab):
        """Referencia a variable"""
        decl = env.get(n.name)
        if decl is None:
            error(f"Variable '{n.name}' no declarada", n.lineno)
            n.type = 'integer'  # tipo por defecto
        else:
            n.type = decl.type
    
    @multimethod
    def visit(self, n: ArrayAccess, env: Symtab):
        """Acceso a array"""
        decl = env.get(n.name)
        if decl is None:
            error(f"Array '{n.name}' no declarado", n.lineno)
            n.type = 'integer'
        elif not isinstance(decl, ArrayDeclaration):
            error(f"'{n.name}' no es un array", n.lineno)
            n.type = 'integer'
        else:
            n.type = decl.type
        
        # Verificar Indice
        n.index.accept(self, env)
        if hasattr(n.index, 'type') and n.index.type != 'integer':
            error(f"Indice de array debe ser integer, no '{n.index.type}'", n.lineno)
    
    @multimethod
    def visit(self, n: FunctionCall, env: Symtab):
        """Llamada a función"""
        decl = env.get(n.name)
        if decl is None:
            error(f"Función '{n.name}' no declarada", n.lineno)
            n.type = 'void'
        elif not isinstance(decl, FunctionDeclaration):
            error(f"'{n.name}' no es una función", n.lineno)
            n.type = 'void'
        else:
            n.type = decl.return_type
            
            # Verificar número de argumentos
            if len(n.args) != len(decl.params):
                error(f"Función '{n.name}' espera {len(decl.params)} argumentos, recibió {len(n.args)}", n.lineno)
            else:
                # Verificar tipos de argumentos
                for i, (arg, param) in enumerate(zip(n.args, decl.params)):
                    arg.accept(self, env)
                    if hasattr(arg, 'type') and arg.type != param.type:
                        error(f"Argumento {i+1} de '{n.name}': esperado '{param.type}', recibió '{arg.type}'", n.lineno)
        
    # ==================== LITERALS ====================
    
    @multimethod
    def visit(self, n: Integer, env: Symtab):
        n.type = 'integer'
    
    @multimethod
    def visit(self, n: Float, env: Symtab):
        n.type = 'float'
    
    @multimethod
    def visit(self, n: Char, env: Symtab):
        n.type = 'char'
    
    @multimethod
    def visit(self, n: String, env: Symtab):
        n.type = 'string'
    
    @multimethod
    def visit(self, n: Boolean, env: Symtab):
        n.type = 'boolean'
    
    @multimethod
    def visit(self, n: Program, env: Symtab):
        """Visitar programa completo"""
        for stmt in n.body:
            stmt.accept(self, env)


# Funcion helper para usar el checker
def check_program(ast):
    """Verifica semanticamente un programa"""
    return Check.checker(ast)