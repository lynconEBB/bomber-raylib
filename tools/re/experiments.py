"""Experimentos de engenharia reversa do Super Bomberman 4 (modo Battle).

Uso (a partir da raiz do repo):
  python3 -I tools/re/experiments.py mkstate     # navega os menus e salva out/battle_start.mss
  python3 -I tools/re/experiments.py move        # P1 anda p/ direita e p/ baixo; mostra o struct do P1
  python3 -I tools/re/experiments.py bomb        # P1 poe bomba; mostra fuse, explosao e mapa
  python3 -I tools/re/experiments.py trace 63    # trace de CPU de um frame (P1 andando) -> out/trace.txt
  python3 -I tools/re/experiments.py speeds      # tabela de velocidades lida direto da ROM
  python3 -I tools/re/experiments.py map         # mapa logico da arena no inicio da partida

Tecnica principal: "diff de execucoes". O emulador e deterministico, entao
rodamos o mesmo savestate duas vezes (com e sem um input) e comparamos a
WRAM frame a frame. O que diverge primeiro e causado pelo input.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

import dis65816 as D  # noqa: E402
import mesen  # noqa: E402

P1 = 0x0300            # struct do jogador 1 (jogador n: $0300 + n*$100)
MAP = 0x2802           # celula (0,0) da arena; celula = 16 bits
MAP_ROW = 0x40         # bytes por linha do mapa


def wram_series(res):
    keys = sorted(res["WRAM"])
    return np.stack([np.frombuffer(res["WRAM"][k], dtype=np.uint8) for k in keys]).astype(np.int32)


def record(body_inputs, frames, name):
    body = body_inputs + """
emu.addEventCallback(function()
  frame = frame + 1
  if loaded and frame >= 1 and frame <= %d then wram(string.format('w%%04d', frame)) end
  if loaded and frame >= %d then emu.stop(0) end
end, emu.eventType.endFrame)
""" % (frames, frames)
    return wram_series(mesen.run_from_state("battle_start", body, name=name))


def cmd_mkstate():
    # Sem input durante a intro: a emulacao fica deterministica e o titulo aparece ~frame 5400.
    body = """
hold(5600, 5603, 0, {down=true})   -- titulo: cursor em BATTLE GAME
hold(5640, 5643, 0, {start=true})
hold(5900, 5903, 0, {a=true})      -- Battle Royal
hold(6100, 6103, 0, {a=true})      -- Single Match
hold(6300, 6303, 0, {a=true})      -- jogadores: 1P/2P MAN, 3-5 COM
hold(6500, 6503, 0, {start=true})  -- regras padrao (3 vitorias, 3:00, opcoes OFF)
for i = 0, 8 do hold(6800 + i*40, 6803 + i*40, 0, {a=true}); hold(6820 + i*40, 6823 + i*40, 1, {a=true}) end -- personagens + Stage 1
local saved = false
emu.addMemoryCallback(function()
  if frame == 7560 and not saved then
    saved = true
    out('BIN', 'battle_start', hexstr(emu.createSavestate()))
  end
end, emu.callbackType.exec, 0xF001, 0xF001)  -- entrada do handler de NMI
emu.addEventCallback(function()
  frame = frame + 1
  if frame == 7560 then shot('battle_start') end
  if frame >= 7562 then emu.stop(0) end
end, emu.eventType.endFrame)
"""
    r = mesen.run(body, name="mkstate")
    st = r["BIN"].get("battle_start")
    if not st:
        raise SystemExit("falhou ao criar o savestate")
    open(os.path.join(mesen.OUT, "battle_start.mss"), "wb").write(st)
    print("ok: out/battle_start.mss (%d bytes), screenshot out/battle_start.png" % len(st))


def cmd_move():
    a = record("hold(60, 99, 0, {right=true})\nhold(130, 169, 0, {down=true})", 200, "move")
    b = record("", 200, "idle")
    diff = (a != b)
    first = np.where(diff.any(0), diff.argmax(0) + 1, 0)
    addrs = np.where(first > 0)[0]
    print("enderecos que divergem (input do P1 -> efeito):", len(addrs))
    for i in addrs[np.argsort(first[addrs], kind="stable")][:25]:
        print("  $%05X  primeiro frame %d" % (i, first[i]))
    blk = a[:, P1:P1 + 0x100]
    offs = [0x0B, 0x11, 0x12, 0x15, 0x16, 0x31, 0x40, 0x60, 0x64, 0x65, 0x66]
    print("\nframe inp " + " ".join("+%02X" % o for o in offs))
    for f in list(range(58, 80)) + list(range(128, 146)):
        inp = "R" if 60 <= f <= 99 else ("D" if 130 <= f <= 169 else ".")
        print("%4d   %s  " % (f, inp) + " ".join(" %02x" % blk[f - 1, o] for o in offs))


def cmd_bomb():
    walk = "hold(70, 110, 0, {right=true})\n"
    a = record("hold(60, 61, 0, {a=true})\n" + walk, 300, "bomb")
    b = record(walk, 300, "nobomb")
    fuse = a[:, 0x08AA]
    start = int(np.argmax(fuse != b[:, 0x08AA])) + 1
    end = start + int(np.argmax(fuse[start:] == 0)) + 1
    dec = int(sum(1 for f in range(start, end) if fuse[f] == fuse[f - 1] - 1))
    print("bomba no slot $0890; fuse em $08AA comeca em $%02X, chega a 0 no frame %d (%d decrementos = ticks de logica)"
          % (fuse[start - 1], end, dec))

    def cell(f, c, r):
        o = MAP + r * MAP_ROW + c * 2
        return a[f - 1, o] | (a[f - 1, o + 1] << 8)
    for f in (start, end, end + 5, end + 40, 300):
        print("frame %3d  " % f + "  ".join("(%d,%d)=%04X" % (c, r, cell(f, c, r))
                                           for (c, r) in ((1, 1), (2, 1), (3, 1), (1, 2), (1, 3))))


def cmd_trace(frame_no):
    body = """
