import argparse, fileinput, re, sys, os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple



# 1. Opcode / condition / shift lookup tables

OpCodes = {
    "AND": 0x00,
    "EOR": 0x01,
    "SUB": 0x02,
    "RSB": 0x03,
    "ADD": 0x04,
    "ADC": 0x05,
    "SBC": 0x06,
    "RSC": 0x07,
    "TST": 0x08,
    "TEQ": 0x09,
    "CMP": 0x0A,
    "CMN": 0x0B,
    "ORR": 0x0C,
    "MOV": 0x0D,
    "BIC": 0x0E,
    "MVN": 0x0F,
}

Cond = {
    "EQ": 0x00,
    "NE": 0x01,
    "CS": 0x02,
    "CC": 0x03,
    "MI": 0x04,
    "PL": 0x05,
    "VS": 0x06,
    "VC": 0x07,
    "HI": 0x08,
    "LS": 0x09,
    "GE": 0x0A,
    "LT": 0x0B,
    "GT": 0x0C,
    "LE": 0x0D,
    "AL": 0x0E,
}

ShiftTypes = {                  
    "LSL": 0b00,
    "LSR": 0b01,
    "ASR": 0b10,
    "ROR": 0b11,
}                   

# 2. Simple regex tokenizer / parser
Token = re.compile(
    r"""
    ^\s*                                              # start of line, optional whitespace

    (?P<mnemonic>[A-Z]{2,3})(?P<cond>[A-Z]{2})?       # mnemonic + optional condition
    \s+
    R(?P<Rd>\d{1,2})                                  # destination register
    (?:\s*,\s*R(?P<Rn>\d{1,2}))?                      # optional Rn
    \s*,\s*

    (?:
        \#(?P<imm>-?\d+)                              # immediate value
      |
        R(?P<Rm>\d{1,2})                              # register operand
        (?:\s*,?\s*                                   # optional comma
            (?P<shiftop>LSL|LSR|ASR|ROR|RRX)          # optional shift type
            (?:\s*\#(?P<shiftimm>\d+))?               # optional shift amount
        )?                                            # end of shift clause
    )

    \s*$
    """,
    re.VERBOSE | re.IGNORECASE,
)




def parse_line(line: str):

    """
    Parse 'ADDNE R1, R2, #42' → ('ADD','NE',1,2,42)
    Raises ValueError on bad syntax.
    """

    match = Token.match(line)                                                       # match the line against the regex pattern

    if not match:
        raise ValueError(f"syntax error: «{line.strip()}»")                         # raise an error if the line doesn't match the expected format

    mnemonic = match.group("mnemonic").upper()                                      # convert mnemonic to uppercase. addne or AdD is treated the same as ADD
    cond = (match.group("cond") or "AL").upper()                                    # default to AL (always) if no condition is specified
    Rd = int(match.group("Rd"))                                                     # destination register
    Rn = int(match.group("Rn") or 0)                                                # optional first operand
    
    if match.group("imm") is not None:
        return mnemonic, cond, Rd, Rn, int(match.group("imm")), True, None, None    # immediate value (e.g., #42)
    
    # register form (with optional shift)
    Rm = int(match.group("Rm"))
    shiftop = (match.group("shiftop") or "LSL").upper()
    if shiftop == "RRX":
        shiftimm = 0
    else:
        shiftimm = int(match.group("shiftimm") or 0)
        if not 0 <= shiftimm <= 31:
            raise ValueError("shift immediate must be 0-31")
    return mnemonic, cond, Rd, Rn, Rm, False, shiftop, shiftimm


