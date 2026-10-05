# AED, last modified abl 2019.03.01
#
# To compile prog:
#    make
# To run tests:
#    make t
#
# NOTE:
# In case of trouble with the shell for loop, GNU Make has 'foreach':
#	$(foreach file,$(FILES),./labconn $(file);)
# https://stackoverflow.com/questions/1490949/how-to-write-loop-in-a-makefile
#----------------------------------------------------------------------

CC=gcc
CFLAGS=-g -Wall -ansi -pedantic

SRCFILES = main.c list.c words.c
INCFILES = list.h words.h
OBJFILES = main.o list.o words.o


newWords: $(OBJFILES)
	$(CC) $(CFLAGS) -o newWords $(OBJFILES)

main.o: main.c list.h words.h
	$(CC) -c $(CFLAGS) main.c

list.o: list.c list.h
	$(CC) -c $(CFLAGS) list.c

words.o: words.c words.h  list.h
	$(CC) -c $(CFLAGS) words.c

clean::
	rm -f *.o core a.out newWords *~



FILES = $(shell ls ../test/*.txt)

VALG = valgrind --leak-check=full

t:	newWords
	for F in ${FILES}; do  ./newWords $${F} ; done;


tv:	newWords
	for F in ${FILES}; do ${VALG} ./newWords $${F} ; done;


tt:	newWords
	for F in ${FILES}; do  time ./newWords $${F} ; done;

