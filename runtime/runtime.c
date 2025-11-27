/*
 * runtime.c
 * 
 * Biblioteca de runtime para el compilador B-Minor
 * Este archivo contiene las funciones de soporte que el código LLVM generado necesita
 */

#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

/* Funciones de impresión para diferentes tipos */

void _printi(int value) {
    printf("%d\n", value);
}

void _printf(double value) {
    printf("%f\n", value);
}

void _printb(bool value) {
    printf("%s\n", value ? "true" : "false");
}

void _printc(char value) {
    printf("%c\n", value);
}

void _prints(char* value) {
    printf("%s\n", value);
}

/* Funciones auxiliares para arrays */

int array_length(void* arr) {
    // Esta es una función simplificada
    // En una implementación real, necesitaríamos metadata del array
    return 0;
}

/* Funciones matemáticas adicionales */

int _powi(int base, int exp) {
    int result = 1;
    for (int i = 0; i < exp; i++) {
        result *= base;
    }
    return result;
}

double _powf(double base, int exp) {
    double result = 1.0;
    for (int i = 0; i < exp; i++) {
        result *= base;
    }
    return result;
}

/* Main - El código LLVM generado define su propia función main */