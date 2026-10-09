# Emulador e Interpretador RISC-V (RV32I / RV32M)

Este projeto consiste em um emulador e interpretador desenvolvido em Python para o conjunto de instruções **RISC-V (RV32I/M)**, construído para atender integralmente às especificações e requisitos do trabalho prático da disciplina de Arquitetura de Computadores.

O programa lê arquivos com código-fonte Assembly RISC-V (`.s` ou `.txt`), carrega as instruções e variáveis nos seus respectivos segmentos de memória, resolve rótulos/símbolos e executa o ciclo de busca, decodificação e execução sequencial.

---

## Requisitos do Sistema

- **Python 3.8** ou superior instalado.
- **Bibliotecas Externas:** Nenhuma (utiliza exclusivamente os módulos nativos `sys` e `re` da biblioteca padrão do Python).

---

## Estrutura e Regras de Arquitetura

O emulador segue estritamente as regras arquiteturais exigidas:

### 1. Mapeamento de Memória (Little-Endian)
- **Segmento de Código (`.text`):** Inicia exatamente no endereço `0x00000000`.
- **Segmento de Dados (`.data`):** Inicia exatamente no endereço `0x00200000`.
- **Comportamento Padrão:** Qualquer leitura de um endereço de memória não gravado previamente retorna o valor `0`.

### 2. Conjunto de Registradores (32 bits)
- **32 Registradores Gerais:** Mapeados de `x0` a `x31`.
- **Suporte Duplo de Nomes:** Aceita tanto a notação numérica (`x0`..`x31`) quanto os apelidos oficiais da **ABI RISC-V**:
  - `zero` (`x0`)
  - `ra` (`x1`), `sp` (`x2`), `gp` (`x3`), `tp` (`x4`)
  - `t0`-`t2` (`x5`-`x7`), `t3`-`t6` (`x28`-`x31`)
  - `s0`/`fp` (`x8`), `s1` (`x9`), `s2`-`s11` (`x18`-`x27`)
  - `a0`-`a7` (`x10`-`x17`)
- **Registrador `x0` (`zero`):** Possui valor fixo `0` (*hardwired*). Qualquer tentativa de escrita nele é ignorada.

---

## Diretivas do Montador

O emulador interpreta e processa as seguintes diretivas no segmento de dados e código:

| Diretiva | Descrição Oficial | Implementação / Efeito no Emulador |
| :--- | :--- | :--- |
| **`.text`** | Inicia o segmento de código. | Direciona os comandos seguintes para a lista de instruções a partir do endereço `0x00000000`. |
| **`.data`** | Inicia o segmento de dados. | Direciona as alocações seguintes para a memória de dados a partir do endereço `0x00200000`. |
| **`.word v`** | Reserva 4 bytes com o valor `v`. | Grava o inteiro de 32 bits em Little-Endian na memória e avança o ponteiro de dados em 4 bytes. |
| **`.half v`** | Reserva 2 bytes com o valor `v`. | Grava o inteiro de 16 bits em Little-Endian na memória e avança o ponteiro de dados em 2 bytes. |
| **`.byte v`** | Reserva 1 byte com o valor `v`. | Grava o byte de 8 bits na memória e avança o ponteiro de dados em 1 byte. |
| **`.zero n` / `.space n`** | Reserva `n` bytes preenchidos com zero. | Avança o ponteiro de dados em `n` bytes (como a leitura da memória retorna `0` por padrão, o espaço permanece zerado). |
| **`.align n`** | Avança o endereço corrente até o próximo múltiplo de $2^n$. | Ajusta o ponteiro ativo (`ptr_dados` ou `ptr_instrucao`) para o próximo endereço múltiplo de $2^n$. |
| **`.globl r`** | Marca o rótulo `r` como global. Não produz efeito na execução. | Identificado pelo leitor e ignorado com segurança sem interromper a execução. |

---

## Chamadas de Sistema (`ecall`)

O emulador interpreta os códigos carregados no registrador `a7` (ou `x17`) no momento da execução da instrução `ecall`:

