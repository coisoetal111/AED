# AED 2026-2027, Sem. 1
# Makefile for Lab 05 - Graphs: Representations, Conversions, and Traversal
#-----------------------------------------------------------------------
#   Compiler, Compiler Flags
CC = gcc
CFLAGS = -g -Wall -std=c99 -pedantic

#   Sources & Objects
SOURCES = LinkedList.c graph.c main.c
OBJECTS = LinkedList.o graph.o main.o

lab05: $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $(OBJECTS)

LinkedList.o: LinkedList.c LinkedList.h defs.h
	$(CC) -c $(CFLAGS) LinkedList.c

graph.o: graph.c graph.h LinkedList.h defs.h
	$(CC) -c $(CFLAGS) graph.c

main.o: main.c graph.h
	$(CC) -c $(CFLAGS) main.c

listest: LinkedList.o listest.c
	$(CC) $(CFLAGS) -o $@ listest.c LinkedList.o

# Tests
FILES = $(shell ls ../tests/*.adj 2>/dev/null)
VALG = valgrind --leak-check=full

t: lab05
	for F in ${FILES}; do ./lab05 $${F}; done;

tv: lab05
	for F in ${FILES}; do ${VALG} ./lab05 $${F}; done;

clean::
	rm -f *.o core a.out lab05 listest *~ ../tests/*.ladj ../tests/*.edge
