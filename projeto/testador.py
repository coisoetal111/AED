#!/usr/bin/env python3
"""
Testador do projeto healkristin.

Uso:
    python3 testador.py              -> mostra um menu para escolher o conjunto de testes
    python3 testador.py baby         -> corre só os BabyOnes
    python3 testador.py child        -> corre só os ChildOnes
    python3 testador.py preteen      -> corre só os PreTeenOnes
    python3 testador.py all          -> corre os três, um a seguir ao outro
    python3 testador.py child -v     -> idem, mas mostra TODAS as linhas diferentes
    python3 testador.py all --strict -> comparação byte a byte (espaços no fim, linhas vazias,
                                        \\n final...), como um `diff` sem opções
    python3 testador.py --no-make    -> não recompila (usa o executável que já existe)

Cada conjunto pode estar numa pasta (BabyOnes/, ChildOnes/, PreTeenOnes/) OU
num .zip na mesma pasta do script. Se só existir o .zip, é extraído sozinho.
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

# ================= CONFIGURAÇÕES =================
EXECUTAVEL = "./healkristin"
EXTENSAO_PROF = ".ProfSol"   # extensão da solução do professor
TIMEOUT = 10                 # segundos máximos por teste

# nome no menu -> (pasta onde ficam os testes, possíveis nomes do .zip)
CONJUNTOS = {
    "baby":    ("BabyOnes",    ["BabyOnes.zip", "BabyOnes_1_.zip", "BabyOnes (1).zip"]),
    "child":   ("ChildOnes",   ["ChildOnes.zip"]),
    "preteen": ("PreTeenOnes", ["PreTeenOnes.zip"]),
}
# =================================================

DIR_SCRIPT = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR_SCRIPT)  # assim corre bem de qualquer sítio


# ---------------------------------------------------------------- compilação
def compilar_codigo():
    print("⚙️  A compilar com make...")
    subprocess.run(["make", "clean"], capture_output=True)
    resultado = subprocess.run(["make"], capture_output=True, text=True)
    if resultado.returncode != 0:
        print("❌ Erro na compilação! O make falhou:")
        print(resultado.stdout)
        print(resultado.stderr)
        sys.exit(1)
    if resultado.stderr.strip():  # warnings (-Wall)
        print("⚠️  Avisos do compilador:")
        print(resultado.stderr)
    print("✅ Compilação concluída com sucesso!\n")


# ------------------------------------------------------- preparar os conjuntos
def preparar_pasta(chave):
    """Devolve o caminho da pasta de testes, extraindo o .zip se for preciso."""
    pasta, zips = CONJUNTOS[chave]

    if glob.glob(os.path.join(pasta, "*.quests")):
        return pasta

    for nome_zip in zips:
        if os.path.exists(nome_zip):
            print(f"📦 A extrair {nome_zip} para '{pasta}/'...")
            with tempfile.TemporaryDirectory() as tmp:
                with zipfile.ZipFile(nome_zip) as z:
                    z.extractall(tmp)
                # o zip pode ter os ficheiros na raiz ou dentro de uma subpasta
                origem = tmp
                for raiz, _, ficheiros in os.walk(tmp):
                    if any(f.endswith(".quests") for f in ficheiros):
                        origem = raiz
                        break
                os.makedirs(pasta, exist_ok=True)
                for f in os.listdir(origem):
                    caminho = os.path.join(origem, f)
                    if os.path.isfile(caminho):
                        shutil.copy2(caminho, os.path.join(pasta, f))
            return pasta

    return None


# ------------------------------------------------------------------ comparação
def ler_linhas(caminho):
    with open(caminho, "r", errors="replace") as f:
        return [l.strip() for l in f if l.strip()]  # ignora vazias e espaços


def comparar_ficheiros(ficheiro_aluno, ficheiro_prof, verbose=False):
    try:
        aluno = ler_linhas(ficheiro_aluno)
        prof = ler_linhas(ficheiro_prof)
    except Exception as e:
        return False, f"Erro ao ler os ficheiros: {e}"

    if aluno == prof:
        return True, None

    difs = [(i + 1, a, p) for i, (a, p) in enumerate(zip(aluno, prof)) if a != p]
    msg = []
    limite = len(difs) if verbose else 1
    for n, a, p in difs[:limite]:
        msg.append(f"Diferença na linha {n} (ignorando linhas vazias):\n"
                   f"      Teu output:  {a}\n"
                   f"      Prof output: {p}")
    if len(difs) > limite:
        msg.append(f"... e mais {len(difs) - limite} linha(s) diferentes (usa -v para ver todas)")
    if len(aluno) != len(prof):
        msg.append(f"Número de linhas diferente (tu: {len(aluno)}, prof: {len(prof)})")
    return False, "\n   -> ".join(msg)


def comparar_estrito(ficheiro_aluno, ficheiro_prof, verbose=False):
    """Compara byte a byte. Mostra as diferenças com repr() para se verem os espaços."""
    try:
        with open(ficheiro_aluno, "r", errors="replace", newline="") as f:
            aluno = f.read()
        with open(ficheiro_prof, "r", errors="replace", newline="") as f:
            prof = f.read()
    except Exception as e:
        return False, f"Erro ao ler os ficheiros: {e}"

    if aluno == prof:
        return True, None

    la = aluno.split("\n")
    lp = prof.split("\n")
    difs = []
    for i in range(max(len(la), len(lp))):
        a = la[i] if i < len(la) else None
        p = lp[i] if i < len(lp) else None
        if a != p:
            difs.append((i + 1, a, p))

    def fmt(x):
        return "<não existe>" if x is None else repr(x)

    msg = []
    limite = len(difs) if verbose else 1
    for n, a, p in difs[:limite]:
        msg.append(f"[estrito] diferença na linha {n}:\n"
                   f"      Teu output:  {fmt(a)}\n"
                   f"      Prof output: {fmt(p)}")
    if len(difs) > limite:
        msg.append(f"... e mais {len(difs) - limite} linha(s) diferentes (usa -v para ver todas)")
    return False, "\n   -> ".join(msg)


# ----------------------------------------------------------------------- testes
def correr_conjunto(chave, verbose=False, estrito=False):
    pasta = preparar_pasta(chave)
    nome_conjunto = CONJUNTOS[chave][0]
    print("=" * 40)
    print(f"🧪 {nome_conjunto}" + ("  [modo ESTRITO]" if estrito else ""))
    print("=" * 40)

    if pasta is None:
        print(f"⚠️  Não encontrei a pasta '{nome_conjunto}' nem o respetivo .zip.\n")
        return 0, 0

    quests = sorted(glob.glob(os.path.join(pasta, "*.quests")))
    if not quests:
        print(f"⚠️  Não foram encontrados ficheiros .quests em '{pasta}'.\n")
        return 0, 0

    passados = 0
    total = 0

    for quest_file in quests:
        base = quest_file[: -len(".quests")]
        map_file = base + ".map"
        pos_file = base + ".position"
        prof_file = base + EXTENSAO_PROF
        results_file = base + ".results"
        nome = os.path.basename(base)

        if not (os.path.exists(map_file) and os.path.exists(pos_file) and os.path.exists(prof_file)):
            print(f"⏭️  [{nome}] Ignorado: faltam ficheiros base ou a solução do professor.")
            continue

        total += 1

        # garante que não estamos a comparar um .results antigo
        if os.path.exists(results_file):
            os.remove(results_file)

        try:
            proc = subprocess.run(
                [EXECUTAVEL, map_file, pos_file, quest_file],
                capture_output=True, text=True, timeout=TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            print(f"⏱️  [{nome}] FALHOU: excedeu {TIMEOUT}s (ciclo infinito?)")
            continue

        if proc.returncode != 0:
            print(f"💥 [{nome}] FALHOU: o programa terminou com código {proc.returncode}"
                  + (" (crash/segfault)" if proc.returncode < 0 else ""))
            if proc.stderr.strip():
                print(f"   -> {proc.stderr.strip()}")
            continue

        if not os.path.exists(results_file):
            print(f"❌ [{nome}] FALHOU: o ficheiro .results não foi gerado.")
            continue

        if estrito:
            sucesso, erro = comparar_estrito(results_file, prof_file, verbose)
        else:
            sucesso, erro = comparar_ficheiros(results_file, prof_file, verbose)
        if sucesso:
            print(f"✅ [{nome}] PASSOU")
            passados += 1
        else:
            print(f"❌ [{nome}] FALHOU")
            print(f"   -> {erro}")

    print(f"\n📊 {nome_conjunto}: {passados}/{total} testes passados.\n")
    return passados, total


# ------------------------------------------------------------------------ menu
def escolher_conjuntos():
    chaves = list(CONJUNTOS)
    print("Que testes queres correr?")
    for i, c in enumerate(chaves, 1):
        print(f"  {i}) {CONJUNTOS[c][0]}")
    print(f"  {len(chaves) + 1}) Todos")
    print("  0) Sair")
    while True:
        escolha = input("> ").strip().lower()
        if escolha in ("0", "q", "sair"):
            sys.exit(0)
        if escolha in (str(len(chaves) + 1), "all", "todos", "t"):
            return chaves
        if escolha.isdigit() and 1 <= int(escolha) <= len(chaves):
            return [chaves[int(escolha) - 1]]
        if escolha in CONJUNTOS:
            return [escolha]
        print("Opção inválida, tenta outra vez.")


def main():
    args = sys.argv[1:]
    verbose = "-v" in args or "--verbose" in args
    sem_make = "--no-make" in args
    estrito = "--strict" in args or "-s" in args
    args = [a for a in args if not a.startswith("-")]

    if args:
        escolhidos = []
        for a in args:
            a = a.lower()
            if a in ("all", "todos"):
                escolhidos = list(CONJUNTOS)
                break
            if a not in CONJUNTOS:
                print(f"Conjunto desconhecido: '{a}'. Opções: {', '.join(CONJUNTOS)}, all")
                sys.exit(1)
            escolhidos.append(a)
    else:
        escolhidos = escolher_conjuntos()
    print()

    if sem_make and os.path.exists(EXECUTAVEL):
        print("⏩ A saltar a compilação (--no-make).\n")
    else:
        compilar_codigo()

    total_passados = total_testes = 0
    for c in escolhidos:
        p, t = correr_conjunto(c, verbose, estrito)
        total_passados += p
        total_testes += t

    print("=" * 40)
    print(f"🏁 RESULTADO FINAL: {total_passados}/{total_testes} testes passados"
          + (" (modo estrito)." if estrito else "."))
    if total_testes and total_passados == total_testes:
        print("🏆 PARABÉNS! O TEU ALGORITMO ESTÁ PERFEITO!")
    print("=" * 40)
    sys.exit(0 if total_passados == total_testes else 1)


if __name__ == "__main__":
    main()