| Código em `a7` | Funcionalidade | Efeito |
| :---: | :--- | :--- |
| **`1`** | **Imprimir Inteiro** | Exibe no terminal o valor numérico contido no registrador `a0`. |
| **`10`** | **Encerrar Programa** | Finaliza imediatamente o ciclo de execução do emulador. |

---

## Como Salvar os Arquivos de Teste no Windows

Ao criar arquivos de teste no **Bloco de Notas**, o Windows costuma salvar o arquivo como `caso1.s.txt` por padrão. Para garantir que a extensão fique correta:

1. No Bloco de Notas, vá em **Arquivo** e depois em **Salvar Como...**.
2. No campo **Tipo**, selecione **Todos os Arquivos (*.*)**.
3. No campo **Nome do arquivo**, digite o nome entre aspas duplas: `"caso1.s"`.

*(Se o seu arquivo permaneceu salvo como `teste01.txt`, não há problema: basta passar `teste01.txt` no comando do terminal).*

---

## Como Executar o Emulador

Abra o terminal (CMD ou PowerShell no Windows, Terminal no Linux/macOS) e navegue até a pasta do projeto:

```cmd
cd C:\Caminho\Para\A\Sua\Pasta
No Windows (usando python ou py):python emulador.py caso1.s ou py emulador.py caso1.s
No Linux / macOS:python3 emulador.py caso1.s

---

## Casos de Teste e Exemplos de Execução

Exemplo 1: Alocação de Memória e Encerramento Silencioso (caso1.s)

Este teste valida a alocação de memória, o alinhamento .align e o armazenamento Little-Endian sem realizar impressões no terminal.

Código Assembly (caso1.s):

.data
w1: .word 14
b1: .byte 120
.align 1
h1: .half 22
w2: .zero 4
b2: .zero 1
.align 1
h2: .zero 2

.text
main:
    la t0, w1    # Endereço de w1 -> t0
    la t1, b1    # Endereço de b1 -> t1
    la t2, h1    # Endereço de h1 -> t2
    lw t3, 0(t0) # Memória[t0] -> t3 (14)
    lb t4, 0(t1) # Memória[t1] -> t4 (120)
    lh t5, 0(t2) # Memória[t2] -> t5 (22)
    la t0, w2    # Endereço de w2 -> t0
    sw t3, 0(t0) # t3 -> Memória[w2]
    la t0, b2    # Endereço de b2 -> t0
    sb t4, 0(t0) # t4 -> Memória[b2]
    la t0, h2    # Endereço de h2 -> t0
    sh t5, 0(t0) # t5 -> Memória[h2]
    
    li a7, 10
    ecall

Comando de Execução: python emulador.py caso1.s
Saída no Terminal:(O programa manipula a memória, copia os valores para w2, b2 e h2 e encerra sem exibir texto na tela).

Verificação do Estado Final da Memória:

w2 (no endereço 0x00200008) = 14

b2 (no endereço 0x0020000C) = 120

h2 (no endereço 0x0020000E) = 22

---

## Tratamento de Exceções e Detalhes Técnicos

Comentários e Espaços: Linhas iniciadas com # ou trechos após # na mesma linha são automaticamente ignorados pelo leitor.

Sintaxe de Memória com Offset: Trata instruções do tipo lw x5, 4(x10) decompondo corretamente o deslocamento imediato e o registrador base.

Pseudoinstruções Suportadas:

    li rd, imm -> Expandido para carregar valores imediatos.

    la rd, label -> Carrega o endereço base da memória associado ao rótulo.

    mv rd, rs -> Traduzido para addi rd, rs, 0.

    j label / jr rs -> Saltos incondicionais ajustando o PC.

    beqz / bnez -> Comparações relativas a zero.

    nop -> Sem efeito (addi x0, x0, 0).

Resolução de Rótulos: Aceita rótulos posicionados na mesma linha da instrução (main: addi a0, x0, 1) ou isolados na linha anterior.

Proteção do Registrador Zero: Qualquer operação de escrita que tenha x0 ou zero como destino é ignorada, mantendo o valor do registrador permanentemente em 0.
