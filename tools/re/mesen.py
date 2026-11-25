"""Driver minimo para o MesenCE em modo headless (--testrunner).

Gera um script Lua (sandbox padrao: sem io/os), roda o emulador sem janela e
le do stdout linhas no formato:  @TAG nome hexdata
  @PNG  -> screenshot
  @WRAM -> dump dos 128 KB de WRAM ($7E0000-$7FFFFF)
  @BIN  -> blob qualquer (ex.: savestate)

Variaveis de ambiente:
  MESEN    caminho do executavel do MesenCE (padrao: Mesen no PATH, senao /opt/mesence/Mesen)
  SB4_ROM  caminho da ROM (padrao: ~/Downloads/Super Bomberman 4 (Japan).sfc)

Quirks do MesenCE 2.2.1 descobertos na pratica:
  - emu.setInput(tabela, _, porta): o TERCEIRO argumento e a porta.
  - createSavestate/loadSavestate so funcionam dentro de um callback de exec.
  - sem settings.json ao lado do executavel ele usa ~/.config/Mesen2.
  - controles precisam ser ligados via --snes.port1.type=SnesController.
"""
import binascii
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
MESEN = os.environ.get("MESEN") or shutil.which("Mesen") or "/opt/mesence/Mesen"
ROM = os.environ.get("SB4_ROM", os.path.expanduser("~/Downloads/Super Bomberman 4 (Japan).sfc"))

LUA_PRELUDE = r"""
local WRAM = emu.memType.snesWorkRam
local function hexstr(s)
  return (s:gsub('.', function(c) return string.format('%02x', string.byte(c)) end))
end
local function out(tag, name, data) print('@' .. tag .. ' ' .. name .. ' ' .. data) end
local function shot(name) out('PNG', name, hexstr(emu.takeScreenshot())) end
local function wram(name)
  local t = {}
  for i = 0, 0x1FFFF do t[#t+1] = string.format('%02x', emu.read(i, WRAM)) end
  out('WRAM', name, table.concat(t))
end
local frame = 0
local schedule = {}     -- lista de {de, ate, porta, botoes}
local function hold(from, to, port, buttons) schedule[#schedule+1] = {from, to, port, buttons} end
emu.addEventCallback(function()
  for port = 0, 1 do
    local b = {a=false,b=false,x=false,y=false,l=false,r=false,select=false,start=false,up=false,down=false,left=false,right=false}
    for _, s in ipairs(schedule) do
      if frame >= s[1] and frame <= s[2] and s[3] == port then
        for k, v in pairs(s[4]) do b[k] = v end
      end
    end
    emu.setInput(b, 0, port)  -- MesenCE 2.2.1: o 3o argumento e a porta
  end
end, emu.eventType.inputPolled)
"""

# Carrega o savestate na primeira instrucao executada (banco $00) e remove o callback.
STATE_LOADER = r"""
local function unhex(h) return (h:gsub('..', function(c) return string.char(tonumber(c, 16)) end)) end
local loaded = false
local loader_ref
loader_ref = emu.addMemoryCallback(function()
  if not loaded then
    loaded = true
    emu.loadSavestate(unhex(STATE_HEX))
    STATE_HEX = nil
    frame = 0
    emu.removeMemoryCallback(loader_ref, emu.callbackType.exec, 0x008000, 0x00FFFF)
  end
end, emu.callbackType.exec, 0x008000, 0x00FFFF)
"""


def _check():
    if not MESEN or not os.path.isfile(MESEN):
        raise SystemExit("MesenCE nao encontrado (%r). Instale em /opt/mesence ou defina MESEN (veja tools/re/README.md)" % MESEN)
    if not os.path.isfile(ROM):
        raise SystemExit("ROM nao encontrada: %s (defina SB4_ROM)" % ROM)
    os.makedirs(OUT, exist_ok=True)


def run(lua_body, name="run", timeout=300):
    _check()
    path = os.path.join(OUT, name + ".lua")
    with open(path, "w") as f:
        f.write(LUA_PRELUDE + "\n" + lua_body)
    p = subprocess.run(
        [MESEN, "--testrunner", path, ROM, "--enablestdout", "--timeout=%d" % timeout,
         "--snes.port1.type=SnesController", "--snes.port2.type=SnesController"],
        cwd=os.path.dirname(MESEN), capture_output=True, text=True, timeout=timeout + 30,
    )
    res = {"PNG": {}, "WRAM": {}, "BIN": {}, "LOG": [], "rc": p.returncode, "stderr": p.stderr}
    for line in p.stdout.splitlines():
        if line.startswith("@"):
            tag, nm, data = line[1:].split(" ", 2)
            if tag in ("PNG", "WRAM", "BIN"):
                blob = binascii.unhexlify(data)
                res[tag][nm] = blob
                if tag == "PNG":
                    with open(os.path.join(OUT, nm + ".png"), "wb") as f:
                        f.write(blob)
            else:
                res["LOG"].append(line)
        elif not line.startswith("[CPU] Uninitialized memory read"):
            res["LOG"].append(line)
    return res


def run_from_state(state_name, lua_body, name="exp", timeout=300):
    path = os.path.join(OUT, state_name + ".mss")
    if not os.path.isfile(path):
        raise SystemExit("Savestate %s nao existe. Rode primeiro: python3 tools/re/experiments.py mkstate" % path)
    st = open(path, "rb").read()
    body = "STATE_HEX = '" + st.hex() + "'\n" + STATE_LOADER + "\n" + lua_body
    return run(body, name=name, timeout=timeout)
