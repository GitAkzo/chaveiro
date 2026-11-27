# Chaveiro 3D Rasec v2 — Estilo Mini Luminária LED (Base Oca + Logo em Pé)

Projeto paramétrico de chaveiro para impressão 3D (FDM ou Resina) no estilo **edge-lit / mini luminária**: a logo **Rasec** impressa em filamento translúcido roxo encaixada verticalmente sobre uma base retangular preta arredondada e oca com alojamento para **LED 5mm/3mm + bateria CR2032** e **botão flexível inferior**.

## Arquivos STL Prontos para Fatiar (`stl/`)

1. **`01_logo_translucida_vertical.stl`** *(Logo em Pé com Espigas de Encaixe)*
   - Dimensões: `36.7 × 37.0 × 3.8 mm` (~3.4 g)
   - **Orientação na mesa:** Deitada (`Z = 0`). **Zero suportes.**
   - **Material ideal:** **PETG ou PLA Roxo Translúcido** (ou Cristal/Branco translúcido com LED roxo/UV).
   - **Configuração para máxima luz (efeito acrílico):** 2 paredes, preenchimento **100% retilíneo alinhado** (ou 15% gyroid bem leve para efeito cristalizado), sem camadas opacas.

2. **`02_base_pedestal_led.stl`** *(Base Oca Preta Arredondada + Alça Lateral)*
   - Dimensões: `48.4 × 25.0 × 13.5 mm` (~6.7 g)
   - **Orientação na mesa:** **De cabeça para baixo** (topo com os 2 slots encostado na mesa, `Z = 0`). **Zero suportes!**
   - **Material ideal:** PLA ou PETG **Preto Fosco**.
   - Recursos integrados:
     - Dois slots no topo (folga `0.25 mm`) para travar a logo em pé com firmeza;
     - Colar guia interno para **LED 5 mm ou 3 mm** apontando para cima, direto na base da perna do "R";
     - Berço interno para bateria moeda **CR2032 (Ø 20 mm × 3.2 mm)**;
     - Alça lateral discreta de `5.5 mm` de altura com furo Ø `4.4 mm` para argola de chaveiro.

3. **`03_tampa_inferior_botao.stl`** *(Tampa Inferior com Botão Flexível em U)*
   - Dimensões: `39.5 × 22.5 × 3.3 mm` (~1.7 g)
   - **Orientação na mesa:** Plana (`Z = 0`). **Zero suportes.**
   - **Material ideal:** PLA ou PETG **Preto Fosco** (PETG deixa o botão flexível ainda mais resistente).
   - Inclui botão flexível em "U" com pino atuador interno, duas travinhas de alinhamento e chanfro lateral para abrir com a unha na troca de bateria.

## Montagem do Circuito LED (Sem Solda)

**Materiais:** 1x LED 5mm ou 3mm (Branco Frio, Roxo ou UV ~3V) + 1x Bateria moeda **CR2032**.

1. Com a `02_base_pedestal_led.stl` virada de cabeça para baixo, insira o bulbo do LED no colar guia direito (apontando para o slot da perna do "R").
2. Dobre a perna **curta (`-`)** até o fundo do berço da bateria e coloque a **CR2032** com o polo `-` para baixo (em contato com a perna curta).
3. Dobre a perna **longa (`+`)** passando ~1 mm acima do centro do polo `+` da bateria (sem encostar em repouso).
4. Encaixe a tampa `03_tampa_inferior_botao.stl` no rebaixo inferior — ao apertar o botão em "U" embaixo da base, o pino empurra a perna `+` contra a bateria e a logo acende!
5. Encaixe a logo `01_logo_translucida_vertical.stl` nos dois slots do topo (use uma gotinha de cola cianoacrilato apenas nas espigas se quiser travamento permanente).
