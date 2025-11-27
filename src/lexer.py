# lexer.py
# Analizador Léxico para el lenguaje B-Minor 

import sly
import re
import sys
import os
import glob

class Lexer(sly.Lexer):
    def __init__(self):
        self.has_errors = False
    
    # Define los tokens reconocidos por el analizador léxico
    tokens = {
        # PALABRAS RESERVADAS
        ARRAY, AUTO, BOOLEAN, BREAK, CHAR, CONTINUE, DO, ELSE, FALSE, 
        FLOAT, FOR, FUNCTION, IF, INTEGER, PRINT, RETURN, STRING, 
        TRUE, VOID, WHILE,
        
        # OPERACIONES MATEMATICAS Y EXPRESIONES REGULARES
        IGUAL, NO_IGUAL, MENOR_IGUAL, MENOR_QUE, MAYOR_IGUAL, MAYOR_QUE,            # = != <= < >= >
        AND, OR, NOT,         # && || !
        
        # NUEVOS TOKENS PARA OPERADORES
        INC, DEC,  # Agregar estos

        # CONSTANTES E IDENTIFICADOR
        INTEGER_CONST, FLOAT_CONST, CHAR_CONST, STRING_CONST, ID
    }
    
    # Ignora espacios, tabulaciones y retornos de carro
    ignore = ' \t\r'

    # Define el mapeo de palabras reservadas a sus tokens correspondientes
    keywords = {
        'array': ARRAY,
        'auto': AUTO,
        'boolean': BOOLEAN,
        'break': BREAK,
        'char': CHAR,
        'continue': CONTINUE,
        'do': DO,
        'else': ELSE,
        'false': FALSE,
        'float': FLOAT,
        'for': FOR,
        'function': FUNCTION,
        'if': IF,
        'integer': INTEGER,
        'print': PRINT,
        'return': RETURN,
        'string': STRING,
        'true': TRUE,
        'void': VOID,
        'while': WHILE
    }

    # ==================== 1. REGLAS DE OPERADORES MULTI-CARÁCTER ====================
    @_(r'\+\+')
    def INC(self, t):
        return t

    @_(r'--')
    def DEC(self, t):
        return t

    @_(r'==')
    def IGUAL(self, t):
        return t
    
    @_(r'!=')
    def NO_IGUAL(self, t):
        return t
    
    @_(r'<=')  
    def MENOR_IGUAL(self, t):
        return t

    @_(r'>=')
    def MAYOR_IGUAL(self, t):
        return t
    
    @_(r'<')
    def MENOR_QUE(self, t):
        return t
    
    @_(r'>')
    def MAYOR_QUE(self, t):
        return t

    @_(r'&&')
    def AND(self, t):
        return t

    @_(r'\|\|')
    def OR(self, t):
        return t

    @_(r'!')
    def NOT(self, t):
        return t

    # ==================== 2. REGLAS DE ERRORES Y MANEJO ESPECIAL ====================
    @_(r'=>')
    def INVALID_LE(self, t):
        print(f"Linea {self.lineno}: Error léxico - Operador inválido '=>' (usa '>=')")
        self.index += len(t.value)
        self.has_errors = True
        return None
    
    @_(r'=<')
    def INVALID_LE_REV(self, t):
        print(f"Linea {self.lineno}: Error léxico - Operador inválido '=<' (usa '<=')")
        self.index += len(t.value)
        self.has_errors = True
        return None

    @_(r'=!')
    def INVALID_NE(self, t):
        print(f"Linea {self.lineno}: Error léxico - Operador inválido '=!' (usa '!=')")
        self.index += len(t.value)
        self.has_errors = True
        return None

    @_(r'&(?!&)')
    def INVALID_AND(self, t):
        print(f"Linea {self.lineno}: Error léxico - Operador '&' no soportado (usa '&&')")
        self.index += len(t.value)
        self.has_errors = True
        return None
    
    @_(r'\|(?!\|)')
    def INVALID_OR(self, t):
        print(f"Linea {self.lineno}: Error léxico - Operador '|' no soportado (usa '||')")
        self.index += len(t.value)
        self.has_errors = True
        return None

    @_(r'<>')
    def INVALID_NOT(self, t):
        print(f"Linea {self.lineno}: Error léxico - Operador inválido '<>' (usa '!=' para desigualdad)")
        self.index += len(t.value)
        self.has_errors = True
        return None

    @_(r'\d+[a-zA-Z_][a-zA-Z0-9_]*')
    def INVALID_ID(self, t):
        print(f"Linea {self.lineno}: Error léxico - Identificador '{t.value}' no puede comenzar con número")
        self.index += len(t.value)
        self.has_errors = True
        return None

    # ==================== 3. REGLAS DE COMENTARIOS ====================
    @_(r'//.*')
    def ignore_comment(self, t):
        pass

    @_(r'/\*(.|\n)*?\*/')
    def ignore_block_comment(self, t):
        self.lineno += t.value.count('\n')

    @_(r'/\*(.|\n)*?\* /')
    def INVALID_COMMENT(self, t):
        print(f"Linea {self.lineno}: Error léxico - Comentario mal formado (espacio entre '*' y '/')")
        self.index += len(t.value)
        self.has_errors = True
        return None

    @_(r'/\*(.|\n)*')
    def UNCLOSED_COMMENT(self, t):
        print(f"Linea {self.lineno}: Error léxico - Comentario no cerrado")
        self.index += len(t.value)
        self.has_errors = True
        return None
    
    @_(r'\*/')
    def INVALID_COMMENT_CLOSE(self, t):
        print(f"Linea {self.lineno}: Error léxico - Comentario cerrado sin abrir")
        self.index += len(t.value)
        self.has_errors = True
        return None

    @_(r'#.*')
    def ignore_hash_comment(self, t):
        pass

    # ==================== 4. REGLAS DE IDENTIFICADORES ====================
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'  
    
    def ID(self, t):
        if len(t.value) > 32:
            print(f"Linea {self.lineno}: Error léxico - Identificador '{t.value[:32]}...' excede el límite de 32 caracteres")
            self.index += len(t.value)
            self.has_errors = True
            return None
            
        t.type = self.keywords.get(t.value, 'ID')  
        return t

    # ==================== 5. REGLAS DE CONSTANTES ====================
    @_(r"'(\\['\\nrt0]|[^\\'])'")
    def CHAR_CONST(self, t):
        char_content = t.value[1:-1]
        
        if char_content.startswith('\\'):
            escape_map = {
                "'": "'", "\\": "\\", "n": "\n", 
                "r": "\r", "t": "\t", "0": "\0"
            }
            if char_content[1] in escape_map:
                t.value = escape_map[char_content[1]]
            else:
                print(f"Linea {self.lineno}: Error léxico - Secuencia de escape inválida: '{char_content}'")
                self.has_errors = True
                return None
        else:
            t.value = char_content
        
        return t
    
    @_(r"'[^']*'")
    def CHAR_ERROR(self, t):
        if len(t.value) == 1:
            print(f"Linea {self.lineno}: Error léxico - CHAR inválido: comilla simple sin cerrar")
            self.index += 1
            self.has_errors = True
            return None
        elif t.value.count("'") < 2:
            print(f"Linea {self.lineno}: Error léxico - CHAR inválido: comilla simple sin cerrar")
            self.index += len(t.value)
            self.has_errors = True
            return None
        else:
            print(f"Linea {self.lineno}: Error léxico - CHAR inválido: '{t.value}' (múltiples caracteres)")
            self.index += len(t.value)
            self.has_errors = True
            return None

    @_(r'\d+\.\d*([eE][+-]?\d+)?|\d*\.\d+([eE][+-]?\d+)?|\d+[eE][+-]?\d+')
    def FLOAT_CONST(self, t):
        if re.search(r'[a-df-zA-DF-Z]', t.value):
            print(f"Linea {self.lineno}: Error léxico - Literal flotante inválido: '{t.value}' (solo se permite 'e' para exponente)")
            self.index += len(t.value)
            self.has_errors = True
            return None
            
        if t.value.endswith('.') or (t.value.startswith('.') and not re.search(r'\.\d', t.value)):
            print(f"Linea {self.lineno}: Error léxico - Literal flotante inválido: '{t.value}' (punto decimal sin dígitos)")
            self.index += len(t.value)
            self.has_errors = True
            return None
            
        try:
            t.value = float(t.value)
        except ValueError:
            print(f"Linea {self.lineno}: Error léxico - Literal flotante inválido: '{t.value}'")
            self.index += len(t.value)
            self.has_errors = True
            return None
        return t

    @_(r'\d+')
    def INTEGER_CONST(self, t):
        next_char = self.text[self.index] if self.index < len(self.text) else None
        if next_char == '.':
            remaining_text = self.text[self.index:]
            match = re.match(r'\.\d*([eE][+-]?\d+)?', remaining_text)
            if match:
                float_value = t.value + match.group()
                
                if re.search(r'[a-df-zA-DF-Z]', float_value):
                    print(f"Linea {self.lineno}: Error léxico - Literal flotante inválido: '{float_value}' (solo se permite 'e' para exponente)")
                    self.index += len(match.group())
                    self.has_errors = True
                    return None
                
                self.index += len(match.group())
                try:
                    return sly.LexToken('FLOAT_CONST', float(float_value), t.lineno)
                except ValueError:
                    print(f"Linea {self.lineno}: Error léxico - Literal flotante inválido: '{float_value}'")
                    self.index += len(float_value)
                    self.has_errors = True
                    return None
        
        t.value = int(t.value)
        return t
    
    @_(r'"(\\.|[^\\"])*"')
    def STRING_CONST(self, t):
        s = t.value[1:-1]
        
        escapes = {
            'n': '\n', 't': '\t', 'r': '\r', '0': '\0',
            '"': '"', "'": "'", '\\': '\\'
        }
        
        result = []
        i = 0
        while i < len(s):
            if s[i] == '\\':
                if i+1 < len(s):
                    esc = s[i+1]
                    if esc in escapes:
                        result.append(escapes[esc])
                    else:
                        print(f"Linea {self.lineno}: Error léxico - Secuencia de escape desconocida '\\{esc}'")
                        self.index += len(t.value)
                        self.has_errors = True
                        return None
                    i += 2
                else:
                    print(f"Linea {self.lineno}: Error léxico - Secuencia de escape incompleta al final del string")
                    self.index += len(t.value)
                    self.has_errors = True
                    return None
            else:
                result.append(s[i])
                i += 1
        
        t.value = ''.join(result)
        return t
    
    @_(r'"[^"]*')
    def STRING_ERROR(self, t):
        if t.value.count('"') < 1:
            print(f"Linea {self.lineno}: Error léxico - STRING inválido: comilla doble sin cerrar")
            self.index += len(t.value)
            self.has_errors = True
            return None

    # ==================== 6. LITERALES (DEBE IR AL FINAL) ====================
    literals = '+-*/%^=()[]{}:;,'
    
    # ==================== 7. MANEJO DE ERRORES Y NEWLINES ====================
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')
        
    def error(self, t):
        if t.value[0].isdigit():
            match = re.match(r'\d+[a-zA-Z_][a-zA-Z0-9_]*', t.value)
            if match:
                invalid_id = match.group()
                print(f"Linea {self.lineno}: Error léxico - Identificador '{invalid_id}' no puede comenzar con número")
                self.index += len(invalid_id)
                self.has_errors = True
                return None

        if hasattr(t, 'value') and t.value:
            error_char = t.value[0] if len(t.value) > 0 else t.value
        else:
            error_char = t.value if t.value else 'EOF'

        print(f"Linea {self.lineno}: Error léxico - Caracter no permitido: '{error_char}'")
        self.index += 1
        self.has_errors = True
        return None

