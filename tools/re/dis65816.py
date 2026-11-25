"""Disassembler 65816 minimo para ROM HiROM (bancos $C0-$FF, $40-$7D, $80-$BF:8000+, $00-$3F:8000+).

Uso: python3 tools/re/dis65816.py C2:57D4 30 [m16|m8] [x16|x8]
"""
import os
import sys

ROM_PATH = os.environ.get("SB4_ROM", os.path.expanduser("~/Downloads/Super Bomberman 4 (Japan).sfc"))
ROM = open(ROM_PATH, "rb").read()

# (mnemonic, mode)
OPS = {}
_t = """
00 BRK i8;01 ORA dpxi;02 COP i8;03 ORA sr;04 TSB dp;05 ORA dp;06 ASL dp;07 ORA dpil;08 PHP imp;09 ORA im;0A ASL acc;0B PHD imp;0C TSB ab;0D ORA ab;0E ASL ab;0F ORA lg
10 BPL rel;11 ORA dpiy;12 ORA dpi;13 ORA sriy;14 TRB dp;15 ORA dpx;16 ASL dpx;17 ORA dpily;18 CLC imp;19 ORA aby;1A INC acc;1B TCS imp;1C TRB ab;1D ORA abx;1E ASL abx;1F ORA lgx
20 JSR ab;21 AND dpxi;22 JSL lg;23 AND sr;24 BIT dp;25 AND dp;26 ROL dp;27 AND dpil;28 PLP imp;29 AND im;2A ROL acc;2B PLD imp;2C BIT ab;2D AND ab;2E ROL ab;2F AND lg
30 BMI rel;31 AND dpiy;32 AND dpi;33 AND sriy;34 BIT dpx;35 AND dpx;36 ROL dpx;37 AND dpily;38 SEC imp;39 AND aby;3A DEC acc;3B TSC imp;3C BIT abx;3D AND abx;3E ROL abx;3F AND lgx
40 RTI imp;41 EOR dpxi;42 WDM i8;43 EOR sr;44 MVP blk;45 EOR dp;46 LSR dp;47 EOR dpil;48 PHA imp;49 EOR im;4A LSR acc;4B PHK imp;4C JMP ab;4D EOR ab;4E LSR ab;4F EOR lg
50 BVC rel;51 EOR dpiy;52 EOR dpi;53 EOR sriy;54 MVN blk;55 EOR dpx;56 LSR dpx;57 EOR dpily;58 CLI imp;59 EOR aby;5A PHY imp;5B TCD imp;5C JML lg;5D EOR abx;5E LSR abx;5F EOR lgx
60 RTS imp;61 ADC dpxi;62 PER rell;63 ADC sr;64 STZ dp;65 ADC dp;66 ROR dp;67 ADC dpil;68 PLA imp;69 ADC im;6A ROR acc;6B RTL imp;6C JMP abi;6D ADC ab;6E ROR ab;6F ADC lg
70 BVS rel;71 ADC dpiy;72 ADC dpi;73 ADC sriy;74 STZ dpx;75 ADC dpx;76 ROR dpx;77 ADC dpily;78 SEI imp;79 ADC aby;7A PLY imp;7B TDC imp;7C JMP abxi;7D ADC abx;7E ROR abx;7F ADC lgx
80 BRA rel;81 STA dpxi;82 BRL rell;83 STA sr;84 STY dp;85 STA dp;86 STX dp;87 STA dpil;88 DEY imp;89 BIT im;8A TXA imp;8B PHB imp;8C STY ab;8D STA ab;8E STX ab;8F STA lg
90 BCC rel;91 STA dpiy;92 STA dpi;93 STA sriy;94 STY dpx;95 STA dpx;96 STX dpy;97 STA dpily;98 TYA imp;99 STA aby;9A TXS imp;9B TXY imp;9C STZ ab;9D STA abx;9E STZ abx;9F STA lgx
A0 LDY ix;A1 LDA dpxi;A2 LDX ix;A3 LDA sr;A4 LDY dp;A5 LDA dp;A6 LDX dp;A7 LDA dpil;A8 TAY imp;A9 LDA im;AA TAX imp;AB PLB imp;AC LDY ab;AD LDA ab;AE LDX ab;AF LDA lg
B0 BCS rel;B1 LDA dpiy;B2 LDA dpi;B3 LDA sriy;B4 LDY dpx;B5 LDA dpx;B6 LDX dpy;B7 LDA dpily;B8 CLV imp;B9 LDA aby;BA TSX imp;BB TYX imp;BC LDY abx;BD LDA abx;BE LDX aby;BF LDA lgx
C0 CPY ix;C1 CMP dpxi;C2 REP i8;C3 CMP sr;C4 CPY dp;C5 CMP dp;C6 DEC dp;C7 CMP dpil;C8 INY imp;C9 CMP im;CA DEX imp;CB WAI imp;CC CPY ab;CD CMP ab;CE DEC ab;CF CMP lg
D0 BNE rel;D1 CMP dpiy;D2 CMP dpi;D3 CMP sriy;D4 PEI dpi;D5 CMP dpx;D6 DEC dpx;D7 CMP dpily;D8 CLD imp;D9 CMP aby;DA PHX imp;DB STP imp;DC JML abil;DD CMP abx;DE DEC abx;DF CMP lgx
E0 CPX ix;E1 SBC dpxi;E2 SEP i8;E3 SBC sr;E4 CPX dp;E5 SBC dp;E6 INC dp;E7 SBC dpil;E8 INX imp;E9 SBC im;EA NOP imp;EB XBA imp;EC CPX ab;ED SBC ab;EE INC ab;EF SBC lg
F0 BEQ rel;F1 SBC dpiy;F2 SBC dpi;F3 SBC sriy;F4 PEA i16;F5 SBC dpx;F6 INC dpx;F7 SBC dpily;F8 SED imp;F9 SBC aby;FA PLX imp;FB XCE imp;FC JSR abxi;FD SBC abx;FE INC abx;FF SBC lgx
"""
for entry in _t.replace("\n", ";").split(";"):
    entry = entry.strip()
    if not entry:
        continue
    code, mn, mode = entry.split()
    OPS[int(code, 16)] = (mn, mode)
