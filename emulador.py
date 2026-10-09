# MARCOS PABLO DA SILVA COSTA
# 22552617

import sys

# Tópico 3.4: Mapeamento para registradores "x0" a "x31"
MAPA_REG_ABI = {
    "zero": "x0", "ra": "x1", "sp": "x2", "gp": "x3", "tp": "x4",
    "t0": "x5", "t1": "x6", "t2": "x7",
    "s0": "x8", "fp": "x8", "s1": "x9",
    "a0": "x10", "a1": "x11", "a2": "x12", "a3": "x13",
    "a4": "x14", "a5": "x15", "a6": "x16", "a7": "x17",
    "s2": "x18", "s3": "x19", "s4": "x20", "s5": "x21",
    "s6": "x22", "s7": "x23", "s8": "x24", "s9": "x25",
    "s10": "x26", "s11": "x27",
    "t3": "x28", "t4": "x29", "t5": "x30", "t6": "x31"
}

def padronizar_registrador(nome):
    s = str(nome).strip().lower()
    if s in MAPA_REG_ABI:
        return MAPA_REG_ABI[s]
    if s.startswith("x") and s[1:].isdigit():
        idx = int(s[1:])
        if 0 <= idx <= 31:
            return f"x{idx}"
    raise ValueError(f"Registrador inválido: {nome}")

def para_inteiro32(val):
    val = val & 0xFFFFFFFF
    if val & 0x80000000:
        return val - 0x100000000
    return val

def converter_inteiro(s):
    return int(str(s).strip(), 0)

def limpa_linha(linha):
    pos = linha.find("#")
    if pos != -1:
        linha = linha[:pos]
    return linha.strip()

def extrair_tokens(linha):
    linha = limpa_linha(linha)
    if not linha:
        return None, []
    
    parts = linha.split(None, 1)
    mnemonico = parts[0]
    ops_raw = parts[1] if len(parts) > 1 else ""
    
    if not ops_raw.strip():
        return mnemonico, []
    
    ops = [op.strip() for op in ops_raw.split(",") if op.strip()]
    return mnemonico, ops

def extrair_memoria_deslocamento_reg(op_str):
    s = op_str.strip()
    if "(" in s and s.endswith(")"):
        idx = s.find("(")
        off_str = s[:idx].strip()
        reg_str = s[idx+1:-1].strip()
        return off_str if off_str else "0", reg_str
    return "0", s

