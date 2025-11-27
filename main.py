# main.py - Compilador B-Minor con visualización de todas las fases
import sys
import os

# Añade src/ al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rich import print
from rich.panel import Panel
from rich.console import Console

from src.lexer import Lexer
from src.parser import parse
from src.checker import check_program
from src.visitor import ASTTreePrinter
from src.llvm import generate_program
from src.interp import interpret_program, BminorExit
from src.model import *
from src.errors import errors_detected, clear_errors

console = Console()

def esperar_enter(mensaje="Presiona ENTER para continuar..."):
    """Espera a que el usuario presione ENTER"""
    console.print(f"\n[bold yellow]{mensaje}[/bold yellow]")
    input()

def mostrar_separador(titulo):
    """Muestra un separador visual entre fases"""
    console.print("\n" + "="*80)
    console.print(f"[bold cyan]{titulo.center(80)}[/bold cyan]")
    console.print("="*80 + "\n")

def fase_1_analisis_lexico(source):
    """FASE 1: Análisis Léxico (Lexer)"""
    mostrar_separador("FASE 1: ANÁLISIS LÉXICO (LEXER)")
    
    console.print("[bold]Tokenizando el código fuente...[/bold]\n")
    
    lexer = Lexer()
    tokens = []
    
    try:
        console.print("[cyan]Linea \t\t Tipo \t\t\t Valor[/cyan]")
        console.print("-" * 80)
        
        for tok in lexer.tokenize(source):
            if tok is not None:
                console.print(f"Linea {tok.lineno:3} | {tok.type:20} | {tok.value}")
                tokens.append(tok)
        
        if lexer.has_errors:
            console.print(f"\n[bold red]✗ Análisis léxico completado con errores[/bold red]")
            return None, True
        else:
            console.print(f"\n[bold green]✓ Análisis léxico exitoso - {len(tokens)} tokens generados[/bold green]")
            return tokens, False
            
    except Exception as e:
        console.print(f"\n[bold red]Error durante el análisis léxico: {e}[/bold red]")
        return None, True

def fase_2_analisis_sintactico(source):
    """FASE 2: Análisis Sintáctico (Parser)"""
    mostrar_separador("FASE 2: ANÁLISIS SINTÁCTICO (PARSER)")
    
    console.print("[bold]Generando el Árbol de Sintaxis Abstracta (AST)...[/bold]\n")
    
    try:
        clear_errors()
        ast = parse(source)
        
        if not ast:
            console.print("[bold red]✗ Error de sintaxis - No se pudo generar el AST[/bold red]")
            return None
        
        if errors_detected():
            console.print(f"[bold red]✗ Análisis sintáctico con {errors_detected()} errores[/bold red]")
            return None
        
        console.print("[bold green]✓ AST generado exitosamente[/bold green]\n")
        
        # Visualizar el AST
        console.print("[bold]Estructura del AST:[/bold]")
        printer = ASTTreePrinter()
        printer.visualize(ast)
        
        return ast
        
    except Exception as e:
        console.print(f"[bold red]Error durante el análisis sintáctico: {e}[/bold red]")
        return None

def fase_3_analisis_semantico(ast):
    """FASE 3: Análisis Semántico (Checker)"""
    mostrar_separador("FASE 3: ANÁLISIS SEMÁNTICO (CHECKER)")
    
    console.print("[bold]Verificando tipos y semántica del programa...[/bold]\n")
    
    try:
        clear_errors()
        env = check_program(ast)
        
        if errors_detected():
            console.print(f"[bold red]✗ Análisis semántico con {errors_detected()} errores[/bold red]")
            return None
        
        console.print("[bold green]✓ Verificación semántica exitosa[/bold green]\n")
        
        # Mostrar tabla de símbolos
        console.print("[bold]Tabla de Símbolos:[/bold]")
        env.print()
        
        return env
        
    except Exception as e:
        console.print(f"[bold red]Error durante el análisis semántico: {e}[/bold red]")
        return None

def fase_4_generacion_codigo(ast):
    """FASE 4: Generación de Código LLVM IR"""
    mostrar_separador("FASE 4: GENERACIÓN DE CÓDIGO LLVM IR")
    
    console.print("[bold]Generando código intermedio LLVM...[/bold]\n")
    
    try:
        ir_code = generate_program(ast)
        
        # Guardar en archivo
        with open('out.ll', 'w', encoding='utf-8') as f:
            f.write(ir_code)
        
        console.print("[bold green]✓ Código LLVM IR generado exitosamente → out.ll[/bold green]\n")
        
        # Mostrar el código generado (primeras 50 líneas)
        console.print("[bold]Código LLVM IR generado (primeras líneas):[/bold]")
        lines = ir_code.split('\n')
        preview = '\n'.join(lines[:50])
        if len(lines) > 50:
            preview += f"\n... ({len(lines) - 50} líneas más)"
        console.print(Panel(preview, title="out.ll", border_style="cyan"))
        
        return ir_code
        
    except Exception as e:
        console.print(f"[bold red]Error durante la generación de código: {e}[/bold red]")
        return None

