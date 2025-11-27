# test_checker.py
import sys
import os
from pathlib import Path
from rich import print
from rich.console import Console
from rich.table import Table

from bminor import Lexer
from parser import Parser
from checker import check_program
from errors import clear_errors, errors_detected

console = Console()


def test_file(filename):
    # Probar un solo archivo
    print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    print(f"[bold cyan]Probando: {filename}[/bold cyan]")
    print(f"[bold cyan]{'='*60}[/bold cyan]\n")
    
    try:
        # Leer archivo
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        clear_errors()
        
        # Lexer
        lexer = Lexer()
        tokens = list(lexer.tokenize(source))
        
        # Parser
        parser = Parser()
        ast = parser.parse(lexer.tokenize(source))
        
        if ast is None:
            print("[red]Error en parsing[/red]")
            return False
        
        # Checker
        clear_errors()
        symtab = check_program(ast)
        
        if errors_detected():
            print(f"\n[red]Total de errores semanticos: {errors_detected()}[/red]")
            return False
        else:
            print("\n[green]✓ Sin errores semanticos[/green]")
            
        print("\n[cyan]Tabla de símbolos:[/cyan]")
        symtab.print()
        
        return True
        
    except FileNotFoundError:
        print(f"[red]Archivo no encontrado: {filename}[/red]")
        return False
    except Exception as e:
        print(f"[red]Error inesperado: {e}[/red]")
        return False


def test_directory(directory):
    # Prueba todos los archivos en un directorio
    # Buscar todos los archivos .bminor en el directorio
    path = Path(directory)
    
    if not path.exists():
        print(f"[red]Error: El directorio '{directory}' no existe[/red]")
        return
    
    if not path.is_dir():
        print(f"[red]Error: '{directory}' no es un directorio[/red]")
        return
    
    # Obtener todos los archivos .bminor
    files = sorted(path.glob('*.bminor'))
    
    # Si no hay archivos .bminor, buscar cualquier archivo
    if not files:
        files = sorted([f for f in path.iterdir() if f.is_file()])
    
    if not files:
        print(f"[yellow]No se encontraron archivos en '{directory}'[/yellow]")
        return
    
    print(f"\n[bold magenta]Encontrados {len(files)} archivo(s) para probar[/bold magenta]\n")
    
    # Resultados
    results = []
    
    # Probar cada archivo
    for file in files:
        success = test_file(str(file))
        results.append((file.name, success))
        print("\n")
    
    # Mostrar resumen
    print_summary(results)


def print_summary(results):
    print(f"\n[bold magenta]{'='*60}[/bold magenta]")
    print(f"[bold magenta]RESUMEN DE PRUEBAS[/bold magenta]")
    print(f"[bold magenta]{'='*60}[/bold magenta]\n")
    
    # Crear tabla
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Archivo", style="cyan", width=40)
    table.add_column("Resultado", justify="center", width=15)
    
    passed = 0
    failed = 0
    
    for filename, success in results:
        if success:
            table.add_row(filename, "[green] PASO[/green]")
            passed += 1
        else:
            table.add_row(filename, "[red] FALLO[/red]")
            failed += 1
    
    console.print(table)
    
    # Estadísticas
    total = len(results)
    print(f"\n[bold]Total de archivos:[/bold] {total}")
    print(f"[green]Exitosos:[/green] {passed}")
    print(f"[red]Fallidos:[/red] {failed}")
    
    if failed == 0:
        print(f"\n[bold green] ¡Todas las pruebas pasaron! [/bold green]")
    else:
        print(f"\n[bold red]⚠ {failed} prueba(s) fallaron[/bold red]")


def main():
    if len(sys.argv) == 1:
        # Sin argumentos: probar directorio test/prueba
        test_directory('test/prueba')
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        
        # Verificar si es un directorio o un archivo
        if os.path.isdir(arg):
            test_directory(arg)
        elif os.path.isfile(arg):
            # Probar archivo individual
            success = test_file(arg)
            if success:
                print("\n[bold green] Prueba exitosa[/bold green]")
            else:
                print("\n[bold red] Prueba fallida[/bold red]")
                sys.exit(1)
        else:
            print(f"[red]Error: '{arg}' no es un archivo ni directorio valido[/red]")
            sys.exit(1)
    else:
        print("[yellow]Uso:[/yellow]")
        print("  python test_checker.py                    # Prueba test/prueba")
        print("  python test_checker.py <archivo.bminor>   # Prueba un archivo")
        print("  python test_checker.py <directorio>       # Prueba un directorio")
        sys.exit(1)


if __name__ == '__main__':
    main()