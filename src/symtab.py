# symtab.py
from rich.table import Table
from rich.console import Console
from rich import print

from model import Node

class Symtab:
	class SymbolDefinedError(Exception):
		pass
		
	class SymbolConflictError(Exception):
		pass
		
	def __init__(self, name, parent=None):
		self.name = name
		self.entries = {}
		self.parent = parent
		if self.parent:
			self.parent.children.append(self)
		self.children = []

	def __getitem__(self, name):
		return self.entries[name]

	def __setitem__(self, name, value):
		self.entries[name] = value

	def __delitem__(self, name):
		del self.entries[name]

	def __contains__(self, name):
		if name in self.entries:
			return self.entries[name]
		return False

	def add(self, name, value):
		'''
		Agrega un simbol con el valor dado a la tabla de simbolos.
		El valor suele ser un nodo AST que representa la declaración
		o definición de una función, variable (por ejemplo, Declaración
		o FuncDeclaration)
		'''
		if name in self.entries:
			if self.entries[name].type != value.type:
				raise Symtab.SymbolConflictError()
			else:
				raise Symtab.SymbolDefinedError()
		self.entries[name] = value
		
	def get(self, name):
		'''
		Recupera el símbol con el nombre dado de la tabla de
		simbol, recorriendo hacia arriba a traves de las tablas
		de simbol principales si no se encuentra en la actual.
		'''
		if name in self.entries:
			return self.entries[name]
		elif self.parent:
			return self.parent.get(name)
		return None
		
	def print(self):
		# Solo mostrar tablas con contenido
		if self.entries:
			table = Table(title = f"Symbol Table: '{self.name}'")
			table.add_column('key', style='cyan')
			table.add_column('value', style='bright_green')
			
			for k,v in self.entries.items():
				value = f"{v.__class__.__name__}({v.name})" if isinstance(v, Node) else f"{v}"
				table.add_row(k, value)
			print(table, '\n')
		
		# Imprimir hijos recursivamente
		for child in self.children:
			child.print()