def fase_5_interpretacion(ast):
    """FASE 5: Interpretación del programa"""
    mostrar_separador("FASE 5: INTERPRETACIÓN DEL PROGRAMA")
    
    console.print("[bold]Ejecutando el programa...[/bold]\n")
    console.print("[cyan]" + "="*80 + "[/cyan]")
    console.print("[bold yellow]Salida del programa:[/bold yellow]\n")
    
    try:
        interpret_program(ast)
        console.print("\n[cyan]" + "="*80 + "[/cyan]")
        console.print("\n[bold green]✓ Interpretación finalizada exitosamente[/bold green]")
        return True
        
    except BminorExit:
        console.print("\n[cyan]" + "="*80 + "[/cyan]")
        console.print("\n[bold yellow]⚠️ Interpretación terminada debido a un error en tiempo de ejecución[/bold yellow]")
        return False
    except Exception as e:
        console.print("\n[cyan]" + "="*80 + "[/cyan]")
        console.print(f"\n[bold red]Error durante la interpretación: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return False

def mostrar_instrucciones_compilacion():
    """Muestra las instrucciones para compilar y ejecutar el programa"""
    mostrar_separador("INSTRUCCIONES DE COMPILACIÓN Y EJECUCIÓN")
    
    instrucciones = """
[bold cyan]Para compilar el código LLVM IR a un ejecutable:[/bold cyan]

1. Generar archivo objeto:
   [yellow]llc out.ll -filetype=obj -o out.o[/yellow]

2. Enlazar con runtime:
   [yellow]gcc out.o examples/runtime.c -o programa[/yellow]

3. Ejecutar:
   [yellow]En Windows:[/yellow]  .\\programa.exe
   [yellow]En Linux/Mac:[/yellow] ./programa

[bold green]Nota:[/bold green] Asegúrate de tener instalados LLVM y GCC en tu sistema.
"""
    console.print(Panel(instrucciones, border_style="green"))

def main():
    console.print(Panel.fit(
        "[bold cyan]COMPILADOR B-MINOR[/bold cyan]\n"
        "Análisis y Compilación por Fases",
        border_style="cyan"
    ))
    
    # Validar argumentos
    if len(sys.argv) < 2:
        console.print("[bold red]Error:[/bold red] Uso incorrecto\n")
        console.print("[bold]Uso:[/bold] python main.py <archivo.bminor> [--no-interp]")
        console.print("\n[bold]Ejemplos:[/bold]")
        console.print("   python main.py sieve.bminor")
        console.print("   python main.py sieve.bminor --no-interp")
        sys.exit(1)

    filename = sys.argv[1]
    skip_interp = '--no-interp' in sys.argv
    
    fullpath = f"examples/{filename}" if not filename.startswith("examples/") else filename
    
    # Verificar que el archivo existe
    if not os.path.exists(fullpath):
        console.print(f"[bold red]Error:[/bold red] No existe {fullpath}\n")
        console.print("[bold]Archivos disponibles:[/bold]")
        try:
            for f in os.listdir("examples"):
                if f.endswith(".bminor"):
                    console.print(f"   {f}")
        except:
            console.print("   (No se pudo listar el directorio examples/)")
        sys.exit(1)

    console.print(f"\n[bold]Compilando:[/bold] [cyan]{fullpath}[/cyan]\n")
    
    # Leer el archivo fuente
    try:
        with open(fullpath, 'r', encoding='utf-8') as f:
            source = f.read()
    except Exception as e:
        console.print(f"[bold red]Error al leer el archivo:[/bold red] {e}")
        sys.exit(1)
    
    # ========== FASE 1: ANÁLISIS LÉXICO ==========
    tokens, tiene_errores = fase_1_analisis_lexico(source)
    if tiene_errores:
        console.print("\n[bold red]Compilación abortada: Errores en análisis léxico[/bold red]")
        sys.exit(1)
    
    esperar_enter()
    
    # ========== FASE 2: ANÁLISIS SINTÁCTICO ==========
    ast = fase_2_analisis_sintactico(source)
    if not ast:
        console.print("\n[bold red]Compilación abortada: Errores en análisis sintáctico[/bold red]")
        sys.exit(1)
    
    esperar_enter()
    
    # ========== FASE 3: ANÁLISIS SEMÁNTICO ==========
    env = fase_3_analisis_semantico(ast)
    if not env:
        console.print("\n[bold red]Compilación abortada: Errores en análisis semántico[/bold red]")
        sys.exit(1)
    
    esperar_enter()
    
    # ========== FASE 4: GENERACIÓN DE CÓDIGO ==========
    ir_code = fase_4_generacion_codigo(ast)
    if not ir_code:
        console.print("\n[bold red]Compilación abortada: Errores en generación de código[/bold red]")
        sys.exit(1)
    
    if not skip_interp:
        esperar_enter()
        
        # ========== FASE 5: INTERPRETACIÓN ==========
        fase_5_interpretacion(ast)
    
    esperar_enter()
    
    # ========== RESUMEN FINAL ==========
    mostrar_separador("COMPILACIÓN EXITOSA")
    console.print(Panel.fit(
        "[bold green]✓ Todas las fases completadas exitosamente[/bold green]\n\n"
        f"Archivo compilado: [cyan]{fullpath}[/cyan]\n"
        f"Código generado: [cyan]out.ll[/cyan]",
        border_style="green"
    ))
    
    mostrar_instrucciones_compilacion()

if __name__ == '__main__':
    main()