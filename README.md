# Chaveiro 3D Rasec — Versão LED (Base Oca) + Versão Maciça

Projeto paramétrico de chaveiro para impressão 3D (FDM ou Resina) baseado na logo **Rasec**, adaptado com **base oca para LED + bateria moeda CR2032** e **botão de pressão flexível integrado** (acende ao apertar a traseira, sem precisar de chave liga/desliga externa).

## Arquivos STL Prontos para Fatiar (`stl/`)

1. **`01_frente_logo_difusor.stl`** *(Tampa Frontal + Difusor + Logo em Relevo)*
   - Dimensões: Ø 45.1 mm × 2.2 mm (base difusora de 0.8 mm + logo em alto-relevo de 1.4 mm).
   - **Orientação na mesa:** Deitada de costas (`Z = 0` na mesa). **Zero suportes.**
   - **Dica de cor/luz:** Imprima a base (0.0 mm a 0.8 mm) em **PLA Branco ou Translúcido** (deixa a luz do LED atravessar suavemente) e faça troca de filamento na camada `0.8 mm` para **PLA Roxo/Lilás** (ou imprima inteira em Branco/Translúcido usando um LED roxo/UV!).

2. **`02_base_oca_led.stl`** *(Base Oca com Alça + Berço CR2032 + Botão Flexível)*
   - Dimensões: 48.0 mm × 56.9 mm × 8.6 mm.
   - **Orientação na mesa:** Traseira apoiada na mesa (`Z = 0`). **Zero suportes.**
   - Inclui:
     - Alça reforçada com furo Ø 4.6 mm para argola de chaveiro padrão;
     - Berço interno para bateria moeda **CR2032** (Ø 20 mm × 3.2 mm);
     - Guias superiores para acomodar um **LED 3 mm ou 5 mm**;
     - Recorte em "U" traseiro formando um **botão flexível (compliant mechanism)** com pino atuador interno;
     - Rebaixo frontal com folga de `0.25 mm` para encaixe rente da tampa difusora.

3. **`03_chaveiro_macico_simples.stl`** *(Bônus — Peça Única Sem LED)*
   - Dimensões: 48.0 mm × 56.9 mm × 3.6 mm.
   - Ideal para impressão rápida (~15 min) com troca de cor na altura `2.2 mm` (base preta/grafite + logo roxa).

## Configurações Recomendadas no Fatiador (Bambu Studio / OrcaSlicer / PrusaSlicer / Cura)

- **Bico:** 0.4 mm
- **Altura de camada:** 0.20 mm (ou 0.16 mm para detalhes ainda mais nítidos na logo)
- **Paredes (Perímetros):** 3
- **Preenchimento (Infill):** 20% Gyroid (na tampa difusora use 100% ou 4 camadas sólidas para difusão uniforme sem marcas de preenchimento)
- **Suportes:** **Desligados (Não precisa!)**
- **Material:** PLA ou PETG (PETG deixa o botão flexível ainda mais durável)

## Montagem do Circuito LED (Sem Solda!)

**Materiais:**
- 1x LED 3 mm ou 5 mm (cor roxa, branca ou magenta — tensão direta ~3V)
- 1x Bateria moeda **CR2032 (3V)**

**Passo a passo:**
1. Encaixe a cabeça do LED entre os dois clipes superiores da cavidade (`02_base_oca_led.stl`), apontando para o centro.
2. Dobre a perna **negativa (menor, cátodo `-`)** para ficar encostada no fundo do berço da bateria.
3. Coloque a bateria **CR2032** no berço com o lado **negativo (`-`, texturizado)** voltado para baixo (em contato com a perna curta do LED) e o lado **positivo (`+`, liso)** voltado para cima.
4. Posicione a perna **positiva (maior, ânodo `+`)** passando ~1 mm acima da face `+` da bateria (sem encostar em repouso).
5. Teste apertando o botão flexível na traseira do chaveiro — o LED deve acender na hora e apagar ao soltar!
6. Encaixe a tampa `01_frente_logo_difusor.stl` no rebaixo frontal (encaixe por pressão; se quiser fechamento permanente, aplique 2 gotinhas mínimas de cola cianoacrilato apenas na borda, ou deixe por encaixe para trocar a bateria no futuro).

## Customização Paramétrica

Você pode alterar diâmetro, folga de encaixe, espessura do difusor ou altura do relevo editando `KeychainSpec` em `keychain_builder.py` e rodando:

```powershell
.\.venv\Scripts\python.exe generate_keychain.py
```
