;*
;* Light Cycles 3D
;*
KEYBD   =       $C000   ; KEYBOARD
KEYSTRB =       $C010
STORE80DIS =    $C000
STORE80EN =	$C001
MAINWRT =       $C004
AUXWRT  =       $C005
VIDCTL  =       $C029
SHADOW  =       $C035
SCB     =       $80     ; 640 PIXEL SUPER-HIRES
PIXBUF  =       $2000
SCBBUF  =       $9D00
PALBUFF =       $9E00
DST     =       $06
SRC     =       $08
;*       =       $1000
;
; TURN OFF 80 COLUMN CODE
;
	STA	STORE80DIS
;
; SHADOW SHR BUFFER IN AUX MEMORY
;
        LDA     VIDCTL
        ORA     #$80
        STA     VIDCTL
        LDA     SHADOW
        AND     #$F7
        STA     SHADOW
;
; FILL SCB
;
        LDX     #200
        LDA     #SCB
        STA     AUXWRT
-       STA     SCBBUF-1,X
        DEX
        BNE     -
        STA     MAINWRT
;
; FILL PALETTE
;
        LDY     #$00
        STA     AUXWRT
-       LDA     PALETTE,Y
        STA     PALBUFF,X
        STA     PALBUFF+$1000,X
        INY
        TYA
        AND     #$07
        TAY
        INX
        BNE     -
        STA     MAINWRT
;
; COPY IMAGE TO FRAMEBUFFER
;
        LDX     #<IMAGE
        STX     SRC
        LDX     #>IMAGE
        STX     SRC+1
        LDX     #<PIXBUF
        STX     DST
        LDX     #>PIXBUF
        STX     DST+1
        LDY     #$00
        STA     AUXWRT
-       LDA     (SRC),Y
        STA     (DST),Y
        INY
        BNE     -
        INC     SRC+1
        INX
        STX     DST+1
        CPX     #>SCBBUF
        BNE     -
        STA     MAINWRT
; !!! A2PI return !!!
        RTS
;
; WAIT FOR KEYPRESS
;
        LDA     KEYSTRB
-       LDA     KEYBD
        BPL     -
        LDA     KEYSTRB
;
; CLEAN UP
;
EXIT:	LDA     VIDCTL
        AND     #$7F
        STA     VIDCTL
        LDA     SHADOW
        ORA     #$08
        STA     SHADOW
        JSR     $BF00   ; ProDOS QUIT
        !BYTE   $65
        !WORD   PARMTBL
PARMTBL !BYTE   4
        !BYTE   0
        !WORD   0
        !BYTE   0
        !WORD   0
PALETTE:
;        !WORD   $0000, $0555, $0AAA, $0FFF
        !WORD   $0000, $0333, $0777, $0FFF
IMAGE:
        !SOURCE "image.asm"
