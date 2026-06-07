# Variables
ASM = nasm
ASM_FLAGS = -g -f elf64 -l disc-log.lst
CC = gcc
CC_FLAGS = -g -m64 -no-pie

# Default Rule
all: disc-log

# Linking object files to final executable
disc-log: disc-log.o
	$(CC) $(CC_FLAGS) -o disc-log disc-log.o
	rm -f disc-log.o

# Compiling Assembly file
disc-log.o: disc-log.asm
	$(ASM) $(ASM_FLAGS) disc-log.asm -o disc-log.o

# Clean up build artifacts
clean:
	rm -f disc-log disc-log.o disc-log.lst