from llvmlite import ir
from multimethod import multimethod

from model import (
    Visitor, Program, Declaration, FunctionDeclaration, PrintStatement,
    Integer, Float, Boolean, String, Variable,
    Assignment, BinaryOp, BlockStatement,
    IfStatement, ForStatement, WhileStmt, ReturnStatement,
    ArrayDeclaration, ArrayAccess,
    DoWhileStmt, UnaryOp, PreInc, PreDec, PostInc, PostDec,
    FunctionCall
)
from errors import error

I32 = ir.IntType(32)        # Entero de 32 bits (integer)
F64 = ir.DoubleType()       # Flotante de doble precision (float)
I1 = ir.IntType(1)          # Booleano de 1 bit (boolean)
I8 = ir.IntType(8)          # caracter de 8 bits (char)
VOID = ir.VoidType()        # Tipo void (sin valor de retorno)
I8_PTR = I8.as_pointer()    # Puntero a char (usado para strings)

# Mapeo de nombres de tipos del lenguaje fuente a tipos LLVM
_typemap = {
    'integer': I32, 
    'float': F64, 
    'boolean': I1,
    'char': I8, 
    'string': I8_PTR, 
    'void': VOID,
}

class LLVMCodegen(Visitor):
    
    def __init__(self):
        # inicializacion del generador de codigo LLVM
        self.module = ir.Module('bminor')
        self.module.triple = 'x86_64-pc-windows-msvc' 
        self.builder = None
        self.functions = {}
        self.locals = {}
        self.globals = {}
        self.global_strings = {}
        self.context_stack = []
        self.current_func = None

        # Funciones runtime predefinidas
        self.runtime = { 
            '_printi': ir.Function(self.module, ir.FunctionType(VOID, [I32]), name='_printi'),
            '_prints': ir.Function(self.module, ir.FunctionType(VOID, [I8_PTR]), name='_prints'),
            '_printb': ir.Function(self.module, ir.FunctionType(VOID, [I1]), name='_printb'),
            '_printf': ir.Function(self.module, ir.FunctionType(VOID, [F64]), name='_printf'),
            '_printc': ir.Function(self.module, ir.FunctionType(VOID, [I8]), name='_printc'),
        }

    def push_context(self):
        self.context_stack.append({
            'locals': self.locals.copy(),
            'builder': self.builder,
            'func': self.current_func
        })
        self.locals = {}

    def pop_context(self):
        if self.context_stack:
            ctx = self.context_stack.pop()
            self.locals = ctx['locals']
            self.builder = ctx['builder']
            self.current_func = ctx['func']

    def get_global_string(self, s: str):
        if s not in self.global_strings:
            arr = ir.Constant(
                ir.ArrayType(I8, len(s)+1),
                bytearray(s.encode('utf-8') + b'\0')
            )
            
            gv = ir.GlobalVariable(self.module, arr.type, f".str.{len(self.global_strings)}")
            gv.global_constant = True
            gv.initializer = arr
            
            self.global_strings[s] = gv
        
        return self.builder.bitcast(self.global_strings[s], I8_PTR)

    def infer_type(self, node):
        """Infiere el tipo de un nodo de expresión"""
        if isinstance(node, Integer):
            return 'integer'
        elif isinstance(node, Float):
            return 'float'
        elif isinstance(node, Boolean):
            return 'boolean'
        elif isinstance(node, String):
            return 'string'
        elif isinstance(node, Variable):
            # Buscar tipo de variable
            var_ptr = self.locals.get(node.name) or self.globals.get(node.name)
            if var_ptr:
                if var_ptr.type.pointee == I32:
                    return 'integer'
                elif var_ptr.type.pointee == F64:
                    return 'float'
                elif var_ptr.type.pointee == I1:
                    return 'boolean'
                elif var_ptr.type.pointee == I8:
                    return 'char'
            return 'integer'  # Default
        elif isinstance(node, BinaryOp):
            # Inferir tipo basado en operandos
            left_type = self.infer_type(node.left)
            right_type = self.infer_type(node.right)
            
            # Operadores de comparación siempre devuelven boolean
            if node.op in ['<', '<=', '>', '>=', '==', '!=']:
                return 'boolean'
            
            # Si alguno es float, el resultado es float
            if left_type == 'float' or right_type == 'float':
                return 'float'
            
            return 'integer'
        elif isinstance(node, FunctionCall):
            # Buscar tipo de retorno de función
            func = self.functions.get(node.name)
            if func:
                if func.return_value.type == I32:
                    return 'integer'
                elif func.return_value.type == F64:
                    return 'float'
                elif func.return_value.type == I8:
                    return 'char'
                elif func.return_value.type == I1:
                    return 'boolean'
            return 'integer'
        
        return 'integer'

    def cast_to_type(self, value, target_type):
        """Convierte un valor al tipo objetivo si es necesario"""
        current_type = value.type
        
        # Si ya es del tipo correcto, retornar
        if current_type == target_type:
            return value
        
        # Integer a Float
        if current_type == I32 and target_type == F64:
            return self.builder.sitofp(value, F64)
        
        # Float a Integer
        if current_type == F64 and target_type == I32:
            return self.builder.fptosi(value, I32)
        
        # Integer a Char
        if current_type == I32 and target_type == I8:
            return self.builder.trunc(value, I8)
        
        # Char a Integer
        if current_type == I8 and target_type == I32:
            return self.builder.sext(value, I32)
        
        return value

    @multimethod
    def visit(self, node: Program):
        # FASE 1: Procesar declaraciones globales (variables y arrays)
        for decl in node.body:
            if isinstance(decl, (Declaration, ArrayDeclaration)) and not isinstance(decl, FunctionDeclaration):
                self.process_global_declaration(decl)
        
        # FASE 2: Pre-declarar funciones
        for decl in node.body:
            if isinstance(decl, FunctionDeclaration):
                self.declare_function(decl)

        # FASE 3: Verificar que exista main()
        main_func = self.functions.get('main')
        if not main_func:
            error("No se encontro funcion main()")
            return str(self.module)

        # FASE 4: Implementar main() y otras funciones
        for decl in node.body:
            if isinstance(decl, FunctionDeclaration):
                self.current_func = self.functions[decl.name]
                entry = self.current_func.append_basic_block('entry')
                self.builder = ir.IRBuilder(entry)
                self.push_context()
                
                # Procesar parámetros
                for i, param in enumerate(decl.params):
                    alloca = self.builder.alloca(_typemap[param.type], name=param.name)
                    self.builder.store(self.current_func.args[i], alloca)
                    self.locals[param.name] = alloca
                
                # Procesar cuerpo
                for stmt in decl.body:
                    stmt.accept(self)
                
                # Asegurar terminador
                if not self.builder.block.is_terminated:
                    if self.current_func.return_value.type == VOID:
                        self.builder.ret_void()
                    else:
                        # Retornar valor por defecto
                        if self.current_func.return_value.type == I32:
                            self.builder.ret(ir.Constant(I32, 0))
                        elif self.current_func.return_value.type == F64:
                            self.builder.ret(ir.Constant(F64, 0.0))
                        elif self.current_func.return_value.type == I8:
                            self.builder.ret(ir.Constant(I8, 0))
                        else:
                            self.builder.ret_void()
                
                self.pop_context()

        return str(self.module)

    def process_global_declaration(self, node):
        """Procesa declaraciones globales de variables y arrays"""
        if isinstance(node, Declaration):
            ty = _typemap[node.type]
            
            gv = ir.GlobalVariable(self.module, ty, name=node.name)
            
            if node.value:
                if isinstance(node.value, Integer):
                    gv.initializer = ir.Constant(ty, node.value.value)
                elif isinstance(node.value, Boolean):
                    gv.initializer = ir.Constant(ty, 1 if node.value.value else 0)
                elif isinstance(node.value, Float):
                    gv.initializer = ir.Constant(ty, node.value.value)
                else:
                    gv.initializer = ir.Constant(ty, 0)
            else:
                if ty == F64:
                    gv.initializer = ir.Constant(ty, 0.0)
                else:
                    gv.initializer = ir.Constant(ty, 0)
            
            self.globals[node.name] = gv
            
        elif isinstance(node, ArrayDeclaration):
            elem_type = _typemap[node.type]
            
            if node.size_expr and isinstance(node.size_expr, Variable):
                if node.size_expr.name in self.globals:
                    size_var = self.globals[node.size_expr.name]
                    size = size_var.initializer.constant
                else:
                    size = 100
            elif node.size_expr and isinstance(node.size_expr, Integer):
                size = node.size_expr.value
            elif node.values:
                size = len(node.values)
            else:
                size = 100
            
            array_type = ir.ArrayType(elem_type, size)
            gv = ir.GlobalVariable(self.module, array_type, name=node.name)
            
            if node.values:
                init_values = []
                for val in node.values:
                    if isinstance(val, Integer):
                        init_values.append(ir.Constant(elem_type, val.value))
                    elif isinstance(val, Boolean):
                        init_values.append(ir.Constant(elem_type, 1 if val.value else 0))
                    elif isinstance(val, Float):
                        init_values.append(ir.Constant(elem_type, val.value))
                    else:
                        init_values.append(ir.Constant(elem_type, 0))
                gv.initializer = ir.Constant(array_type, init_values)
            else:
                if elem_type == F64:
                    gv.initializer = ir.Constant(array_type, [ir.Constant(elem_type, 0.0)] * size)
                else:
                    gv.initializer = ir.Constant(array_type, [ir.Constant(elem_type, 0)] * size)
            
            self.globals[node.name] = gv

    def declare_function(self, node: FunctionDeclaration):
        param_types = [_typemap.get(p.type, I32) for p in node.params]
        ret_type = _typemap.get(node.return_type, VOID)
        func_type = ir.FunctionType(ret_type, param_types)
        func = ir.Function(self.module, func_type, name=node.name)
        self.functions[node.name] = func

    @multimethod
    def visit(self, node: FunctionDeclaration):
        pass

    @multimethod
    def visit(self, node: Declaration):
        """Declaracion local de variable"""
        ty = _typemap[node.type]
        alloca = self.builder.alloca(ty, name=node.name)
        self.locals[node.name] = alloca
        
        if node.value:
            val = node.value.accept(self)
            # Realizar conversión de tipo si es necesario
            val = self.cast_to_type(val, ty)
            self.builder.store(val, alloca)
        else:
            # Inicializar con valor por defecto
            if ty == F64:
                self.builder.store(ir.Constant(ty, 0.0), alloca)
            else:
                self.builder.store(ir.Constant(ty, 0), alloca)

    @multimethod
    def visit(self, node: ArrayDeclaration):
        """Declaracion local de array"""
        elem_type = _typemap[node.type]
        size = 100
        
        if node.size_expr:
            size_val = node.size_expr.accept(self)
            if isinstance(size_val, ir.Constant):
                size = size_val.constant
        elif node.values:
            size = len(node.values)
        
        array_type = ir.ArrayType(elem_type, size)
        alloca = self.builder.alloca(array_type, name=node.name)
        self.locals[node.name] = alloca
        
        # Inicializar
        if elem_type == F64:
            zero = ir.Constant(elem_type, 0.0)
        else:
            zero = ir.Constant(elem_type, 0)
            
        for i in range(size):
            ptr = self.builder.gep(
                alloca, 
                [ir.Constant(I32, 0), ir.Constant(I32, i)]
            )
            self.builder.store(zero, ptr)

    @multimethod
    def visit(self, node: ArrayAccess):
        """Acceso a elemento de array"""
        array_ptr = self.locals.get(node.name)
        if not array_ptr:
            array_ptr = self.globals.get(node.name)
        
        if not array_ptr:
            error(f"Array no declarado: {node.name}")
            return ir.Constant(I32, 0)
        
        index = node.index.accept(self)
        ptr = self.builder.gep(array_ptr, [ir.Constant(I32, 0), index])
        return self.builder.load(ptr)

    @multimethod
    def visit(self, node: PrintStatement):
        """Statement de impresion"""
        for expr in node.expressions:
            val = expr.accept(self)
            
            # Inferir tipo de expresión
            expr_type = self.infer_type(expr)
            
            if expr_type == 'integer':
                val = self.cast_to_type(val, I32)
                self.builder.call(self.runtime['_printi'], [val])
            elif expr_type == 'boolean':
                val = self.cast_to_type(val, I1)
                self.builder.call(self.runtime['_printb'], [val])
            elif expr_type == 'float':
                val = self.cast_to_type(val, F64)
                self.builder.call(self.runtime['_printf'], [val])
            elif expr_type == 'char':
                val = self.cast_to_type(val, I8)
                self.builder.call(self.runtime['_printc'], [val])
            elif expr_type == 'string' or isinstance(expr, String):
                if not isinstance(val.type, ir.PointerType):
                    val = self.get_global_string(str(expr.value))
                self.builder.call(self.runtime['_prints'], [val])

    @multimethod
    def visit(self, node: WhileStmt):
        cond_bb = self.builder.append_basic_block('while_cond')
        body_bb = self.builder.append_basic_block('while_body')
        end_bb = self.builder.append_basic_block('while_end')

        self.builder.branch(cond_bb)
        
        self.builder.position_at_end(cond_bb)
        cond_val = node.condition.accept(self)
        cond_val = self.cast_to_type(cond_val, I1)
        self.builder.cbranch(cond_val, body_bb, end_bb)

        self.builder.position_at_end(body_bb)
        node.body.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_bb)

        self.builder.position_at_end(end_bb)

    @multimethod
    def visit(self, node: DoWhileStmt):
        body_bb = self.builder.append_basic_block('do_body')
        cond_bb = self.builder.append_basic_block('do_cond')
        end_bb = self.builder.append_basic_block('do_end')
        
        self.builder.branch(body_bb)
        
        self.builder.position_at_end(body_bb)
        node.body.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_bb)
        
        self.builder.position_at_end(cond_bb)
        cond_val = node.condition.accept(self)
        cond_val = self.cast_to_type(cond_val, I1)
        self.builder.cbranch(cond_val, body_bb, end_bb)
        
        self.builder.position_at_end(end_bb)

    @multimethod
    def visit(self, node: IfStatement):
        then_bb = self.builder.append_basic_block('if_then')
        else_bb = self.builder.append_basic_block('if_else')
        end_bb = self.builder.append_basic_block('if_end')
        
        cond_val = node.condition.accept(self)
        cond_val = self.cast_to_type(cond_val, I1)
        
        if node.else_branch:
            self.builder.cbranch(cond_val, then_bb, else_bb)
        else:
            self.builder.cbranch(cond_val, then_bb, end_bb)
        
        self.builder.position_at_end(then_bb)
        node.then_branch.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(end_bb)
        
        if node.else_branch:
            self.builder.position_at_end(else_bb)
            node.else_branch.accept(self)
            if not self.builder.block.is_terminated:
                self.builder.branch(end_bb)
        else:
            self.builder.position_at_end(else_bb)
            self.builder.branch(end_bb)
        
        self.builder.position_at_end(end_bb)

    @multimethod
    def visit(self, node: ForStatement):
        if node.init:
            node.init.accept(self)
        
        cond_bb = self.builder.append_basic_block('for_cond')
        body_bb = self.builder.append_basic_block('for_body')
        update_bb = self.builder.append_basic_block('for_update')
        end_bb = self.builder.append_basic_block('for_end')
        
        self.builder.branch(cond_bb)
        
        self.builder.position_at_end(cond_bb)
        if node.condition:
            cond_val = node.condition.accept(self)
            cond_val = self.cast_to_type(cond_val, I1)
            self.builder.cbranch(cond_val, body_bb, end_bb)
        else:
            self.builder.branch(body_bb)
        
        self.builder.position_at_end(body_bb)
        node.body.accept(self)
        if not self.builder.block.is_terminated:
            self.builder.branch(update_bb)
        
        self.builder.position_at_end(update_bb)
        if node.update:
            node.update.accept(self)
        self.builder.branch(cond_bb)
        
        self.builder.position_at_end(end_bb)

    @multimethod
    def visit(self, node: ReturnStatement):
        if node.value:
            val = node.value.accept(self)
            # Convertir al tipo de retorno de la función
            expected_type = self.current_func.return_value.type
            val = self.cast_to_type(val, expected_type)
            self.builder.ret(val)
        else:
            self.builder.ret_void()

    @multimethod
    def visit(self, node: BlockStatement):
        for stmt in node.statements:
            stmt.accept(self)

    @multimethod
    def visit(self, node: Assignment):
        if isinstance(node.target, Variable):
            val = node.value.accept(self)
            
            alloca = self.locals.get(node.target.name)
            if not alloca:
                alloca = self.globals.get(node.target.name)
            
            if alloca:
                # Convertir al tipo de la variable
                target_type = alloca.type.pointee
                val = self.cast_to_type(val, target_type)
                self.builder.store(val, alloca)
            
        elif isinstance(node.target, ArrayAccess):
            val = node.value.accept(self)
            
            array_ptr = self.locals.get(node.target.name)
            if not array_ptr:
                array_ptr = self.globals.get(node.target.name)
            
            if array_ptr:
                index = node.target.index.accept(self)
                ptr = self.builder.gep(array_ptr, [ir.Constant(I32, 0), index])
                # Convertir al tipo del array
                target_type = ptr.type.pointee
                val = self.cast_to_type(val, target_type)
                self.builder.store(val, ptr)

    @multimethod
    def visit(self, node: BinaryOp):
        left = node.left.accept(self)
        right = node.right.accept(self)
        
        # Determinar si alguno es float
        left_is_float = left.type == F64
        right_is_float = right.type == F64
        is_float_op = left_is_float or right_is_float
        
        # Promover a float si es necesario
        if is_float_op:
            left = self.cast_to_type(left, F64)
            right = self.cast_to_type(right, F64)
        
        # Operaciones aritméticas
        if node.op == '+':
            return self.builder.fadd(left, right) if is_float_op else self.builder.add(left, right)
        if node.op == '-':
            return self.builder.fsub(left, right) if is_float_op else self.builder.sub(left, right)
        if node.op == '*':
            return self.builder.fmul(left, right) if is_float_op else self.builder.mul(left, right)
        if node.op == '/':
            return self.builder.fdiv(left, right) if is_float_op else self.builder.sdiv(left, right)
        if node.op == '%':
            return self.builder.srem(left, right)  # Solo para enteros
        
        # Operaciones de comparación
        if is_float_op:
            if node.op == '<': return self.builder.fcmp_ordered('<', left, right)
            if node.op == '<=': return self.builder.fcmp_ordered('<=', left, right)
            if node.op == '>': return self.builder.fcmp_ordered('>', left, right)
            if node.op == '>=': return self.builder.fcmp_ordered('>=', left, right)
            if node.op == '==': return self.builder.fcmp_ordered('==', left, right)
            if node.op == '!=': return self.builder.fcmp_ordered('!=', left, right)
        else:
            if node.op == '<': return self.builder.icmp_signed('<', left, right)
            if node.op == '<=': return self.builder.icmp_signed('<=', left, right)
            if node.op == '>': return self.builder.icmp_signed('>', left, right)
            if node.op == '>=': return self.builder.icmp_signed('>=', left, right)
            if node.op == '==': return self.builder.icmp_signed('==', left, right)
            if node.op == '!=': return self.builder.icmp_signed('!=', left, right)
        
        # Operaciones lógicas
        if node.op == '&&': return self.builder.and_(left, right)
        if node.op == '||': return self.builder.or_(left, right)
        
        return ir.Constant(I1, 0)

    @multimethod
    def visit(self, node: UnaryOp):
        expr_val = node.expr.accept(self)
        
        if node.op == '-':
            if expr_val.type == F64:
                return self.builder.fneg(expr_val)
            else:
                return self.builder.neg(expr_val)
        elif node.op == '!':
            return self.builder.not_(expr_val)
        
        return expr_val

    @multimethod
    def visit(self, node: PreInc):
        var_ptr = self.locals.get(node.expr.name) or self.globals.get(node.expr.name)
        if var_ptr:
            old_val = self.builder.load(var_ptr)
            if old_val.type == F64:
                new_val = self.builder.fadd(old_val, ir.Constant(F64, 1.0))
            else:
                new_val = self.builder.add(old_val, ir.Constant(I32, 1))
            self.builder.store(new_val, var_ptr)
            return new_val
        return ir.Constant(I32, 0)

    @multimethod
    def visit(self, node: PreDec):
        var_ptr = self.locals.get(node.expr.name) or self.globals.get(node.expr.name)
        if var_ptr:
            old_val = self.builder.load(var_ptr)
            if old_val.type == F64:
                new_val = self.builder.fsub(old_val, ir.Constant(F64, 1.0))
            else:
                new_val = self.builder.sub(old_val, ir.Constant(I32, 1))
            self.builder.store(new_val, var_ptr)
            return new_val
        return ir.Constant(I32, 0)

    @multimethod
    def visit(self, node: PostInc):
        var_ptr = self.locals.get(node.expr.name) or self.globals.get(node.expr.name)
        if var_ptr:
            old_val = self.builder.load(var_ptr)
            if old_val.type == F64:
                new_val = self.builder.fadd(old_val, ir.Constant(F64, 1.0))
            else:
                new_val = self.builder.add(old_val, ir.Constant(I32, 1))
            self.builder.store(new_val, var_ptr)
            return old_val
        return ir.Constant(I32, 0)

    @multimethod
    def visit(self, node: PostDec):
        var_ptr = self.locals.get(node.expr.name) or self.globals.get(node.expr.name)
        if var_ptr:
            old_val = self.builder.load(var_ptr)
            if old_val.type == F64:
                new_val = self.builder.fsub(old_val, ir.Constant(F64, 1.0))
            else:
                new_val = self.builder.sub(old_val, ir.Constant(I32, 1))
            self.builder.store(new_val, var_ptr)
            return old_val
        return ir.Constant(I32, 0)

    @multimethod
    def visit(self, node: Integer):
        return ir.Constant(I32, node.value)
    
    @multimethod
    def visit(self, node: Boolean):
        return ir.Constant(I1, 1 if node.value else 0)
    
    @multimethod
    def visit(self, node: Float):
        return ir.Constant(F64, node.value)
    
    @multimethod
    def visit(self, node: String):
        return self.get_global_string(node.value)
    
    @multimethod
    def visit(self, node: Variable):
        var_ptr = self.locals.get(node.name)
        if not var_ptr:
            var_ptr = self.globals.get(node.name)
        
        if not var_ptr:
            error(f"Variable no declarada: {node.name}")
            return ir.Constant(I32, 0)
        
        return self.builder.load(var_ptr)

    @multimethod
    def visit(self, node: FunctionCall):
        """Llamada a función"""
        func = self.functions.get(node.name)
        if not func:
            error(f"Función no declarada: {node.name}")
            return ir.Constant(I32, 0)
        
        # Evaluar argumentos y convertir tipos si es necesario
        args = []
        for i, arg in enumerate(node.args):
            arg_val = arg.accept(self)
            # Convertir al tipo esperado por el parámetro
            if i < len(func.args):
                expected_type = func.args[i].type
                arg_val = self.cast_to_type(arg_val, expected_type)
            args.append(arg_val)
        
        return self.builder.call(func, args)


def generate_program(ast):
    gen = LLVMCodegen()
    return gen.visit(ast)