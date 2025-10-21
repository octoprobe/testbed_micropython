CC=gcc
CFLAGS=-Wall -Wextra -std=c99
TARGET=mpremote_c
SOURCE=mpremote_c.c

$(TARGET): $(SOURCE)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCE)

clean:
	rm -f $(TARGET)

.PHONY: clean