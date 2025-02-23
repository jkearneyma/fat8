; Copyright 2025 jim kearney

; build using build.sh in this directory
; assembler used is asl: http://john.ccac.rwth-aachen.de:8000/as/
; (convenient build via https://github.com/Macroassembler-AS/asl-releases)

	PAGE	0
	CPU	8008
	RADIX	8
	LISTING PURECODE
	MACEXP_DFT NOIF,NOMACRO

BEL	EQU	07
BS	EQU	10
LF	EQU	12
CR	EQU	15
ESC	EQU	33
SP	EQU	40

SERINP	EQU	0	; serial read d0
SEROUTP	EQU	10	; serial write d0
WREINPP	EQU	1	; write enables read d0-7
WREOUTP	EQU	11	; write enables write d0-7

SCELBAL	EQU	03000	; SCELBAL program start
SCELVAR	EQU	20000	; SCELBAL variables start

	ORG	000	; main button forces 1-byte read here
	rst	7	; 1 byte call to 070

; Self-modifying code is necessary sometimes, for
; example there is no indirect jump instruction.
; N.b. that this is normally write-protected memory
; and that protection must be removed to write
; here, and then restored.
jmpvec	jmp	0
; Similarly there is no indirect I/O instruction.
iovec	inp	0
	ret

	; load constant address to HL
lhli	MACRO	arg1
	lhi	arg1/400
	lli	arg1#400
	ENDM

ldehl	MACRO
	ldh
	lel
	ENDM

lhlde	MACRO
	lhd
	lle
	ENDM

	; Utility functions called by RST n
	; Rewrite CAL to RST
cal	MACRO	dest
	IF UpString("dest")="PUTS"
	; Print asciz string pointed at by HL, ABHL destroyed
	rst	1
	ELSEIF UpString("dest")="PUTC"
	; Print char in A, B destroyed
	rst	3
	ELSEIF UpString("dest")="GETC"
	; Wait for an input character. AB destroyed, C is return
	rst	4
	ELSEIF UpString("dest")="DELAY"
	; Delay 4 * B cycles, B destroyed
	rst	5
	ELSE
	!cal	dest
	ENDIF
	ENDM

	ORG	010
puts:	lam
	nda	; test a
	rtz
	cal	putc
	inl
	jfz	puts
	inh
	jmp	puts
 
	; Print char in A, B destroyed
	ORG	030
putc:	lba
	xra
	out	SEROUTP
	lab
	jmp	putc_cont

	ORG	040
getc:
	inp	SERINP	; look for start bit '0'
	rrc
	jtc	getc
	jmp	getc_cont

	; delay by B count
	; preserves ACDEHL
	; leaves B 0, z
	ORG	050
delay:
	dcb
	jfz	delay
	ret

	ORG	060
	ret		; free

	ORG	070
; first, unprotect SCELBAL variable area
	lai	(377 << (SCELVAR/4000)) & 377
	out	WREOUTP
	lhli	intro
	cal	puts
main:
	lhli	prompt
	cal	puts
	cal	getc
	cpi	'a'
	jtc	noupper
	sui	'a'-'A'
noupper:lda
	cal	putc
	lad
	cpi	'?'
	jtz	dohelp
	cpi	':'
	jtz	doihex
	cpi	'E'
	jtz	doentr
	cpi	'I'
	jtz	doinp
	cpi	'J'
	jtz	dojump
	cpi	'O'
	jtz	dooutp
	cpi	'P'
	jtz	doprint
	cpi	'S'
	jtz	scelbal
	lhli	bip
	cal	puts
	jmp	main

putlsb	MACRO
	out	SEROUTP
	rrc
	lbi	42	; small delay
	lbi	42	; small delay
	lbi	12	; big delay
	cal	delay
	ENDM

putc_cont:
	lbi	42	; small delay
	lbi	12	; big delay
	cal	delay
	REPT	10
	putlsb
	ENDM
	lba
	lai	1	; stop bit
	out	SEROUTP
	lab
	lbi	42	; small delay
	lbi	12	; big delay
	jmp	delay

getlsb	MACRO
	laa		; small delay
	lbi	12	; big delay
	cal	delay
	lba
	inp	SERINP
	rar		; bit to carry
	lab
	rar		; carry to msb
	ENDM

getc_cont:
	inp	SERINP	; check start bit '0' again
	rrc		; (e.g. noise)
	jtc	getc
	lbi	3
	cal	delay	; halfway into start bit
	inp	SERINP	; check again '0'
	rrc
	jtc	getc
	REPT	10
	getlsb
	ENDM
	lbi	12
	cal	delay
	lba
	inp	SERINP	; check stop bit '1'
	rrc
	jfc	getc
	lab
	ret		; still at least half the stop bit to go,
			; but there's no reason to wait for it

; preserves CDHL
; ret val in A and E (same)
; NZ if Esc
octal3:	cal	octal1
	rfz
octal2:	cal	octal1
	rfz
octal1:	lae
	ndi	37 
	rlc
	rlc
	rlc
	lea
oretry:	cal	getc
	cpi	ESC
	jtz	octbad
	cpi	'0'
	jtc	octbad
	cpi	'8'
	jfc	octbad
	cal	putc
	ndi	7
	ore
	lea
octok:	cpa
	ret	; Z
octbad:	lai	BEL
	cal	putc
	jmp	oretry
octesc:	xra
	adi	1
	ret	; NZ

; read a split address
; preserves HL
; ret addr in DE
; NZ if Esc
readadr:lhli	paddr
	cal	puts
	cal	octal3
	rfz
	lde
	lai	':'
	cal	putc
	jmp	octal3

; write A as octal
; preserve CDE, trash ABHL
writoct:lli	3
	nda
writo1:	ral
	ral
	lha	; save A
	ral
	ndi	7
	adi	'0'
	cal	putc
	lah
	ral
	dcl
	jfz	writo1
	ret

dohelp:	lhli	help
	cal	puts
	jmp	main

; format
; :llaaaattdd*xx<CR>[<LF>]
; where ll=length of dd, aaaa=address, tt=type, dd=data, xx=checksum
; tt=00 data, 01 eof
doihex:	lll
	hlt

unprot1c:
	inp	WREINPP
	lba
	ori	1	; write enable first 2KB
	out	WREOUTP
	ret

unprot1:MACRO
	cal	unprot1c
	ENDM
reprot1:MACRO
	lab
	out	WREOUTP
	ENDM


doinp:	lhli	pport
	cal	puts
	xra
	lea
	cal	octal1
	jfz	main
	lai	SP
	cal	putc
	lae
	rlc
	ori	101
	lhli	iovec
	lca
	unprot1
	lmc
	reprot1
	cal	iovec
	cal	writoct
	jmp	main

dooutp:	lhli	pport
	cal	puts
	xra
	lea
	cal	octal1
	jfz	main
	rlc
	ori	121
	lhli	iovec
	lca
	unprot1
	lmc
	reprot1
	lhli	pvalu
	cal	puts
	cal	octal3
	cal	iovec
	jmp	main

dojump:	cal	readadr
	jfz	main	; Esc
	lhli	crlf
	cal	puts
	lhli	jmpvec+1
	unprot1
	lme
	inl
	lmd
	reprot1
	jmp	jmpvec

doentr:	cal	readadr
	jfz	main	; Esc
	lhli	crlf
	cal	puts
enter0:	lhlde
	lam
	cal	writoct
	lhli	bs3
	cal	puts
; first char 0-3, SP, ESC
wait1:	lhlde
	cal	getc
	cpi	ESC
	jtz	main
	cpi	SP
	jtz	skipentr
	cpi	'0'
	jtc	fail1
	cpi	'4'
	jfc	fail1
	cal	putc
	lea
	cal	octal2
	jfz	main
	lll
	lme
	ldehl
	jmp	tonext

fail1:	lai	BEL
	cal	putc
	jmp	wait1

skipentr:
	lhlde
	lam
	cal	writoct
tonext: lai	SP
	cal	putc
	ine
	jfz	enter0
	ind
	jmp	enter0
	

doprint:cal	readadr
	jfz	main	; Esc
	lhli	memex
pbytes:	cal	puts
	lad
	cal	writoct
	lai	':'
	cal	putc
	lae
	cal	writoct
	lci	10
pbyte:	lai	SP
	cal	putc
	lhlde
	lam
	cal	writoct
	ine
	jfz	pnovf
	ind
pnovf:	dcc
	jfz	pbyte
pnext:	cal	getc
	lhli	crlf
	cpi	CR
	jtz	pbytes
	cpi	ESC
	jtz	main
	lai	BEL
	cal	putc
	jmp	pnext

intro:	DB	CR,LF,CR,LF,LF,"fat8 monitor. ? for help. Del to cancel.",0
prompt:	DB	CR,LF,"fat8> ",0
bip:	DB	BEL,BS,0
paddr:	DB	" ___:___",BS,BS,BS,BS
bs3:	DB	BS,BS,BS,0
memex:	DB	" <Enter> for next line, <Esc> to end"
crlf:	DB	CR,LF,0
pport:	DB	" _",BS,0
pvalu:	DB	" ___",BS,BS,BS,0
help:	DB	CR,LF,"P aaa:aaa  | print 8 bytes, <Enter>/<Esc>"
	DB	CR,LF,"E aaa:aaa  | enter bytes until <Esc>"
	DB	CR,LF,"J aaa:aaa  | jump to address"
	DB	CR,LF,"I p        | input"
	DB	CR,LF,"O p ddd    | output"
	DB	CR,LF,"S          | start SCELBAL"
	DB	CR,LF,":<data>    | Intel hex loader"
	DB	CR,LF,0