assert len(OPS) == 256, len(OPS)

FMT = {
    "imp": "", "acc": "A", "i8": "#${0:02X}", "i16": "${0:04X}",
    "dp": "${0:02X}", "dpx": "${0:02X},X", "dpy": "${0:02X},Y", "dpi": "(${0:02X})", "dpxi": "(${0:02X},X)",
    "dpiy": "(${0:02X}),Y", "dpil": "[${0:02X}]", "dpily": "[${0:02X}],Y", "sr": "${0:02X},S", "sriy": "(${0:02X},S),Y",
    "ab": "${0:04X}", "abx": "${0:04X},X", "aby": "${0:04X},Y", "abi": "(${0:04X})", "abxi": "(${0:04X},X)", "abil": "[${0:04X}]",
    "lg": "${0:06X}", "lgx": "${0:06X},X",
}


def rom_offset(addr24):
    bank, off = addr24 >> 16, addr24 & 0xFFFF
    if bank >= 0xC0:
        return ((bank - 0xC0) << 16) | off
    if 0x40 <= bank < 0x7E:
        return ((bank - 0x40) << 16) | off
    if 0x80 <= bank < 0xC0 and off >= 0x8000:
        return ((bank - 0x80) << 16) | off
    if bank < 0x40 and off >= 0x8000:
        return (bank << 16) | off
    raise ValueError("not ROM: %06X" % addr24)


def rd(addr24, n):
    o = rom_offset(addr24)
    return ROM[o:o + n]


def insn_len(op, m16, x16):
    mn, mode = OPS[op]
    if mode in ("imp", "acc"):
        return 1
    if mode == "im":
        return 3 if m16 else 2
    if mode == "ix":
        return 3 if x16 else 2
    if mode in ("i8", "dp", "dpx", "dpy", "dpi", "dpxi", "dpiy", "dpil", "dpily", "sr", "sriy", "rel"):
        return 2
    if mode in ("ab", "abx", "aby", "abi", "abxi", "abil", "rell", "blk", "i16"):
        return 3
    if mode in ("lg", "lgx"):
        return 4
    raise ValueError(mode)


def disasm_one(addr24, m16, x16):
    op = rd(addr24, 1)[0]
    mn, mode = OPS[op]
    n = insn_len(op, m16, x16)
    b = rd(addr24, n)
    arg = int.from_bytes(b[1:], "little") if n > 1 else 0
    pc = addr24 & 0xFFFF
    bank = addr24 & 0xFF0000
    if mode == "rel":
        tgt = (pc + 2 + (arg - 256 if arg >= 128 else arg)) & 0xFFFF
        s = "$%04X" % tgt
    elif mode == "rell":
        tgt = (pc + 3 + (arg - 65536 if arg >= 32768 else arg)) & 0xFFFF
        s = "$%04X" % tgt
    elif mode == "blk":
        s = "$%02X,$%02X" % (b[2], b[1])
    elif mode in ("im", "ix"):
        s = ("#$%04X" if n == 3 else "#$%02X") % arg
    else:
        s = FMT[mode].format(arg)
    # track REP/SEP
    nm16, nx16 = m16, x16
    if mn == "REP":
        if arg & 0x20: nm16 = True
        if arg & 0x10: nx16 = True
    if mn == "SEP":
        if arg & 0x20: nm16 = False
        if arg & 0x10: nx16 = False
    return n, "%-4s%s" % (mn, (" " + s) if s else ""), b, nm16, nx16


def linear(addr24, count, m16=True, x16=True):
    out = []
    a = addr24
    for _ in range(count):
        n, txt, b, m16, x16 = disasm_one(a, m16, x16)
        out.append("%02X:%04X  %-12s %s" % (a >> 16, a & 0xFFFF, " ".join("%02X" % c for c in b), txt))
        a = (a & 0xFF0000) | ((a + n) & 0xFFFF)
    return "\n".join(out)


if __name__ == "__main__":
    a = int(sys.argv[1].replace(":", ""), 16)
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    m = (sys.argv[3] if len(sys.argv) > 3 else "m16")
    x = (sys.argv[4] if len(sys.argv) > 4 else "x16")
    print(linear(a, n, m == "m16", x == "x16"))
