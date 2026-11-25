# BomberC

Jogo estilo Bomberman, **só modo batalha (arena)**, em **C + raylib**, para **Linux e Windows**.
As mecânicas (movimento, timers, itens, montarias) devem ser iguais às do *Super Bomberman 4* (SFC),
obtidas por engenharia reversa. Arte, sons e nome são próprios: da ROM só usamos números.

É um projeto de aprendizado: o objetivo é aprender gamedev de baixo nível e largar o pensamento orientado a objetos.

## Regras

- C puro, sem OOP e sem ECS: "fat structs" em arrays fixos. Simplicidade acima de abstração.
- Uma feature ou decisão de arquitetura por vez, apresentada para revisão. Nada de implementar etapas inteiras de uma vez.
- Uma arena (chão verde, paredes cinzas). Hoje 5 jogadores como no original; no futuro até 8, com arena maior (16:9).
- Futuro: salas online misturadas com jogadores locais. Bibliotecas de rede ainda não foram escolhidas.
- Não fazer commit sem pedido. Comunicação em pt-BR.

## O que existe

- `src/main.c`: janela + render target de 240×208 (15×13 tiles de 16 px).
- `CMakeLists.txt`: raylib 6.2 via FetchContent, gerador Ninja Multi-Config.
  Build: `cmake --build build --config Debug` → `build/Debug/bomber`.
- `docs/roadmap.md`: checklist das etapas.
- `docs/re/super-bomberman-4.md`: descobertas da engenharia reversa (mapa de RAM, tabelas, timers).
- `tools/re/`: harness de engenharia reversa com MesenCE headless (`/opt/mesence`, no PATH),
  `experiments.py` (experimentos reproduzíveis) e `dis65816.py` (disassembler). Veja `tools/re/README.md`.
- ROM: `~/Downloads/Super Bomberman 4 (Japan).sfc` (nunca versionar).