class EmuladorRISCV:
    def __init__(self):
        # Tópico 4.1: Registradores (dict) inicializados em 0
        self.registradores = {f"x{i}": 0 for i in range(32)}
        # Tópico 4.2: Memória byte a byte (dict)
        self.memoria = {}
        # Tópico 4.3: PC (Program Counter)
        self.pc = 0x00000000
        # Tópico 4.4: Dicionário de Rótulos e Dicionário de Instruções
        self.rotulos = {}
        self.instrucoes = {}

    def obter_registrador(self, reg_name):
        reg = padronizar_registrador(reg_name)
        return self.registradores[reg]

    def definir_registrador(self, reg_name, val):
        reg = padronizar_registrador(reg_name)
        # Tópico 4.1: x0 é fixo em 0; escritas são descartadas
        if reg != "x0":
            self.registradores[reg] = para_inteiro32(val)

    def ler_bytes_memoria(self, addr, size):
        val = 0
        for i in range(size):
            # Tópico 4.2: Endereço nunca escrito retorna 0 por padrão
            b = self.memoria.get(addr + i, 0)
            val |= (b & 0xFF) << (8 * i)
        return val

    def escrever_bytes_memoria(self, addr, val, size):
        # Tópico 4.2: Gravação em Little-Endian
        val_unsigned = val & ((1 << (8 * size)) - 1)
        for i in range(size):
            b = (val_unsigned >> (8 * i)) & 0xFF
            self.memoria[addr + i] = b

    def resolver_imediato_ou_rotulo(self, token):
        token = token.strip()
        if token in self.rotulos:
            return self.rotulos[token]
        return converter_inteiro(token)

    def carregar_programa(self, caminho_arquivo):
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        segmento = ".text"
        pc_curr = 0x00000000
        dc_curr = 0x00200000

        for l_raw in linhas:
            linha = limpa_linha(l_raw)
            if not linha:
                continue

            # Tópico 5: Suporte a múltiplos rótulos ou rótulo + instrução na mesma linha
            while ":" in linha:
                partes = linha.split(":", 1)
                lbl = partes[0].strip()
                linha = partes[1].strip()
                if segmento == ".text":
                    self.rotulos[lbl] = pc_curr
                else:
                    self.rotulos[lbl] = dc_curr

            if not linha:
                continue

            mnem, ops = extrair_tokens(linha)
            if not mnem:
                continue

            if mnem in [".text", ".data"]:
                segmento = mnem
                continue

            if mnem == ".globl":
                continue

            # Tópico 3.3: Diretiva .align n
            if mnem == ".align":
                n = converter_inteiro(ops[0])
                align_bytes = 1 << n
                if segmento == ".text":
                    if pc_curr % align_bytes != 0:
                        pc_curr = ((pc_curr // align_bytes) + 1) * align_bytes
                else:
                    if dc_curr % align_bytes != 0:
                        dc_curr = ((dc_curr // align_bytes) + 1) * align_bytes
                continue

            if segmento == ".data":
                if mnem == ".word":
                    for op in ops:
                        val = self.resolver_imediato_ou_rotulo(op)
                        self.escrever_bytes_memoria(dc_curr, val, 4)
                        dc_curr += 4
                elif mnem == ".half":
                    for op in ops:
                        val = self.resolver_imediato_ou_rotulo(op)
                        self.escrever_bytes_memoria(dc_curr, val, 2)
                        dc_curr += 2
                elif mnem == ".byte":
                    for op in ops:
                        val = self.resolver_imediato_ou_rotulo(op)
                        self.escrever_bytes_memoria(dc_curr, val, 1)
                        dc_curr += 1
                elif mnem in [".zero", ".space"]:
                    count = converter_inteiro(ops[0])
                    # Tópico 4.2: Reserva n bytes sem alocar chaves no dicionário
                    dc_curr += count
            else:
                self.instrucoes[pc_curr] = [mnem] + ops
                pc_curr += 4

    def executar(self):
        # Tópicos 4.3 e 5: Início obrigatoriamente no rótulo 'main'
        if "main" in self.rotulos:
            self.pc = self.rotulos["main"]
        else:
            self.pc = 0x00000000

        while True:
            if self.pc not in self.instrucoes:
                break

            campos = self.instrucoes[self.pc]
            mnem = campos[0]
            ops = campos[1:]
            
            pc_alterado = False

            # --- TÓPICO 3.2 PSEUDOINSTRUÇÕES ---
            if mnem == "li":
                rd = ops[0]
                imm = self.resolver_imediato_ou_rotulo(ops[1])
                self.definir_registrador(rd, imm)
            elif mnem == "la":
                rd = ops[0]
                lbl = ops[1]
                self.definir_registrador(rd, self.rotulos[lbl])
            elif mnem == "mv":
                rd = ops[0]
                rs = ops[1]
                self.definir_registrador(rd, self.obter_registrador(rs))
            elif mnem == "j":
                lbl = ops[0]
                self.pc = self.rotulos[lbl]
                pc_alterado = True
            elif mnem == "jr":
                rs = ops[0]
                self.pc = self.obter_registrador(rs)
                pc_alterado = True

            # --- TÓPICO 3.1 INSTRUÇÕES TIPO R ---
            elif mnem == "add":
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) + self.obter_registrador(ops[2]))
            elif mnem == "sub":
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) - self.obter_registrador(ops[2]))
            elif mnem == "sll":
                shamt = self.obter_registrador(ops[2]) & 0x1F
                self.definir_registrador(ops[0], (self.obter_registrador(ops[1]) & 0xFFFFFFFF) << shamt)
            elif mnem == "slt":
                self.definir_registrador(ops[0], 1 if self.obter_registrador(ops[1]) < self.obter_registrador(ops[2]) else 0)
            elif mnem == "sltu":
                u1 = self.obter_registrador(ops[1]) & 0xFFFFFFFF
                u2 = self.obter_registrador(ops[2]) & 0xFFFFFFFF
                self.definir_registrador(ops[0], 1 if u1 < u2 else 0)
            elif mnem == "xor":
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) ^ self.obter_registrador(ops[2]))
            elif mnem == "srl":
                shamt = self.obter_registrador(ops[2]) & 0x1F
                val = (self.obter_registrador(ops[1]) & 0xFFFFFFFF) >> shamt
                self.definir_registrador(ops[0], val)
            elif mnem == "sra":
                shamt = self.obter_registrador(ops[2]) & 0x1F
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) >> shamt)
            elif mnem == "or":
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) | self.obter_registrador(ops[2]))
            elif mnem == "and":
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) & self.obter_registrador(ops[2]))
            elif mnem == "mul":
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) * self.obter_registrador(ops[2]))
            elif mnem == "div":
                v1 = self.obter_registrador(ops[1])
                v2 = self.obter_registrador(ops[2])
                if v2 == 0:
                    self.definir_registrador(ops[0], -1)
                else:
                    self.definir_registrador(ops[0], int(v1 / v2))
            elif mnem == "rem":
                v1 = self.obter_registrador(ops[1])
                v2 = self.obter_registrador(ops[2])
                if v2 == 0:
                    self.definir_registrador(ops[0], v1)
                else:
                    res = abs(v1) % abs(v2)
                    self.definir_registrador(ops[0], -res if v1 < 0 else res)

            # --- TÓPICO 3.1 INSTRUÇÕES TIPO I ARITMÉTICO ---
            elif mnem == "addi":
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) + self.resolver_imediato_ou_rotulo(ops[2]))
            elif mnem == "slti":
                self.definir_registrador(ops[0], 1 if self.obter_registrador(ops[1]) < self.resolver_imediato_ou_rotulo(ops[2]) else 0)
            elif mnem == "sltiu":
                u1 = self.obter_registrador(ops[1]) & 0xFFFFFFFF
                u2 = self.resolver_imediato_ou_rotulo(ops[2]) & 0xFFFFFFFF
                self.definir_registrador(ops[0], 1 if u1 < u2 else 0)
            elif mnem == "ori":
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) | (self.resolver_imediato_ou_rotulo(ops[2]) & 0xFFFFFFFF))
            elif mnem == "andi":
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) & self.resolver_imediato_ou_rotulo(ops[2]))
            elif mnem == "slli":
                shamt = self.resolver_imediato_ou_rotulo(ops[2]) & 0x1F
                self.definir_registrador(ops[0], (self.obter_registrador(ops[1]) & 0xFFFFFFFF) << shamt)
            elif mnem == "srli":
                shamt = self.resolver_imediato_ou_rotulo(ops[2]) & 0x1F
                val = (self.obter_registrador(ops[1]) & 0xFFFFFFFF) >> shamt
                self.definir_registrador(ops[0], val)
            elif mnem == "srai":
                shamt = self.resolver_imediato_ou_rotulo(ops[2]) & 0x1F
                self.definir_registrador(ops[0], self.obter_registrador(ops[1]) >> shamt)

            # --- TÓPICO 3.1 INSTRUÇÕES TIPO I DE CARGA ---
            elif mnem in ["lb", "lh", "lw", "lbu", "lhu"]:
                rd = ops[0]
                off_str, rs1_str = extrair_memoria_deslocamento_reg(ops[1])
                off = self.resolver_imediato_ou_rotulo(off_str)
                addr = self.obter_registrador(rs1_str) + off

                if mnem == "lb":
                    val = self.ler_bytes_memoria(addr, 1)
                    if val & 0x80:
                        val -= 0x100
                    self.definir_registrador(rd, val)
                elif mnem == "lh":
                    val = self.ler_bytes_memoria(addr, 2)
                    if val & 0x8000:
                        val -= 0x10000
                    self.definir_registrador(rd, val)
                elif mnem == "lw":
                    val = self.ler_bytes_memoria(addr, 4)
                    if val & 0x80000000:
                        val -= 0x100000000
                    self.definir_registrador(rd, val)
                elif mnem == "lbu":
                    self.definir_registrador(rd, self.ler_bytes_memoria(addr, 1) & 0xFF)
                elif mnem == "lhu":
                    self.definir_registrador(rd, self.ler_bytes_memoria(addr, 2) & 0xFFFF)

            # --- TÓPICO 3.1 INSTRUÇÕES TIPO S (ARMAZENAMENTO) ---
            elif mnem in ["sb", "sh", "sw"]:
                rs2 = ops[0]
                off_str, rs1_str = extrair_memoria_deslocamento_reg(ops[1])
                off = self.resolver_imediato_ou_rotulo(off_str)
                addr = self.obter_registrador(rs1_str) + off
                val = self.obter_registrador(rs2)

                if mnem == "sb":
                    self.escrever_bytes_memoria(addr, val, 1)
                elif mnem == "sh":
                    self.escrever_bytes_memoria(addr, val, 2)
                elif mnem == "sw":
                    self.escrever_bytes_memoria(addr, val, 4)

            # --- TÓPICO 3.1 INSTRUÇÕES TIPO B (DESVIO CONDICIONAL) ---
            elif mnem in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]:
                v1 = self.obter_registrador(ops[0])
                v2 = self.obter_registrador(ops[1])
                target = self.resolver_imediato_ou_rotulo(ops[2])
                
                cond = False
                if mnem == "beq":
                    cond = (v1 == v2)
                elif mnem == "bne":
                    cond = (v1 != v2)
                elif mnem == "blt":
                    cond = (v1 < v2)
                elif mnem == "bge":
                    cond = (v1 >= v2)
                elif mnem == "bltu":
                    cond = ((v1 & 0xFFFFFFFF) < (v2 & 0xFFFFFFFF))
                elif mnem == "bgeu":
                    cond = ((v1 & 0xFFFFFFFF) >= (v2 & 0xFFFFFFFF))

                if cond:
                    self.pc = target
                    pc_alterado = True

            # --- TÓPICO 3.1 SISTEMA (ECALL) ---
            elif mnem == "ecall":
                a7_val = self.obter_registrador("a7")
                if a7_val == 1:
                    print(self.obter_registrador("a0"))
                elif a7_val == 10:
                    break

            if not pc_alterado:
                self.pc += 4

# Tópico 2: Execução via linha de comando sem input()
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        emulador = EmuladorRISCV()
        emulador.carregar_programa(sys.argv[1])
        emulador.executar()
