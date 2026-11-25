# Roadmap

Ciclo de cada feature: engenharia reversa no emulador → proposta de dados/structs para revisão →
implementação mínima → comparação com a ROM.

## Etapa 0: ferramentas de engenharia reversa

- [x] Harness MesenCE headless (`tools/re/`)
- [x] Mapa de RAM inicial (`docs/re/super-bomberman-4.md`)

## Etapa 1: esqueleto + arena

- [ ] Decisões de base (revisar antes de codar):
  - [ ] loop com timestep fixo de 60 Hz, separado do render
  - [ ] lógica só com inteiros em ponto fixo (sem float)
  - [ ] input como bitmask por jogador por tick
  - [ ] estado do jogo num único struct com arrays fixos, sem ponteiros
  - [ ] separação simulação / render / plataforma (simulação sem raylib)
- [ ] Organização dos arquivos e do build (Linux + Windows)
- [ ] Grid de tiles (chão, bloco fixo, bloco destrutível) com dimensões parametrizáveis
- [ ] Layout da arena clássica 15×13 + blocos destrutíveis com os cantos livres
- [ ] Render da arena (chão verde, paredes cinzas) escalado para a janela

## Etapa 2: movimento de 1 jogador

- [ ] RE: escolha de direção, quinas e colisão (código perto de `C2:3FF0-C2:4035`)
- [ ] Posição em ponto fixo + tabela de velocidades (`C3:2A50`)
- [ ] Colisão com blocos e alinhamento ao corredor
- [ ] Teste "golden": input + posição por tick gravados da ROM vs. nossa simulação

## Etapa 3: bombas e explosões

- [ ] RE: capacidade inicial de bombas, duração exata da chama, reação em cadeia
- [ ] Colocar bomba (fuse de 126 ticks) e colisão com bombas
- [ ] Explosão em cruz com alcance e destruição de blocos
- [ ] Morte do jogador

## Etapa 4: multijogador local e regras do round

- [ ] N jogadores locais (teclado e gamepads) e spawns
- [ ] Vitória, empate, tempo (3:00), placar e número de vitórias

## Etapa 5: itens

- [ ] RE: lista, IDs, quantidade por partida e como são sorteados
- [ ] Itens escondidos nos blocos, coleta, efeitos e item destruído pela chama

## Etapa 6: habilidades, doenças e montarias

- [ ] RE + implementação, uma por vez (chute, soco, caveira, montarias…)

## Etapa 7: regras opcionais

- [ ] Sudden Death, Misobon e Dash Bomber

## Etapa 8: 8 jogadores e arena maior

- [ ] Tamanho da arena em 16:9 e spawns para até 8 jogadores

## Etapa 9: rede

- [ ] Escolher biblioteca (candidata: ENet) e modelo (rollback ou lockstep)
- [ ] Salas e mistura de jogadores locais e online

## Etapa 10: polimento

- [ ] Arte e sons próprios, menus, build e teste no Windows
