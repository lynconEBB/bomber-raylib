# Engenharia reversa: Super Bomberman 4 (modo Battle)

Objetivo: extrair as **regras e números** (velocidades, timers, layout, itens)
para reimplementá-los do zero em C. Não usamos nenhum asset da ROM
(gráficos, sons, músicas): só os números da mecânica.

- ROM: *Super Bomberman 4 (Japan)*, HiROM + FastROM, 2 MB, md5 `df33e261104efee409de8f294d80ad6e`
- Ferramentas: MesenCE 2.2.1 headless + scripts em `tools/re/` (veja o README de lá)
- Endereços de RAM são da WRAM (`$7E0000-$7FFFFF`); `$0300` = `$7E0300`.
- Status: **confirmado** = observado no emulador / código lido;
  **hipótese** = consistente com os dados, mas falta teste dedicado.

## 1. Tempo

| O quê | Valor | Status |
|---|---|---|
| Taxa da lógica | 1 tick por frame (60 Hz NTSC) | confirmado |
| Lag frames | o SNES pula ticks quando a CPU não dá conta (ex.: explosões) | confirmado |
| Contador de ticks de lógica | `$0166` / `$0170` (não avança em lag frame) | confirmado |
| Contador de frames (NMI) | `$016A` (avança sempre) | confirmado |

Para nós: **1 tick = 1/60 s, sem lag**. Todos os timers abaixo estão em ticks.

## 2. Mapa da arena (Stage 1, "いつもの")

- 15×13 tiles **incluindo** a borda; tile = 16×16 px; área jogável 13×11.
- Mapa lógico: célula de 16 bits em `$2802 + linha*$40 + coluna*2`.
- Byte baixo (flags):

| Valor | Significado | Status |
|---|---|---|
| `$00` | chão | confirmado |
| `$40` | bloco fixo (borda e pilares em coluna/linha pares) | confirmado |
| `$80` | bloco destrutível | confirmado |
| `$C0` | bloco destrutível sendo destruído | confirmado |
| `$41` | item no chão (byte alto = tipo/gráfico; `$09` = +1 bomba) | hipótese |
| `$01` | aparece perto do jogador / da bomba | a investigar |

- Byte alto: gráfico/estado (`$EC` fixo, `$CC` destrutível, `$C9` bomba, `$10` chama).
- Layout no início de uma partida (`python3 -I tools/re/experiments.py map`):

```
###############
#..++++.++++..#
#.#+#.#.#+#+#.#
#+++.+++++++++#
#.#+#+#+#+#+#+#
#.++++...+++.+#
#+#.#+#.#+#+#+#
#+++++...+.+++#
#+#+#+#+#+#+#+#
#.+.++++++++++#
#.#+#.#+#.#.#.#
#..+++++++++..#
###############
```

Os cantos (e o centro, para o 5º jogador) ficam livres. A distribuição dos `+`
parece aleatória por partida (falta confirmar com várias seeds).

## 3. Jogadores

- **Array de structs de `$100` bytes**: P1 em `$0300`, P2 em `$0400`, … (`$0300 + n*$100`).
  A mesma rotina de movimento roda com `X=$0300` e com `X=$0400`. É exatamente
  um "fat struct" em array fixo.

| Offset | Campo | Status |
|---|---|---|
| `+$0B` | estado (1 = parado, 4 = andando) | confirmado |
| `+$0C` / `+$0D` | frame e timer da animação | confirmado |
| `+$11` | X fração (1/256 px) | confirmado |
| `+$12-$13` | X em pixels (posição = 24 bits, 16.8) | confirmado (código `C2:57D4`) |
| `+$15` | Y fração | confirmado |
| `+$16-$17` | Y em pixels | confirmado |
| `+$40` | nível de velocidade (começa em 1) | confirmado |
| `+$60` | direção do movimento: 0 = cima, 1 = cima-dir, 2 = dir, …, 7 = cima-esq, 8 = parado | confirmado |
| `+$64-$65` | vx deste tick (8.8, com sinal) | confirmado |
| `+$66-$67` | vy deste tick | confirmado |
| `+$68` / `+$6A` | velocidade extra somada a vx/vy (esteira? empurrão?) | hipótese |

### Posições e grade

