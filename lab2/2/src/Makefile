# AED, last modified abl 2019.02.28
#
# To compile prog:
#    make
# To run all tests:
#    make t
#
# NOTE:
# In case of trouble with the shell for loop, GNU Make has 'foreach':
#	$(foreach file,$(FILES),./labconn $(file);)
# https://stackoverflow.com/questions/1490949/how-to-write-loop-in-a-makefile
#----------------------------------------------------------------------

SRCFILES = labconn.c connectivity.c
OBJFILES = labconn.o connectivity.o
INCFILES = connectivity.h

TARGET = labconn

CC = gcc
CFLAGS= -g -Wall -I.
LIBS=

default: $(TARGET)

$(TARGET): $(OBJFILES)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJFILES) $(LIBS)

clean:
	/bin/rm ${TARGET} $(OBJFILES)


## do all test runs automatically

FILES=$(shell ls zx/*)

t:  t1 t2 t3 t4


t1:
	rm -f out1.txt
	for F in ${FILES}; do  ./labconn -1 $$F >> out1.txt; done;

t2:
	rm -f out2.txt
	for F in ${FILES}; do  ./labconn -2 $$F >> out2.txt; done;

t3:
	rm -f out3.txt
	for F in ${FILES}; do  ./labconn -3 $$F >> out3.txt; done;

t4:
	rm -f out4.txt
	for F in ${FILES}; do  ./labconn -4 $$F >> out4.txt; done;
