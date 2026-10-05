CC = gcc
CFLAGS = -Wall -std=c99 -O3
LDFLAGS = -lm
TARGET = healkristin

SRCS = healkristin.c tasks.c funcMan.c
OBJS = $(SRCS:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJS) $(LDFLAGS)

%.o: %.c healkristin.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)