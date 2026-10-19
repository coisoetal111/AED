# AED, last modified abl 2024.10.2
#
# To compile progs:
#    make   OR  make sortelem  OR qsortelem
# To run tests:
#    make t     OR: make qt     OR (Valgrind):  make tv  ETC
#
# NOTE:
# In case of trouble with the shell for loop, GNU Make has 'foreach':
#	$(foreach file,$(FILES),./labconn $(file);)
# https://stackoverflow.com/questions/1490949/how-to-write-loop-in-a-makefile
#----------------------------------------------------------------------
#   Compiler, Compiler Flags

CC = gcc
CFLAGS = -g -Wall -ansi -pedantic

#   Sources
SOURCES = elem.c sortelems.c

#   Objects  ('make' automatically compiles .c to .o)
OBJECTS = elem.o sortelems.o
QOBJECTS = elem.o qsortelems.o

sortelems: $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $(OBJECTS)

elem.o: elem.c elem.h defs.h

sortelems.o: sortelems.c elem.h defs.h

qsortelems: $(QOBJECTS)
	$(CC) $(CFLAGS) -o $@ $(QOBJECTS)

elem.o: elem.c elem.h defs.h

qsortelems.o: qsortelems.c elem.h defs.h

clean:
	rm -f *.o  sortelems qsortelems


FILES = $(shell ls ../tests/*.vec)

VALG = valgrind --leak-check=full

t:
	for F in ${FILES}; do  ./sortelems $${F} ; done;


tv:
	for F in ${FILES}; do ${VALG} ./sortelems $${F} ; done;


tt:
	for F in ${FILES}; do  time ./sortelems $${F} ; done;



qt:
	for F in ${FILES}; do  ./qsortelems $${F} ; done;


qtv:
	for F in ${FILES}; do ${VALG} ./qsortelems $${F} ; done;


qtt:
	for F in ${FILES}; do  time ./qsortelems $${F} ; done;