- Posição "alinhada" na grade: **X = 16·col + `$0F`**, **Y = 16·lin + `$1F`**
  (o Y tem 16 px a mais por causa da faixa do HUD).
- Spawn do P1: X = `$20`, Y = `$30` (1 px fora do alinhamento). Ao andar para a
  direita, o jogo usou a direção 1 (cima-direita) por um tick para corrigir Y → `$2F`.

### Velocidade (tabela na ROM `C3:2A50`)

Cálculo (`C2:2FC4`): `ponteiro = $C32A50 + nivel*64 + direcao*4`; lê `dx, dy`
(8.8 com sinal), soma `+$68/+$6A` e guarda em `vx/vy`; depois `C2:57D4` faz
`X += vx; Y += vy`. As diagonais têm a **mesma** velocidade em cada eixo e servem
para alinhar o jogador ao corredor.

| Nível (`+$40`) | px/tick | 8.8 | Uso provável (hipótese) |
|---|---|---|---|
| 0 | 0,875 | 224 | ? |
| 1 | 1,000 | 256 | velocidade inicial (confirmado) |
| 2 | 1,125 | 288 | patins +1 |
| 3 | 1,250 | 320 | patins +2 |
| 4 | 1,375 | 352 | patins +3 |
| 5 | 1,500 | 384 | patins +4 |
| 6 | 2,000 | 512 | doença "rápido"? |
| 7 | 0,500 | 128 | doença "lento"? |

## 4. Bombas e explosões

- **Pool de objetos genéricos**: slots de `$30` bytes a partir de `$0890`
  (bomba em `$0890`; chamas em `$0920`, `$0950`, `$0980`).
  `+$00-$02` = ponteiro da rotina que "é" o objeto (`C1:3BE5` bomba,
  `C1:5051` explosão, `C1:595B` segmento de chama?). Trocar o ponteiro =
  trocar de estado (máquina de estados sem OOP).

| O quê | Valor | Status |
|---|---|---|
| Botão de bomba | **A** | confirmado |
| Posição da bomba | alinhada na grade (`+$12`/`+$16` = `$1F`, `$2F` para o tile (1,1)) | confirmado |
| Fuse | `+$1A` (`$08AA`) começa em **`$7E` = 126 ticks** e decrementa 1 por tick; `+$1B` guarda o valor inicial | confirmado |
| Fogo inicial | **2** (bomba em (1,1) atingiu (3,1) e (1,3)) | confirmado |
| Duração da explosão | ~**25 ticks** (contador `+$0C` sobe de 2 em 2 até `$32`) | hipótese forte |
| Célula com bomba | `$C900` | confirmado |
| Bloco atingido | `$80` → `$C0` por ~35 frames, depois chão ou item | confirmado |
| Item revelado | célula `$0941` = "+1 bomba" | confirmado (visual) |
| Jogador na chama | morre (P1 morreu na própria explosão em (2,1)) | confirmado |

## 5. Opções do modo Battle (vistas nos menus)

- Modos: Battle Royal (バトルロイヤル), Champion (チャンピオン), Maniac (マニアック)
- Single Match / Tag Match
- 5 jogadores: MAN/COM (sem multitap: 1P e 2P MAN, 3P-5P COM)
- Regras: COM LEVEL, BATTLE (vitórias, padrão 3), TIME (padrão 3:00),
  Sudden Death (サドンデス), Misobon (みそボン = eliminados atacam da borda),
  Dash Bomber (ダッシュボンバー); todas OFF por padrão
- 6 personagens e seleção de stage (Stage 1 = arena clássica)

## 6. A investigar (uma feature por vez)

1. Escolha de direção e "quinas": como o input + vizinhança viram `+$60`
   (código perto de `C2:3FF0-C2:4035`, tabelas lidas via `[$54],Y`/`[$58],Y`).
2. Colisão: com blocos, com bombas (inclusive sair de cima da própria bomba).
3. Capacidade inicial de bombas (provavelmente 1) e máximos de bomba/fogo/velocidade.
4. Itens: lista, IDs, quantidade por partida, se são pré-sorteados ou decididos na destruição.
5. Botões B/X/Y/L/R no Battle (chute, soco, montaria?).
6. Montarias, doenças (caveira), Sudden Death, Misobon, Dash Bomber.
7. Duração exata da chama, reação em cadeia, timings de morte e fim de round.
