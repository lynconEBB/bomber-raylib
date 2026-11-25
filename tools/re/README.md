# tools/re: engenharia reversa com MesenCE headless

Scripts para rodar o Super Bomberman 4 sem janela, injetar inputs, despejar a
WRAM a cada frame e gravar traces de CPU. As descobertas ficam em
`docs/re/super-bomberman-4.md`.

## Setup

1. Instale o MesenCE (fork mantido do Mesen2) em `/opt/mesence`, conferindo o SHA-256 do release:

   ```sh
   sudo install -d -o "$USER" -g "$USER" /opt/mesence   # a pasta precisa ser sua: o Mesen grava nela
   cd /tmp
   curl -LO https://github.com/nesdev-org/MesenCE/releases/download/2.2.1/Mesen_2.2.1_Linux_x64.zip
   echo "c88ff4d251b407515c43d3332d641927655cd69fb538996b6a21da4509dbb58f  Mesen_2.2.1_Linux_x64.zip" | sha256sum -c
   unzip Mesen_2.2.1_Linux_x64.zip -d /opt/mesence
   echo '{}' > /opt/mesence/settings.json   # modo portátil: config fica na pasta, não em ~/.config/Mesen2
   ```

   E no `~/.bashrc`: `export PATH="$PATH:/opt/mesence"`.

   Obs.: o Mesen2 antigo (SourMesen 2.1.1) quebra com `std::bad_cast` nesta distro.

2. Os scripts acham o Mesen sozinhos (PATH, depois `/opt/mesence/Mesen`). Para sobrescrever:

   ```sh
   export MESEN=/outro/caminho/Mesen
   export SB4_ROM=~/Downloads/"Super Bomberman 4 (Japan).sfc"   # padrão
   ```

3. Python 3 com `numpy`.

## Uso

```sh
python3 -I tools/re/experiments.py mkstate   # 1x: cria tools/re/out/battle_start.mss
python3 -I tools/re/experiments.py map
python3 -I tools/re/experiments.py speeds
python3 -I tools/re/experiments.py move
python3 -I tools/re/experiments.py bomb
python3 -I tools/re/experiments.py trace 63
python3 -I tools/re/dis65816.py C2:2FC4 40   # disassembly linear (m16/x16 por padrão)
```

Tudo que é gerado vai para `tools/re/out/` (ignorado pelo git): savestates,
screenshots, scripts Lua gerados e traces.

## Técnicas usadas

- **Diff de execuções**: a emulação é determinística. Rodamos o mesmo savestate
  com e sem um input; os bytes que divergem primeiro são os afetados pelo input.
- **Callback de escrita**: `emu.addMemoryCallback(..., write, addr, addr, cpuType.snes, memType.snesWorkRam)`
  + `emu.getState()['cpu.pc']` mostra qual instrução escreveu no endereço.
- **Trace de execução**: callback de `exec` em toda a faixa, salvando PC + flags.
  Com as flags M/X de cada instrução o disassembly 65816 sai exato.

## Quirks do MesenCE 2.2.1

- `emu.setInput(tabela, _, porta)`: o **terceiro** argumento é a porta.
- `createSavestate`/`loadSavestate` só funcionam dentro de callback de `exec`.
- Sem `--snes.port1.type=SnesController` nenhum controle fica conectado.
- O Lua roda no sandbox padrão (sem `io`/`os`); tudo sai pelo stdout (`--enablestdout`).
