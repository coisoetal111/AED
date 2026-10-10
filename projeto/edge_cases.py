#!/usr/bin/env python3
"""Casos-limite dirigidos para o HealkrISTin (fase 1).
Uso: python3 edge_cases.py ./healkristin [./hk_asan]
Cada caso cria os ficheiros num directório temporário, corre o binário,
e compara com a resposta esperada (referência independente em Python)."""
import os, sys, subprocess, tempfile, shutil, time, resource, signal, random

BIN = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "./healkristin")
if not os.path.exists(BIN):
    sys.exit(f"Binário não encontrado: {BIN}\nCompila primeiro (make) e corre na pasta do projecto:\n  python3 edge_cases.py [./healkristin] [./binario_asan]")
ASAN = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else None
if ASAN is None:  # tenta compilar uma versão com AddressSanitizer (só para diagnóstico)
    import glob
    srcs = glob.glob(os.path.join(os.path.dirname(BIN), "*.c"))
    if srcs and shutil.which("gcc"):
        out = os.path.join(tempfile.gettempdir(), "hk_asan_bin")
        r = subprocess.run(["gcc", "-g", "-fsanitize=address,undefined", "-std=c99", "-o", out] + srcs + ["-lm"],
                           capture_output=True)
        if r.returncode == 0:
            ASAN = out
TL = 10.0
PERF_KILL = 15.0   # nos testes de desempenho, corta aos 15 s (já é falha acima de 10 s)

# ---------------------------------------------------------------- referência
def reference(cities, edges, pos, quests):
    par = list(range(cities + 1))
    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for a, b in edges:
        if 1 <= a <= cities and 1 <= b <= cities:
            par[f(a)] = f(b)
    groups = {}
    for c in range(1, cities + 1):
        groups.setdefault(f(c), []).append(c)
    cl = sorted(groups.values(), key=lambda g: g[0])
    root = {c: f(c) for c in range(1, cities + 1)}
    out = []
    for q in quests:
        t = q.split()
        if t[0] == "Task1":
            out.append(f"Task1 {len(cl)}\n")
        elif t[0] == "Task2":
            out.append(f"Task2 {len(cl)}\n" + "".join("Cluster: " + " ".join(map(str, g)) + "\n" for g in cl))
        elif t[0] in ("Task3", "Task4"):
            c = int(t[1])
            best, bc = None, -2
            if 1 <= c <= cities:
                mine = [x for x in range(1, cities + 1) if root[x] == root[c]] if t[0] == "Task4" else [c]
                for o in range(1, cities + 1):
                    if root[o] == root[c]:
                        continue
                    d = min((pos[o][0]-pos[m][0])**2 + (pos[o][1]-pos[m][1])**2 for m in mine)
                    if best is None or d < best:
                        best, bc = d, o
            out.append(f"{t[0]} {c} {bc}\n")
    return "\n".join(out) + ("\n" if out else "")

