# 🛠️ ARMv7 Data Processing Instruction Assembler & Disassembler

This project is a high-speed, parallelized **assembler and disassembler** for **ARMv7-A Data Processing Instructions only** (e.g., `ADD`, `SUB`, `MOV`, `CMP`, etc.), written entirely in **Python**. It is designed for education, testing, and tooling development.

> 🔄 **Note:** This project currently supports **only Data Processing instructions**, but is being actively developed and will **expand to support all ARMv7 instruction categories**, including memory access (`LDR`, `STR`), branches, system instructions, and Thumb.

---

## 📌 Key Features

- ✅ **Only supports ARMv7-A (A32) Data Processing Instructions**
- ✅ Works with immediate operands (e.g., `#5`)
- ✅ Supports all **conditional suffixes** (e.g., `ADDEQ`, `MOVNE`)
- ✅ Fast and scalable via **multi-core parallelism**
- ✅ Clean, extensible, and modular Python code
- ✅ CLI to convert instruction files to/from hex

---

## 🧠 What Are ARMv7 Data Processing Instructions?

These are core 32-bit instructions used for arithmetic, logical, and move operations.

### Supported Instructions:

| Type         | Mnemonics |
|--------------|-----------|
| Arithmetic   | `ADD`, `SUB`, `RSB`, `ADC`, `SBC`, `RSC` |
| Logical      | `AND`, `ORR`, `EOR`, `BIC` |
| Move         | `MOV`, `MVN` |
| Comparison   | `CMP`, `CMN`, `TST`, `TEQ` |

All instructions support condition codes: `EQ`, `NE`, `GE`, `AL`, etc.

Example:
```asm
ADDEQ R1, R2, #10
CMPNE R0, #100


## 📦 Project Structure
armv7_dp/
├── assembler.py        # Encodes instructions to 32-bit binary
├── disassembler.py     # Decodes binary to assembly string
├── parser.py           # Parses assembly line into fields
├── cli.py              # CLI interface (assemble/disassemble in parallel)
└── __init__.py

test_cases.py           # Test runner and sample usage
README.md               # You're reading it


## 🚀 How to Use

### 🔧 Assemble a `.s` file into hex machine instructions

```bash
python -m armv7_dp.cli asm input.s -j 0 > output.hex

- **asm:** mode for assembling
- **input.s:** file with ARMv7 data processing instructions (one per line)
- **-j 0:** use all available CPU cores (parallel processing)
- **> output.hex:** save results in hex format


## 🔍 Disassemble a hex file back to readable assembly

```bash
python -m armv7_dp.cli dis output.hex -j 0

- **dis:** mode for disassembling
- **output.hex:** file with 32-bit ARM instructions in hex (e.g. **0xE281100A**)
- Output will be printed as human-readable ARM assembly 


## 🧪 Input/Output Examples
### 📝 Example input.s

```asm
ADD R1, R1, #10
MOVNE R0, #100
CMP R3, #255


### 🧾 Resulting Hex Output

```text
0xE281100A
0x13A00064
0xE35300FF


### 🔁 Disassembled Output

```asm
ADDAL R1, R1, #10
MOVNE R0, #100
CMPAL R3, #255

## ⚙️ How It Works

1. **Parsing**: The `parser.py` module breaks each line into:
   - Mnemonic (`ADD`)
   - Condition (`EQ`, `NE`, etc.)
   - Destination register
   - Source register
   - Immediate operand

2. **Assembling**:
   - Maps mnemonics and condition codes to binary opcodes
   - Encodes immediate using ARM’s rotated `imm12` format
   - Outputs final 32-bit binary instruction

3. **Disassembling**:
   - Reads a 32-bit hex word
   - Extracts opcode, register IDs, condition
   - Reconstructs readable assembly line

4. **Parallelism**:
   - Files are split into batches
   - Batches are processed using `ProcessPoolExecutor`
   - Merged in correct order for large-scale performance


## 🔥 Performance

The assembler/disassembler is capable of processing **thousands of instructions per second** using all available CPU cores. The multi-processing architecture allows handling large `.s` or `.hex` files efficiently and reliably.


## 📦 Requirements

- Python **3.7 or higher**
- No external libraries needed
- Works cross-platform (Linux, Windows, macOS)


## 🧱 Limitations (By Design)
❌ Not yet supported:
- Register-to-register operands (e.g., ADD R1, R2, R3)
- Register shifts (LSL, ASR, etc.)
- Load/store instructions (LDR, STR, etc.)
- Branch instructions (B, BL, BX)
- Floating-point and NEON instructions
- Thumb (T32) mode
- ELF or binary image export
✅ These are part of the roadmap and will be added progressively.


## 📈 Roadmap

- [x] Assemble/disassemble ARMv7 Data Processing (immediate mode)
- [ ] Register-to-register operands (`ADD R0, R1, R2`)
- [ ] `S`-bit variants (`ADDS`, `SUBS`)
- [ ] Register-shifted operand support (`LSL`, `ASR`)
- [ ] Branch instructions (`B`, `BL`, `BX`)
- [ ] Load/store instructions (`LDR`, `STR`)
- [ ] Thumb (`T32`) disassembly support
- [ ] `.bin` or ELF output support
- [ ] Full instruction coverage for ARMv7-A (A32)


## 📜 License
This project is licensed under the MIT License.
See the LICENSE file for details.


## 👨‍💻 Maintainer
Developed and maintained by Labiba Faiza Karim
Contributions and forks are welcome. If you'd like to submit fixes or enhancements, feel free to open an issue or a pull request.

## 🌐 Connect
For queries or collaboration, reach out at:
- **Email**: [karim.labibafaiza2002@gmail.com]
- **LinkedIn**: [https://www.linkedin.com/in/labiba-faiza-karim-6057b8217/]