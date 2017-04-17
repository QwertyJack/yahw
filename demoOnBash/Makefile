all: tts iat
.PHONY: clean

GCC=gcc
CLIBPATH=-L`pwd -L`/lib -L`pwd`/lib64
LIBFLAG=-lmsc -ldl -lrt -pthread
LDFLAG=-Wl,-rpath,`pwd`/lib:`pwd`/lib64

tts: src/ttsdemo.c
	$(GCC) -o $@ $^ $(CLIBPATH) $(LIBFLAG) $(LDFLAG)

iat: src/iatdemo.c
	$(GCC) -o $@ $^ $(CLIBPATH) $(LIBFLAG) $(LDFLAG)

clean:
	rm iat tts