# ---------------------------------------------------------------- execução
def run(binary, cwd, args, timeout=TL * 3):
    t0 = time.time()
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        p = subprocess.run([binary] + args, cwd=cwd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, None, None, time.time() - t0
    return p.returncode, p.stdout, p.stderr, time.time() - t0

def mk_pos(n, xmax=100, ymax=100, seed=1):
    rnd = random.Random(seed)
    return {i: (rnd.randint(1, xmax), rnd.randint(1, ymax)) for i in range(1, n + 1)}

def pos_text(pos, xmax=100, ymax=100):
    return f"{xmax} {ymax}\n" + "".join(f"{i} {x} {y}\n" for i, (x, y) in pos.items())

def map_text(n, edges, L=None):
    return f"{n} {len(edges) if L is None else L}\n" + "".join(f"{a} {b}\n" for a, b in edges)

results = []   # (grupo, nome, veredicto, detalhe)

def check_valid(group, name, quests_txt, map_txt, pos_txt, expected, qname="t.quests",
                mname="t.map", pname="t.position", subdir=None, args=None):
    d = tempfile.mkdtemp(prefix="hk_")
    try:
        base = os.path.join(d, subdir) if subdir else d
        os.makedirs(base, exist_ok=True)
        open(os.path.join(base, qname), "w", newline="").write(quests_txt)
        open(os.path.join(base, mname), "w", newline="").write(map_txt)
        open(os.path.join(base, pname), "w", newline="").write(pos_txt)
        a = args if args else [qname, mname, pname]
        rc, so, se, el = run(BIN, base, a)
        resname = os.path.join(base, qname[:-len(".quests")] + ".results")
        if rc is None:
            results.append((group, name, "TIMEOUT", f">{TL*3}s")); return
        if rc != 0:
            sig = f"sinal {signal.Signals(-rc).name}" if rc < 0 else f"exit {rc}"
            det = sig
            if ASAN:
                _, _, se2, _ = run(ASAN, base, a)
                line = [l for l in (se2 or b"").decode(errors="replace").splitlines() if "ERROR" in l or "runtime error" in l]
                det += " | ASan: " + (line[0][:140] if line else "-")
            results.append((group, name, "CRASH/EXIT≠0", det)); return
        if so or se:
            results.append((group, name, "OUTPUT EXTRA", f"stdout/stderr não vazio"));
            return
        got = open(resname, newline="").read() if os.path.exists(resname) else None
        if got == "" and expected: got = "(ficheiro vazio)"
        if expected is None:
            if got is None:
                results.append((group, name, "OK", "sem .results (correcto)"))
            else:
                results.append((group, name, "FALHA", f".results criado ({len(got)} bytes) mas devia não haver output"))
        else:
            if got == expected:
                results.append((group, name, "OK", f"{el:.2f}s"))
            else:
                results.append((group, name, "FALHA", "esperado %r | obtido %r" % (expected[:120], (got or 'NONE')[:120])))
    finally:
        shutil.rmtree(d, ignore_errors=True)

def simple(group, name, n, edges, quests, pos=None, **kw):
    pos = pos or mk_pos(n)
    exp = reference(n, edges, pos, quests)
    check_valid(group, name, "\n".join(quests) + "\n", map_text(n, edges), pos_text(pos), exp, **kw)

# ================================================================== CASOS
G = "A. dados válidos / limites"
simple(G, "1 cidade, sem ligações, Task1-4", 1, [], ["Task1", "Task2", "Task3 1", "Task4 1"])
simple(G, "tudo ligado -> Task3/4 dão -2", 4, [(1,2),(2,3),(3,4)], ["Task1","Task2","Task3 2","Task4 3"])
simple(G, "nenhuma ligação (todos isolados)", 6, [], ["Task1","Task2","Task3 1","Task4 6"])
simple(G, "cidade 0 / negativa / C+1 (fora do mapa)", 5, [(1,2)], ["Task3 0","Task4 0","Task3 -1","Task4 6","Task3 21"])
simple(G, "ligações duplicadas, invertidas e auto-laços", 6, [(1,2),(2,1),(1,2),(3,3),(4,5),(5,4)], ["Task1","Task2"])
simple(G, "mesmo Task3 repetido para cidades diferentes", 8, [(1,2),(3,4)], ["Task3 1","Task3 5","Task3 1","Task3 8","Task3 3"])
pos_tie = {1:(1,1),2:(3,1),3:(1,3),4:(2,2)}
simple(G, "empate de distância -> menor número de cidade (Task3)", 4, [(1,4)], ["Task3 1"], pos=pos_tie)
pos_tie4 = {1:(5,5),2:(5,6),3:(1,5),4:(9,5),5:(5,1),6:(5,9)}
simple(G, "empate de distância em Task4", 6, [(1,2)], ["Task4 1","Task4 2","Task3 2"], pos=pos_tie4)
simple(G, "Task4 != Task3 (exemplo do enunciado)", 5, [(1,2),(2,3)], ["Task3 1","Task4 1"],
       pos={1:(1,1),2:(2,2),3:(9,9),4:(10,10),5:(3,3)})
_p10={1:(1,1),2:(2,2),3:(60000,60000),4:(60000,1)}
check_valid(G, "coordenadas 60000 (overflow int nas distâncias)", "Task3 1\nTask4 1\nTask4 3\n", map_text(4,[(1,2)]),
            pos_text(_p10, 60000, 60000), reference(4,[(1,2)],_p10,["Task3 1","Task4 1","Task4 3"]))
# xmax grande
pos_big = {1:(1,1),2:(2,1),3:(2000000000,2000000000),4:(2000000000,1)}
check_valid(G, "coordenadas até 2e9 (long long necessário)", "Task3 1\nTask4 3\n", map_text(4,[(1,2)]),
            pos_text(pos_big, 2000000000, 2000000000), reference(4,[(1,2)],pos_big,["Task3 1","Task4 3"]))
simple(G, "ficheiro .quests vazio", 3, [(1,2)], [])  # esperado: .results vazio
check_valid(G, "L=0 com cabeçalho só", "Task1\nTask2\n", "5 0\n", pos_text(mk_pos(5)),
            reference(5, [], mk_pos(5), ["Task1","Task2"]))
check_valid(G, "L maior que nº de linhas reais", "Task1\nTask2\n", "5 10\n1 2\n", pos_text(mk_pos(5)),
            reference(5, [(1,2)], mk_pos(5), ["Task1","Task2"]))
check_valid(G, "L menor que nº de linhas reais (linhas extra)", "Task1\nTask2\n", "5 1\n1 2\n3 4\n", pos_text(mk_pos(5)),
            reference(5, [(1,2)], mk_pos(5), ["Task1","Task2"]))

G = "B. formato do .quests"
q = lambda s: s
pos6 = mk_pos(6)
exp = lambda ql: reference(6, [(1,2)], pos6, ql)
for nm, txt, ql in [
    ("fim de linha CRLF (Windows)", "Task1\r\nTask3 1\r\nTask2\r\n", ["Task1","Task3 1","Task2"]),
    ("sem \\n no fim do ficheiro", "Task1\nTask3 1", ["Task1","Task3 1"]),
    ("linha em branco no meio", "Task1\n\nTask3 1\n", ["Task1","Task3 1"]),
    ("linha em branco no fim", "Task1\nTask3 1\n\n\n", ["Task1","Task3 1"]),
    ("espaços no fim das linhas", "Task1  \nTask3 1  \nTask2 \n", ["Task1","Task3 1","Task2"]),
    ("espaços/tab antes do número", "Task3   1\nTask4\t2\n", ["Task3 1","Task4 2"]),
    ("espaços no início da linha", "  Task1\n Task3 1\n", ["Task1","Task3 1"]),
]:
    check_valid(G, nm, txt, map_text(6,[(1,2)]), pos_text(pos6), exp(ql))
# casos sem referência clara: apenas não podem crashar / não podem parar o resto
for nm, txt in [
    ("Task3 sem argumento", "Task1\nTask3\nTask2\n"),
    ("Task3 com argumento não numérico", "Task1\nTask3 abc\nTask2\n"),
    ("Task desconhecida (Task9)", "Task1\nTask9\nTask2\n"),
    ("linha de lixo", "Task1\nfoo bar\nTask2\n"),
    ("Task3 com número gigante (>int)", "Task1\nTask3 99999999999\nTask2\n"),
    ("Task3 com 2 argumentos", "Task1\nTask3 1 2\nTask2\n"),
    ("Task1 com argumento extra", "Task1 7\nTask2\n"),
]:
    d = tempfile.mkdtemp(prefix="hk_")
    try:
        open(f"{d}/t.quests","w").write(txt); open(f"{d}/t.map","w").write(map_text(6,[(1,2)])); open(f"{d}/t.position","w").write(pos_text(pos6))
        rc, so, se, el = run(BIN, d, ["t.quests","t.map","t.position"])
        got = open(f"{d}/t.results").read() if os.path.exists(f"{d}/t.results") else None
        if rc != 0:
            results.append((G, nm, "CRASH/EXIT≠0", f"rc={rc}"))
        else:
            has2 = got is not None and "Task2 5" in got
            results.append((G, nm, "OK (continua)" if has2 else "INFO: pára de processar", repr((got or "")[:90])))
    finally:
        shutil.rmtree(d, ignore_errors=True)

G = "C. validação do .map (ids fora de {1..C})"
for nm, edges in [("ligação com cidade 0", [(0,1)]), ("ligação com cidade C+1", [(1,7)]),
                  ("ligação com id negativo", [(-3,2)]), ("ligação com id enorme", [(1,1000000)])]:
    d = tempfile.mkdtemp(prefix="hk_")
    try:
        open(f"{d}/t.quests","w").write("Task1\nTask2\n"); open(f"{d}/t.map","w").write(map_text(6,edges)); open(f"{d}/t.position","w").write(pos_text(pos6))
        rc, so, se, el = run(BIN, d, ["t.quests","t.map","t.position"])
        if rc != 0:
            det = f"rc={rc}"
            if ASAN:
                _,_,se2,_ = run(ASAN, d, ["t.quests","t.map","t.position"])
                ln = [l for l in (se2 or b"").decode(errors="replace").splitlines() if "ERROR" in l or "runtime error" in l]
                det += " | ASan: " + (ln[0][:120] if ln else "-")
            results.append((G, nm, "CRASH/EXIT≠0", det))
        else:
            got = open(f"{d}/t.results").read() if os.path.exists(f"{d}/t.results") else None
            results.append((G, nm, "OK (sem crash)", repr((got or "NONE")[:60])))
    finally:
        shutil.rmtree(d, ignore_errors=True)

G = "D. validação do .position (deve terminar SEM output)"
P = lambda s: s
bad_pos = [
    ("coordenada X > Xmax", "10 10\n1 11 1\n2 1 1\n3 1 1\n"),
    ("coordenada Y > Ymax", "10 10\n1 1 11\n2 1 1\n3 1 1\n"),
    ("coordenada 0", "10 10\n1 0 1\n2 1 1\n3 1 1\n"),
    ("coordenada negativa", "10 10\n1 -1 1\n2 1 1\n3 1 1\n"),
    ("falta uma cidade (menos linhas)", "10 10\n1 1 1\n2 1 1\n"),
    ("id duplicado (falta cidade 3)", "10 10\n1 1 1\n2 1 1\n2 3 3\n"),
    ("id fora de {1..C} (4)", "10 10\n1 1 1\n2 1 1\n4 1 1\n"),
    ("id 0", "10 10\n1 1 1\n2 1 1\n0 1 1\n"),
    ("valor não numérico", "10 10\n1 1 1\n2 a 1\n3 1 1\n"),
    ("linha incompleta", "10 10\n1 1 1\n2 1\n3 1 1\n"),
    ("ficheiro vazio", ""),
    ("Xmax=0", "0 10\n1 1 1\n2 1 1\n3 1 1\n"),
    ("só cabeçalho", "10 10\n"),
    ("coordenada decimal (1.5)", "10 10\n1 1.5 1\n2 1 1\n3 1 1\n"),
]
for nm, txt in bad_pos:
    check_valid(G, nm, "Task1\nTask2\nTask3 1\n", map_text(3,[(1,2)]), txt, None)

G = "E. validação do .map (cabeçalho)"
for nm, txt in [("C=0", "0 0\n"), ("C negativo", "-3 0\n"), ("L negativo", "3 -1\n"),
                ("ficheiro vazio", ""), ("só um número", "3\n"), ("cabeçalho não numérico", "x y\n")]:
    check_valid(G, nm, "Task1\nTask2\n", txt, pos_text(mk_pos(3)), None)

G = "F. invocação / nomes de ficheiros"
check_valid(G, "nome com vários pontos (a.b.quests)", "Task1\nTask2\n", map_text(3,[(1,2)]), pos_text(mk_pos(3)),
            reference(3,[(1,2)],mk_pos(3),["Task1","Task2"]), qname="a.b.quests", mname="c.d.map", pname="e.f.position")
check_valid(G, "caminho relativo ./x.quests ./x.map ./x.position", "Task1\n", map_text(3,[(1,2)]), pos_text(mk_pos(3)),
            reference(3,[(1,2)],mk_pos(3),["Task1"]), args=["./t.quests","./t.map","./t.position"])
check_valid(G, "caminho com directório com ponto (dir.v1/t.quests)", "Task1\n", map_text(3,[(1,2)]), pos_text(mk_pos(3)),
            reference(3,[(1,2)],mk_pos(3),["Task1"]), subdir="dir.v1")
check_valid(G, "nome só números (013.quests)", "Task1\n", map_text(3,[(1,2)]), pos_text(mk_pos(3)),
            reference(3,[(1,2)],mk_pos(3),["Task1"]), qname="013.quests", mname="013.map", pname="013.position")
check_valid(G, "nome com espaço (a b.quests)", "Task1\n", map_text(3,[(1,2)]), pos_text(mk_pos(3)),
            reference(3,[(1,2)],mk_pos(3),["Task1"]), qname="a b.quests", mname="a b.map", pname="a b.position")
check_valid(G, "nome com 200 caracteres", "Task1\n", map_text(3,[(1,2)]), pos_text(mk_pos(3)),
            reference(3,[(1,2)],mk_pos(3),["Task1"]), qname="q"*200+".quests", mname="m"*200+".map", pname="p"*200+".position")
check_valid(G, "nome com 1100 caracteres (buffer result[1024])", "Task1\n", map_text(3,[(1,2)]), pos_text(mk_pos(3)),
            reference(3,[(1,2)],mk_pos(3),["Task1"]), qname="q"*100+".quests", mname="m.map", pname="p.position") if False else None
# três ficheiros com o mesmo nome base
check_valid(G, "mesmo nome base nos 3 (x.quests x.map x.position)", "Task1\n", map_text(3,[(1,2)]), pos_text(mk_pos(3)),
            reference(3,[(1,2)],mk_pos(3),["Task1"]), qname="x.quests", mname="x.map", pname="x.position")
# argumentos errados -> sem output
def args_case(name, files, args, expect_none=True):
    d = tempfile.mkdtemp(prefix="hk_")
    try:
        for f, c in files.items(): open(f"{d}/{f}", "w").write(c)
        rc, so, se, el = run(BIN, d, args)
        created = [f for f in os.listdir(d) if f not in files]
        if rc != 0: results.append((G, name, "CRASH/EXIT≠0", f"rc={rc}"))
        elif so or se: results.append((G, name, "OUTPUT EXTRA", "stdout/stderr"))
        elif created: results.append((G, name, "FALHA", f"criou ficheiros: {created} (devia não produzir output)"))
        else: results.append((G, name, "OK", "sem output"))
    finally: shutil.rmtree(d, ignore_errors=True)
F3 = {"t.quests":"Task1\n","t.map":"3 1\n1 2\n","t.position":pos_text(mk_pos(3))}
args_case("0 argumentos", F3, [])
args_case("2 argumentos", F3, ["t.quests","t.map"])
args_case("4 argumentos", F3, ["t.quests","t.map","t.position","t.quests"])
args_case("ficheiro .quests não existe", {"t.map":F3["t.map"],"t.position":F3["t.position"]}, ["x.quests","t.map","t.position"])
args_case("ficheiro .map não existe", {"t.quests":"Task1\n","t.position":F3["t.position"]}, ["t.quests","x.map","t.position"])
args_case("ficheiro .position não existe", {"t.quests":"Task1\n","t.map":F3["t.map"]}, ["t.quests","t.map","x.position"])
args_case("extensão errada (.txt)", {**F3,"t.txt":"x"}, ["t.quests","t.map","t.txt"])
args_case("extensões trocadas (.map .quests .position)", F3, ["t.map","t.quests","t.position"])
args_case("sem extensão", {**F3,"noext":"x"}, ["t.quests","t.map","noext"])
args_case("duas .quests e nenhum .map", {**F3,"u.quests":"Task1\n"}, ["t.quests","u.quests","t.position"])
args_case("extensão com maiúsculas (.QUESTS)", {"t.QUESTS":"Task1\n","t.map":F3["t.map"],"t.position":F3["t.position"]}, ["t.QUESTS","t.map","t.position"])
args_case("string vazia como argumento", F3, ["","t.map","t.position"])
args_case("argumento só '.quests' sem nome", {".quests":"Task1\n","t.map":F3["t.map"],"t.position":F3["t.position"]}, [".quests","t.map","t.position"])

# ---------------------------------------------------------------- desempenho
G = "G. desempenho (limite 10 s)"
def perf(name, n, edges_gen, quests):
    print(f'  [desempenho] a correr: {name} ...', flush=True)
    d = tempfile.mkdtemp(prefix="hk_")
    try:
        rnd = random.Random(5)
        edges = edges_gen(n, rnd)
        pos = {i: (rnd.randint(1, 30000), rnd.randint(1, 30000)) for i in range(1, n + 1)}
        open(f"{d}/t.quests","w").write("\n".join(quests) + "\n")
        open(f"{d}/t.map","w").write(map_text(n, edges))
        open(f"{d}/t.position","w").write(pos_text(pos, 30000, 30000))
        rc, so, se, el = run(BIN, d, ["t.quests","t.map","t.position"], timeout=PERF_KILL)
        if rc is None:
            results.append((G, name, "LENTO (>10 s)", f"cortado aos {PERF_KILL:.0f} s")); return
        ok = ""
        if el <= TL and n <= 3000:
            got = open(f"{d}/t.results").read()
            ok = " resultado ✔" if got == reference(n, edges, pos, quests) else " RESULTADO ERRADO"
        print(f'  [desempenho] {name}: {el:.2f}s', flush=True)
        v = "OK" if el <= TL and rc == 0 else ("LENTO (>10 s)" if rc == 0 else "CRASH")
        results.append((G, name, v, f"{el:.2f}s{ok}"))
    finally:
        shutil.rmtree(d, ignore_errors=True)
none = lambda n, r: []
chain = lambda n, r: [(i, i + 1) for i in range(1, n)]
rand_sparse = lambda n, r: [(r.randint(1, n), r.randint(1, n)) for _ in range(n // 2)]
rand_dense = lambda n, r: [(r.randint(1, n), r.randint(1, n)) for _ in range(4 * n)]
perf("Task1 | 200k cidades sem ligações", 200000, none, ["Task1"])
perf("Task2 | 50k cidades, todas isoladas", 50000, none, ["Task2"])
perf("Task2 | 100k cidades, todas isoladas", 100000, none, ["Task2"])
perf("Task2 | 100k cidades, ~metade ligadas (muitos clusters)", 100000, rand_sparse, ["Task2"])
perf("Task1+Task2 | 300k cidades, 1 cluster (cadeia)", 300000, chain, ["Task1","Task2"])
perf("Task3 x1000 | 100k cidades", 100000, rand_sparse, [f"Task3 {i}" for i in range(1, 1001)])
perf("Task4 x20 | 100k cidades, clusters pequenos", 100000, rand_sparse, [f"Task4 {i}" for i in range(1, 21)])
perf("Task4 x1000 | 20k cidades", 20000, rand_sparse, [f"Task4 {i}" for i in range(1, 1001)])
perf("Task4 x1 | 2 clusters grandes (50k+50k)", 100000, lambda n, r: [(i, i+1) for i in range(1, 50000)] + [(i, i+1) for i in range(50001, 100000)], ["Task4 1"])
perf("Task4 x1 | cluster gigante + 1 cidade fora (n=300k)", 300000, lambda n, r: [(i, i+1) for i in range(1, n-1)], ["Task4 1"])
perf("Task4 x100 | cluster gigante + 1 cidade fora (n=300k)", 300000, lambda n, r: [(i, i+1) for i in range(1, n-1)], ["Task4 1"]*100)
perf("mapa grande: 500k cidades, 2M ligações, Task1", 500000, lambda n, r: [(r.randint(1,n), r.randint(1,n)) for _ in range(2000000)], ["Task1"])

# ---------------------------------------------------------------- relatório
order = []
for g, n, v, d in results:
    if g not in order: order.append(g)
bad = 0
lines = ["# Relatório de casos-limite — HealkrISTin (fase 1)\n"]
for g in order:
    lines.append(f"\n## {g}\n\n| # | Caso | Veredicto | Detalhe |\n|---|---|---|---|")
    for i, (gg, n, v, d) in enumerate([r for r in results if r[0] == g], 1):
        flag = "✅" if v.startswith("OK") else ("ℹ️" if v.startswith("INFO") else "❌")
        if flag == "❌": bad += 1
        lines.append(f"| {i} | {n} | {flag} {v} | {d.replace('|','/')} |")
lines.append(f"\n**Total: {len(results)} casos, {bad} falhas.**")
rep = "\n".join(lines)
print(rep)
open("relatorio_casos_limite.md", "w").write(rep + "\n")