# ==================== FUNCIONES DE USUARIO ====================
def tokenize(source_code):
    lexer = Lexer()
    lexer.has_errors = False
    tokens = []
    print("Linea \t\t Tipo \t\t\t Valor\n")
    try:
        for tok in lexer.tokenize(source_code):
            if tok is not None:
                print(f"Linea {tok.lineno} | {tok.type:20} | {tok.value}")
                tokens.append(tok)
        return tokens, lexer.has_errors
    except Exception as e:
        print(f"Error durante el análisis léxico: {e}")
        return None, True

def analyze_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            source = file.read()
            print(f"\n=== Analizando {filename} ===\n")
            tokens, has_errors = tokenize(source)
            if tokens is not None:
                if has_errors:
                    print(f"\n=== Análisis de {filename} terminó con errores ===")
                    return False
                else:
                    print(f"\n=== Análisis completado de {filename} ===")
                    return True
            else:
                print(f"\n=== Análisis de {filename} terminó con errores ===")
                return False
    except Exception as e:
        print(f"Error al abrir o procesar el archivo {filename}: {e}")
        return False

def analyze_folder(folder_path):
    pattern = os.path.join(folder_path, "*.bminor")
    files = glob.glob(pattern)
    pattern2 = os.path.join(folder_path, "*.bminor.c++")
    files.extend(glob.glob(pattern2))
    
    if not files:
        print(f"No se encontraron archivos .bminor o .bminor.c++ en {folder_path}")
        return
    
    print(f"=== ANALIZANDO ARCHIVOS EN {folder_path} ===\n")
    
    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"--- Analizando {filename} ---")
        try:
            success = analyze_file(file_path)
            
            if "bad" in filename:
                expected_result = "debería tener errores"
                actual_result = "tuvo errores" if not success else "no tuvo errores"
                status = "✓" if not success else "✗"
                print(f"{status} {filename} {expected_result} y {actual_result}")
            else:
                expected_result = "debería ser correcto"
                actual_result = "fue correcto" if success else "tuvo errores"
                status = "✓" if success else "✗"
                print(f"{status} {filename} {expected_result} y {actual_result}")
            
            print("-" * 50 + "\n")
        except Exception as e:
            print(f"Error procesando {filename}: {e}")
            print("-" * 50 + "\n")
            continue

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python bminor.py --scan <archivo>")
        print("      python bminor.py --scan-all <carpeta>")
        print("\nEjemplos:")
        print("  python bminor.py --scan pruebas/scanner/good1.bminor.c++")
        print("  python bminor.py --scan-all pruebas/scanner/")
        sys.exit(1)

    command = sys.argv[1]
    
    if command == '--scan' and len(sys.argv) == 3:
        file_path = sys.argv[2]
        analyze_file(file_path)
    elif command == '--scan-all' and len(sys.argv) == 3:
        folder_path = sys.argv[2]
        analyze_folder(folder_path)
    else:
        print("Comandos válidos:")
        print("  --scan <archivo>    : Analiza un archivo específico")
        print("  --scan-all <carpeta>: Analiza todos los archivos .bminor.c++ en una carpeta")
        print("\nEjemplos:")
        print("  python bminor.py --scan test/scanner/good1.bminor")
        print("  python bminor.py --scan-all test/scanner/")