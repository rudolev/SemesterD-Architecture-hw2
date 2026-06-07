ASM = nasm
ASM_FLAGS = -g -f elf64 -l disc-log.lst
CC = gcc
CC_FLAGS = -g -m64 -no-pie

all: disc-log

disc-log: disc-log.o
	$(CC) $(CC_FLAGS) -o disc-log disc-log.o
	rm -f disc-log.o

disc-log.o: disc-log.asm
	$(ASM) $(ASM_FLAGS) disc-log.asm -o disc-log.o

clean:
	rm -f disc-log disc-log.o disc-log.lst