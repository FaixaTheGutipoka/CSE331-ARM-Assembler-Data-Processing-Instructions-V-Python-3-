import argparse, fileinput, re, sys, multiprocessing, time
# from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple
# from itertools import islice

\

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

# Data Transfer instructions
DataTransfer = {
    "LDR", 
    "STR"
}                      

# 2. Simple regex tokenizer / parser
Token = re.compile(r"""^\s*
    (?P<mnemonic>[A-Z]{2,3})(?P<cond>[A-Z]{2})? \s+
    R(?P<Rd>\d{1,2})
    (?:                                 # ── DP form ──
        (?:\s*,\s*R(?P<Rn>\d{1,2}))? \s*,\s*
        (?:
            \#(?P<imm>0x[0-9A-Fa-f]+|-?\d+) |          # ← here
            R(?P<Rm>\d{1,2})
            (?:\s*,?\s*(?P<shiftop>LSL|LSR|ASR|ROR|RRX)
                (?:\s*\#(?P<shiftimm>\d+))?)?
        )
    |
        \s*,\s*\[R(?P<base>\d{1,2}),\s*\#(?P<dt_imm>0x[0-9A-Fa-f]+|\d+)\]   # ← and here
    )
    \s*$""", re.VERBOSE | re.IGNORECASE)


# 3. Parser
def parse_line(line: str):

    """
    Return a tuple that tells the encoder what to do.

    • For data-transfer  :  ("DT",  mn,  cond, Rd, Rn, imm12)
    • For data-processing:  (mn,   cond, Rd, Rn, op2, is_imm, shiftop, shiftimm)
    
    """

    match = Token.match(line)                                                       # match the line against the regex pattern

    if not match:
        raise ValueError(f"syntax error: «{line.strip()}»")                         # raise an error if the line doesn't match the expected format

    mnemonic = match.group("mnemonic").upper()                                      # convert mnemonic to uppercase. addne or AdD is treated the same as ADD
    cond = (match.group("cond") or "AL").upper()
    Rd = int(match.group("Rd"))                                                     # destination register
    Rn = int(match.group("Rn") or 0)                                    # default to AL (always) if no condition is specified
        
    if mnemonic in DataTransfer and match.group("base"):
        Rn  = int(match.group("base"))
        off = int(match.group("dt_imm"), 0)    # base-0 again
        return ("DT", mnemonic, cond, Rd, Rn, off)                                                # optional first operand
    
    if match.group("imm") is not None:
        imm_val = int(match.group("imm"), 0)   # base-0 converts 0x, 0o, 0b, decimal
        return mnemonic, cond, Rd, Rn, imm_val, True, None, None
    
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


# 4. Encodes
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