# 3. Immediate-12 encoder   (rotate-right until fits in 8 bits)
def encode_imm12(value: int) -> int:

    """
    ARM encodes an 8-bit value rotated right by an even amount.
    Returns the imm12 field (rotate:4 | imm8) or raises ValueError.
    """

    value &= 0xFFFFFFFF                                                 # Ensure value is treated as a 32-bit unsigned integer
    for rot in range(0, 32, 2):                                         # Rotate right by 0, 2, 4, ..., 30 bits
        low8 = ((value >> rot) | (value << (32 - rot))) & 0xFFFFFFFF    # Rotate right and mask to 32 bits
        
        if low8 <= 0xFF:                                                # If the low 8 bits fit in an 8-bit value
            return (rot // 2) << 8 | low8                               # Return the imm12 field (rotate:4 | imm8)

    raise ValueError(f"{value} not encodable in imm12")                 # Raise an error if no valid encoding is found


def encode_reg_shift(Rm: int, shiftop: str, shiftimm: int) -> int:
    if shiftop == "RRX":
        # imm5=0, type=ROR(11), bit 4 = 0
        return (0 << 7) | (0b11 << 5) | (Rm & 0xF)
    stype = ShiftTypes[shiftop]
    return ((shiftimm & 0x1F) << 7) | (stype << 5) | (Rm & 0xF)


# 4. Assemble one instruction → 32-bit word
def assemble_one(mnem, cond, Rd, Rn, op2, is_imm, shiftop, shiftimm):

    """
    The goal of the function is to turn one parsed assembly instruction into the
    exact 32-bit machine word that ARMv7 expects in hexadecimal format.
    """

    if mnem not in OpCodes:                             # Check if the mnemonic is supported
        raise KeyError(f"unsupported mnemonic {mnem}")

    opcode = OpCodes[mnem]                              # Get the opcode for the mnemonic
    cond_bits = Cond.get(cond, 0xE)                     # Get the condition bits, default to AL (0xE) if not specified
    
    is_test = opcode in (0x8, 0x9, 0xA, 0xB)            # TST,TEQ,CMP,CMN
    S = 1 if is_test else 0                             # Set S bit for test instructions, otherwise 0. Automatically setting S = 1 if the instruction must update flags by design.
    if mnem == "MOV":
        Rn = 0                                                # MOV ignores Rn

    if is_imm:
        I = 1
        op2_field = encode_imm12(op2)
    else:
        I = 0
        op2_field = encode_reg_shift(op2, shiftop, shiftimm) # Rm is directly encoded in bits [3:0]

    return (
        (cond_bits << 28)          # bits 31-28 — condition
        | (I << 25)                # bit 25 = I-bit = 1 (immediate)
                                   # bits 27-26 = 00 (data-proc class); by default it is 00 for any data processing instructions
        | (opcode << 21)           # bits 24-21 — opcode
        | (S << 20)                # bit 20 — set-flags
        | (Rn << 16)               # bits 19-16 — first operand register
        | (Rd << 12)               # bits 15-12 — destination register
        | op2_field                # bits 11-0 — second operand (immediate or register)
    )


# 5. Formatting results

# HEX
def word_to_hex(word: int) -> str: return f"0x{word:08X}"
# BIN
def word_to_bin(word: int) -> str: return f"{word:032b}"
# RAW
def to_bytes(ws:List[int])->bytes: return b"".join(w.to_bytes(4,"little") for w in ws)


# 6. Assemble a list of lines
def assemble_lines(lines: List[str]) -> List[Tuple[str, int]]:

    """ 
    This function takes a list of assembly lines as strings (e.g., from a .s file) and:
    - Cleans them
    - Parses each into components (like "ADD", R1, etc.)
    - Converts them to machine instructions (32-bit ints)
    - Returns the list of final machine instructions
    """

    machine=[]
    for idx,raw in enumerate(lines,1):
        src=raw.partition(";")[0].strip()
        if not src: continue
        try:
            parts=parse_line(src)
            word=assemble_one(*parts)
            machine.append((src,word))
        except Exception as e:
            raise RuntimeError(f"[line {idx}] {e}") from None
    return machine


# 7. CLI interface
def main() -> None:
    
    ap=argparse.ArgumentParser(description="ARMv7 DP assembler (imm + shifted reg)")
    ap.add_argument("files",nargs="*",help="assembly source (.s); stdin if none")
    ap.add_argument("--format",choices=["table","raw"],default="table")
    ap.add_argument("--out",help="output file for --format raw")
    args=ap.parse_args()

    pairs=assemble_lines(list(fileinput.input(args.files or ("-",))))

    if args.format=="raw":
        if not args.out:
            print("--out FILE required with --format raw",file=sys.stderr);sys.exit(1)
        with open(args.out,"wb") as f:
            f.write(to_bytes([w for _,w in pairs]))
        return

    # Table output
    print(f"{'ASSEMBLY':<40} | {'HEX':<10} | BINARY")
    print("-"*40+"-+-"+"-"*10+"-+-"+"-"*32)
    for asm,word in pairs:
        print(f"{asm:<40} | {word_to_hex(word):<10} | {word_to_bin(word)}")


if __name__ == "__main__":
    main()
