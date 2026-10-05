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

SOURCE=palTab.c
OBJECT=palTab.o
TARGET=palTab

palTab: $(OBJECT)
	$(CC) $(SOURCE) -g -o $(TARGET)


FILES = $(shell ls ../test/*.txt)

VALG = valgrind --leak-check=full


t:	palTab
	for F in ${FILES}; do  ./palTab $${F} ; done;


tv:	palTab
	for F in ${FILES}; do ${VALG} ./palTab $${F} ; done;


tt:	palTab
	for F in ${FILES}; do  time ./palTab $${F} ; done;
