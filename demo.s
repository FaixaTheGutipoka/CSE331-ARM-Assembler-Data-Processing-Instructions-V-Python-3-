; ============================================================
;   DATA PROCESSING – ARITHMETIC (ADD, SUB, RSB, ADC, SBC, RSC)
; ============================================================

; -------- ADD --------
ADDEQ R0, R1, #1
ADDNE R0, R1, R2
ADD    R0, R1, R2, LSL #2
ADD    R0, R1, R2, LSR #1
ADD    R0, R1, R2, ASR #3
ADD    R0, R1, R2, ROR #4
ADD    R0, R1, R2, RRX

; -------- SUB --------
SUBEQ R3, R4, #5
SUBNE R3, R4, R5
SUB    R3, R4, R5, LSL #2
SUB    R3, R4, R5, LSR #1
SUB    R3, R4, R5, ASR #3
SUB    R3, R4, R5, ROR #4
SUB    R3, R4, R5, RRX

; -------- RSB --------
RSBEQ R6, R7, #2
RSBNE R6, R7, R8
RSB    R6, R7, R8, LSL #2
RSB    R6, R7, R8, LSR #1
RSB    R6, R7, R8, ASR #3
RSB    R6, R7, R8, ROR #4
RSB    R6, R7, R8, RRX

; -------- ADC --------
ADCEQ R9,  R10, #3
ADCNE R9,  R10, R11
ADC    R9,  R10, R11, LSL #2
ADC    R9,  R10, R11, LSR #1
ADC    R9,  R10, R11, ASR #3
ADC    R9,  R10, R11, ROR #4
ADC    R9,  R10, R11, RRX

; -------- SBC --------
SBCEQ R12, R13, #7
SBCNE R12, R13, R14
SBC    R12, R13, R14, LSL #2
SBC    R12, R13, R14, LSR #1
SBC    R12, R13, R14, ASR #3
SBC    R12, R13, R14, ROR #4
SBC    R12, R13, R14, RRX

; -------- RSC --------
RSCEQ R1,  R2,  #9
RSCNE R1,  R2,  R3
RSC    R1,  R2,  R3, LSL #2
RSC    R1,  R2,  R3, LSR #1
RSC    R1,  R2,  R3, ASR #3
RSC    R1,  R2,  R3, ROR #4
RSC    R1,  R2,  R3, RRX


; ============================================================
;   DATA PROCESSING – LOGICAL (AND, ORR, EOR, BIC)
; ============================================================

; -------- AND --------
ANDEQ R0, R0, #0xFF
ANDNE R0, R0, R1
AND    R0, R0, R1, LSL #2
AND    R0, R0, R1, LSR #1
AND    R0, R0, R1, ASR #3
AND    R0, R0, R1, ROR #4
AND    R0, R0, R1, RRX

; -------- ORR --------
ORREQ R2, R3, #0x55
ORRNE R2, R3, R4
ORR    R2, R3, R4, LSL #2
ORR    R2, R3, R4, LSR #1
ORR    R2, R3, R4, ASR #3
ORR    R2, R3, R4, ROR #4
ORR    R2, R3, R4, RRX

; -------- EOR --------
EOREQ R5, R6, #0xAA
EORNE R5, R6, R7
EOR    R5, R6, R7, LSL #2
EOR    R5, R6, R7, LSR #1
EOR    R5, R6, R7, ASR #3
EOR    R5, R6, R7, ROR #4
EOR    R5, R6, R7, RRX

; -------- BIC --------
BICEQ R8,  R9,  #0xF0
BICNE R8,  R9,  R10
BIC    R8,  R9,  R10, LSL #2
BIC    R8,  R9,  R10, LSR #1
BIC    R8,  R9,  R10, ASR #3
BIC    R8,  R9,  R10, ROR #4
BIC    R8,  R9,  R10, RRX


; ============================================================
;   DATA PROCESSING – MOVE (MOV, MVN)
; ============================================================

MOVEQ R0, #123
MOVNE R0, R1
MOV    R0, R1, LSL #8
MOV    R0, R1, LSR #4
MOV    R0, R1, ASR #2
MOV    R0, R1, ROR #1
MOV    R0, R1, RRX

MVNEQ R2, #0x0
MVNNE R2, R3
MVN    R2, R3, LSL #2
MVN    R2, R3, LSR #1
MVN    R2, R3, ASR #3
MVN    R2, R3, ROR #4
MVN    R2, R3, RRX


; ============================================================
;   DATA PROCESSING – COMPARE / TEST (CMP, CMN, TST, TEQ)
;   (no Rd field; only Rn / operand2)
; ============================================================

CMPEQ R4, #200
CMPNE R4, R5
CMP    R4, R5, LSL #2
CMP    R4, R5, LSR #1
CMP    R4, R5, ASR #3
CMP    R4, R5, ROR #4
CMP    R4, R5, RRX

CMNEQ R6, #1
CMNNE R6, R7
CMN    R6, R7, LSL #2
CMN    R6, R7, LSR #1
CMN    R6, R7, ASR #3
CMN    R6, R7, ROR #4
CMN    R6, R7, RRX

TSTEQ R8, #0xFF
TSTNE R8, R9
TST    R8, R9, LSL #2
TST    R8, R9, LSR #1
TST    R8, R9, ASR #3
TST    R8, R9, ROR #4
TST    R8, R9, RRX

TEQEQ R10, #127
TEQNE R10, R11
TEQ    R10, R11, LSL #2
TEQ    R10, R11, LSR #1
TEQ    R10, R11, ASR #3
TEQ    R10, R11, ROR #4
TEQ    R10, R11, RRX


; ============================================================
;   SINGLE DATA TRANSFER (LDR / STR) – Immediate Offset
; ============================================================

LDREQ R0, [R1, #0]
LDRNE R2, [R3, #4]
LDR    R4, [R5, #8]
LDR    R6, [R7, #12]
LDR    R8, [R9, #1024]
LDR    R10, [R11, #4095]   ; max imm12

STREQ R12, [R1, #0]
STRNE R12, [R1, #4]
STR    R12, [R1, #8]
STR    R12, [R1, #12]
STR    R12, [R1, #1024]
STR    R12, [R1, #4095]