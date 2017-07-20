.SUFFIXES	=
AFLAGS	    = -o $@
IMGVIEW     = IMGVIEW.SYSTEM\#FF2000
#
# Image filetypes for Virtual ][
#
PLATYPE	= .\$$ED
BINTYPE	= .BIN
SYSTYPE	= .SYS
TXTTYPE	= .TXT
#
# Image filetypes for CiderPress
#
#RELTYPE	= \#FE1000
#INTERPTYPE	= \#050000
#BINTYPE	= \#060000
#SYSTYPE	= \#FF2000
#TXTTYPE	= \#040000

all: $(IMGVIEW)
bin: imgview.bin

clean:
	-rm *.o *~ *.a *.bin

image.asm: ntsc.py
	python ntsc.py > image.asm

$(IMGVIEW): imgview.asm image.asm
	acme --setpc 8192 -o $(IMGVIEW) imgview.asm
	ac -d IMGVIEW.PO IMGVIEW.SYSTEM
	ac -p IMGVIEW.PO IMGVIEW.SYSTEM SYS < IMGVIEW.SYSTEM#FF2000

imgview.bin: imgview.asm image.asm
	acme --setpc 4096 -o imgview.bin imgview.asm

