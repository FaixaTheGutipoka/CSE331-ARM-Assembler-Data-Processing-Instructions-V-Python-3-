ADDEQ R0, R0, #1
SUB R1, R2, #10
CMP R3, #255
ADD R1, R2, #10    ; immediate
ADD R1, R2, R3     ; register
ADD R0, R1, R2
ADD R3, R3, R4, LSL #3
SUBNE R5, R5, #10
ORR R6, R6, R7, RRX


