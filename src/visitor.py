# visitor.py

from rich.tree import Tree
from rich import print as rprint
from multimethod import multimethod

from model import *

# Opción 1: Usar Rich.Tree (no requiere instalación adicional)
class ASTTreePrinter(Visitor):
    def __init__(self):
        self.tree = None
    
    def visualize(self, node):
        self.tree = Tree("AST")
        node.accept(self, self.tree)
        rprint(self.tree)
        return self.tree
    
    @multimethod
    def visit(self, node: Program, tree: Tree):
        program_tree = tree.add("Program")
        for stmt in node.body:
            stmt.accept(self, program_tree)
    
    @multimethod
    def visit(self, node: Declaration, tree: Tree):
        decl_tree = tree.add(f"Declaration: {node.name}")
        decl_tree.add(f"Type: {node.type}")
        if node.value:
            node.value.accept(self, decl_tree)
    
    @multimethod
    def visit(self, node: WhileStmt, tree: Tree):
        while_tree = tree.add("WhileStmt")
        node.condition.accept(self, while_tree.add("Condition"))
        node.body.accept(self, while_tree.add("Body"))
    
    @multimethod
    def visit(self, node: DoWhileStmt, tree: Tree):
        do_tree = tree.add("DoWhileStmt")
        node.body.accept(self, do_tree.add("Body"))
        node.condition.accept(self, do_tree.add("Condition"))
    
    @multimethod
    def visit(self, node: PostInc, tree: Tree):
        inc_tree = tree.add("PostInc: ++")
        node.expr.accept(self, inc_tree)
    
    @multimethod
    def visit(self, node: PostDec, tree: Tree):
        dec_tree = tree.add("PostDec: --")
        node.expr.accept(self, dec_tree)
    
    @multimethod
    def visit(self, node: BinaryOp, tree: Tree):
        op_tree = tree.add(f"BinaryOp: {node.op}")
        node.left.accept(self, op_tree)
        node.right.accept(self, op_tree)
    
    @multimethod
    def visit(self, node: UnaryOp, tree: Tree):
        op_tree = tree.add(f"UnaryOp: {node.op}")
        node.expr.accept(self, op_tree)
    
    @multimethod
    def visit(self, node: Integer, tree: Tree):
        tree.add(f"Integer: {node.value}")
    
    @multimethod
    def visit(self, node: Float, tree: Tree):
        tree.add(f"Float: {node.value}")
    
    @multimethod
    def visit(self, node: Char, tree: Tree):
        tree.add(f"Char: '{node.value}'")
    
    @multimethod
    def visit(self, node: String, tree: Tree):
        tree.add(f"String: \"{node.value}\"")
    
    @multimethod
    def visit(self, node: Boolean, tree: Tree):
        tree.add(f"Boolean: {node.value}")
    
    @multimethod
    def visit(self, node: Variable, tree: Tree):
        tree.add(f"Variable: {node.name}")
    
    @multimethod
    def visit(self, node: ArrayAccess, tree: Tree):
        access_tree = tree.add(f"ArrayAccess: {node.name}")
        node.index.accept(self, access_tree)
    
    @multimethod
    def visit(self, node: FunctionCall, tree: Tree):
        call_tree = tree.add(f"FunctionCall: {node.name}")
        for arg in node.args:
            arg.accept(self, call_tree)
    
    @multimethod
    def visit(self, node: Assignment, tree: Tree):
        assign_tree = tree.add("Assignment")
        node.target.accept(self, assign_tree.add("Target"))
        node.value.accept(self, assign_tree.add("Value"))
    
    @multimethod
    def visit(self, node: ArrayDeclaration, tree: Tree):
        decl_tree = tree.add(f"ArrayDeclaration: {node.name}")
        decl_tree.add(f"Type: {node.type}")
        if node.size_expr:
            node.size_expr.accept(self, decl_tree.add("Size"))
        if node.values:
            values_tree = decl_tree.add("Values")
            for val in node.values:
                val.accept(self, values_tree)

    @multimethod
    def visit(self, node: FunctionDeclaration, tree: Tree):
        func_tree = tree.add(f"FunctionDeclaration: {node.name}")
        func_tree.add(f"ReturnType: {node.return_type}")
        if node.params:
            params_tree = func_tree.add("Parameters")
            for param in node.params:
                param.accept(self, params_tree)
        if node.body:
            body_tree = func_tree.add("Body")
            for stmt in node.body:
                stmt.accept(self, body_tree)

    @multimethod
    def visit(self, node: Param, tree: Tree):
        param_tree = tree.add(f"Param: {node.name}")
        param_tree.add(f"Type: {node.type}")
        if node.size_expr:
            node.size_expr.accept(self, param_tree)
    
    @multimethod
    def visit(self, node: IfStatement, tree: Tree):
        if_tree = tree.add("IfStatement")
        node.condition.accept(self, if_tree.add("Condition"))
        node.then_branch.accept(self, if_tree.add("Then"))
        if node.else_branch:
            node.else_branch.accept(self, if_tree.add("Else"))
    
    @multimethod
    def visit(self, node: ForStatement, tree: Tree):
        for_tree = tree.add("ForStatement")
        if node.init:
            node.init.accept(self, for_tree.add("Init"))
        if node.condition:
            node.condition.accept(self, for_tree.add("Condition"))
        if node.update:
            node.update.accept(self, for_tree.add("Update"))
        node.body.accept(self, for_tree.add("Body"))
    
    @multimethod
    def visit(self, node: PrintStatement, tree: Tree):
        print_tree = tree.add("PrintStatement")
        for expr in node.expressions:
            expr.accept(self, print_tree)
    
    @multimethod
    def visit(self, node: ReturnStatement, tree: Tree):
        return_tree = tree.add("ReturnStatement")
        if node.value:
            node.value.accept(self, return_tree)
    
    @multimethod
    def visit(self, node: BlockStatement, tree: Tree):
        block_tree = tree.add("BlockStatement")
        for stmt in node.statements:
            stmt.accept(self, block_tree)

if __name__ == '__main__':
    import sys
    from parser import parse

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python visitor.py <filename>")

    try:
        txt = open(sys.argv[1], encoding='utf-8').read()
        ast = parse(txt)
        
        if ast:
            # Usar Rich.Tree para visualización
            printer = ASTTreePrinter()
            printer.visualize(ast)
            print("\n=== AST generado exitosamente ===")
        else:
            print("Error: No se pudo parsear el archivo")
            
    except Exception as e:
        print(f"Error procesando el archivo: {e}")