hold(60, 99, 0, {right=true})
local tracing = false
local buf = {}
emu.addMemoryCallback(function()
  if not tracing then return end
  local s = emu.getState()
  buf[#buf+1] = string.format('%%02X%%04X %%02X %%04X %%04X %%04X', s['cpu.k'], s['cpu.pc'], s['cpu.ps'], s['cpu.a'], s['cpu.x'], s['cpu.y'])
end, emu.callbackType.exec, 0x000000, 0xFFFFFF)
emu.addEventCallback(function()
  if loaded and frame == %d then tracing = true end
  if loaded and frame == %d then tracing = false; print('@TRACE t ' .. table.concat(buf, '|')); emu.stop(0) end
end, emu.eventType.startFrame)
emu.addEventCallback(function() frame = frame + 1 end, emu.eventType.endFrame)
""" % (frame_no, frame_no + 1)
    r = mesen.run_from_state("battle_start", body, name="trace")
    lines = [l for l in r["LOG"] if l.startswith("@TRACE")][0].split(" ", 2)[2].split("|")
    out = []
    for ln in lines:
        f = ln.split()
        pc, p = int(f[0], 16), int(f[1], 16)
        n, txt, bts, _, _ = D.disasm_one(pc, not (p & 0x20), not (p & 0x10))
        out.append("%02X:%04X  %-12s %-22s A=%s X=%s Y=%s P=%s" % (
            pc >> 16, pc & 0xFFFF, " ".join("%02X" % c for c in bts), txt, f[2], f[3], f[4], f[1]))
    path = os.path.join(mesen.OUT, "trace.txt")
    open(path, "w").write("\n".join(out))
    print("%d instrucoes -> %s (procure por C2:2FC4 = calculo da velocidade)" % (len(out), path))


def cmd_speeds():
    names = ["cima", "cima-dir", "dir", "baixo-dir", "baixo", "baixo-esq", "esq", "cima-esq"]
    print("tabela C3:2A50, 64 bytes por nivel, 4 bytes por direcao (dx,dy em 8.8)")
    for lvl in range(8):
        blk = D.rd(0xC32A50 + lvl * 64, 32)
        vals = []
        for d in range(8):
            dx = int.from_bytes(blk[d * 4:d * 4 + 2], "little", signed=True)
            dy = int.from_bytes(blk[d * 4 + 2:d * 4 + 4], "little", signed=True)
            vals.append("%s=(%+d,%+d)" % (names[d], dx, dy))
        print("nivel %d (%.4f px/frame): %s" % (lvl, abs(int.from_bytes(D.rd(0xC32A50 + lvl * 64 + 2, 2), "little", signed=True)) / 256, " ".join(vals)))


def cmd_map():
    a = record("", 2, "map")
    sym = {0x00: ".", 0x40: "#", 0x80: "+"}
    for r in range(13):
        row = ""
        for c in range(15):
            o = MAP + r * MAP_ROW + c * 2
            row += sym.get(a[0, o], "?")
        print(row)
    print("# = bloco fixo ($40)   + = bloco destrutivel ($80)   . = chao ($00)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "mkstate":
        cmd_mkstate()
    elif cmd == "move":
        cmd_move()
    elif cmd == "bomb":
        cmd_bomb()
    elif cmd == "trace":
        cmd_trace(int(sys.argv[2]) if len(sys.argv) > 2 else 63)
    elif cmd == "speeds":
        cmd_speeds()
    elif cmd == "map":
        cmd_map()
    else:
        print(__doc__)