# 5. Assemble instructions → 32-bit word
def assemble_one(mnem, cond, Rd, Rn, op2, is_imm, shiftop, shiftimm):

    """
    The goal of the function is to turn one parsed data processing assembly instruction into the
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


def assemble_transfer(mnemonic: str, cond: str, Rd: int, Rn:int, imm12: int) -> int:
    
    """
    The goal of the function is to turn one parsed data transferring assembly instruction into the
    exact 32-bit machine word that ARMv7 expects in hexadecimal format.
    """

    if not (0 <= imm12 <= 0xFFF):
        raise ValueError("offset must be 0-4095")
    
    L = 1 if mnemonic == "LDR" else 0
    cond_bits = Cond.get(cond, 0xE)

    return (
        (cond_bits << 28) |     # cond[31:28]
        (0b01   << 26)  |       # 01 = Single data transfer
        (1      << 24)  |       # P=1 (pre-index)
        (1      << 23)  |       # U=1 (add offset)
        (0      << 21)  |       # W=0 (no write-back)
        (L      << 20)  |       # L=1 load, 0 store
        (Rn     << 16)  |       # base register
        (Rd     << 12)  |       # destination/source register
        imm12                   # 12-bit immediate offset
    )

'''
# 6. Chunck helper
def chunked(iterable, size):
    it = iter(iterable)
    while True:
        batch = list(islice(it, size))
        if not batch:
            return
        yield batch

# 7. top-level worker (must be picklable!): for parallel processing
def worker_batch(idx_batch: int,
                 lines_batch: List[str],
                 batch_size: int
                ) -> List[Tuple[int, str, int]]:
    """
    Assemble one batch of lines:
      - idx_batch: which batch number (0-based)
      - lines_batch: list of source lines
      - batch_size: size of each batch, so we can compute the original line numbers

    Returns a list of tuples (original_line_index, source_text, machine_word).
    """
    results = []
    base = idx_batch * batch_size
    for offset, line in enumerate(lines_batch):
        src = line.partition(";")[0].strip()
        if not src:
            continue
        word = assemble_one(*parse_line(src))
        results.append((base + offset + 1, src, word))
    return results

def worker_batch_star(args):
    """
    Unpack a single tuple (idx_batch, lines_batch, batch_size)
    and call worker_batch.
    """
    return worker_batch(*args)

'''

# 8.  Serial & Parallel assemblers
def assemble_serial(lines:List[str])->List[Tuple[str,int]]:                 
    machine=[]
    for idx, line in enumerate(lines,1):                                                # Enumerate lines starting from 1
        src=line.partition(";")[0].strip()                                             # Remove inline comments and whitespace
        if not src: continue                                                        # Skip blank or comment-only lines
        try:
            parsed = parse_line(src)
            if parsed[0] == "DT":
                _, mnemonic, cond, Rd, Rn, imm = parsed
                word = assemble_transfer(mnemonic, cond, Rd, Rn, imm)
            else:
                word = assemble_one(*parsed)
            machine.append((src, word))                       # Parse and assemble the instruction
        except Exception as e: 
            raise RuntimeError(f"[line {idx}] {e}") from None       
    return machine


'''
def assemble_parallel(lines: List[str], batch_size: int = 100) -> List[Tuple[str,int]]:
    """
    Split into batches, run worker_batch in parallel via executor.map,
    then flatten & reorder.
    """
    batches = list(chunked(lines, batch_size))
    # Build a list of argument tuples
    args_list = [(i, batch, batch_size) for i, batch in enumerate(batches)]
    with ProcessPoolExecutor() as pool:
        # Use map on the top‐level worker_batch_star
        all_batches = pool.map(worker_batch_star, args_list)
    # Flatten and sort by original line index
    flat = [item for batch in all_batches for item in batch]
    flat.sort(key=lambda t: t[0])
    return [(src, word) for _, src, word in flat]

    '''

# 9. Formatting results
h=lambda w:f"0x{w:08X}"
b=lambda w:f"{w:032b}"
def to_bytes(ws): return b"".join(w.to_bytes(4,"little") for w in ws)



# 10. CLI interface
def main():
    ap = argparse.ArgumentParser(description="ARMv7 DP assembler (serial only)")
    ap.add_argument("files", nargs="*", help="source .s files; stdin if none")
    ap.add_argument("--format", choices=["table","raw"], default="table",
                    help="output format")
    ap.add_argument("--out", help="file for raw output (.bin)")
    args = ap.parse_args()

    lines = list(fileinput.input(args.files or ("-",)))

    # start timer
    t0 = time.perf_counter()
    pairs = assemble_serial(lines)
    elapsed = time.perf_counter() - t0

    if args.format == "raw":
        if not args.out:
            sys.exit("--out FILE required with --format raw")
        with open(args.out, "wb") as f:
            f.write(to_bytes([w for _, w in pairs]))
        print(f"✓ {len(pairs)} instrs in {elapsed:.4f}s (serial)"
              # f"({'parallel' if args.parallel else 'serial'})"
              )
        return

    print(f"{'ASSEMBLY':<40} | {'HEX':<10} | BINARY")
    print("-"*40 + "-+-" + "-"*10 + "-+-" + "-"*32)
    for asm, word in pairs:
        print(f"{asm:<40} | {h(word):<10} | {b(word)}")
    print(f"\n✓ Assembled {len(pairs)} instructions in {elapsed:.4f} s "
          # f"({'parallel' if args.parallel else 'serial'})"
          )

if __name__ == "__main__":
    #multiprocessing.freeze_support()   # for Windows
    main()
