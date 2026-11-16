#!/usr/bin/env python3
"""Casos-limite dirigidos para o HealkrISTin (fase 1 + fase final: Task5 e Task6).
Uso: python3 edge_cases.py [./healkristin] [./binario_asan] [--fase2] [--skip-perf]
  --fase2      corre só os grupos H-K (Task5/Task6), salta os da fase 1 (A-G)
  --skip-perf  salta os testes de desempenho (G e K)
Cada caso cria os ficheiros num directório temporário, corre o binário,
e compara com a resposta esperada (referência independente em Python)."""
import os, sys, subprocess, tempfile, shutil, time, resource, signal, random

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
FASE2_ONLY = "--fase2" in sys.argv
SKIP_PERF = "--skip-perf" in sys.argv
BIN = os.path.abspath(ARGS[0] if ARGS else "./healkristin")
if not os.path.exists(BIN):
    sys.exit(f"Binário não encontrado: {BIN}\nCompila primeiro (make) e corre na pasta do projecto:\n  python3 edge_cases.py [./healkristin] [./binario_asan]")
ASAN = os.path.abspath(ARGS[1]) if len(ARGS) > 1 else None
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

if not FASE2_ONLY:
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
        if SKIP_PERF:
            return
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


# ======================================================================
# FASE FINAL: Task5 (MST entre clusters) e Task6 (rota de restauro)
# ======================================================================
# Modelo usado (derivado do enunciado, secção 5):
#  * Task5: ligar todos os clusters com o mínimo de cabo. Cada ligação junta duas
#    cidades de clusters diferentes (distância euclidiana). Output:
#        Task5 <total:.2f>
#        <menor> <maior> <dist:.2f>     (ordenadas por menor, depois por maior)
#    Total = soma das distâncias EXACTAS (sem arredondar) e só depois .2f.
#  * Task6 <s>: rota fechada que começa e acaba em s e percorre TODAS as ligações
#    da Task5 (cada uma como um passo, em qualquer sentido). Entre restauros
#    consecutivos a equipa desloca-se em linha recta entre cidades (passo de
#    "transição"). Output:
#        Task6 <extra:.2f>              (extra = soma das transições = rota - cabo)
#        <a> <b> <dist:.2f>             (um passo por linha, pela ordem de passagem)
#    Não se imprime passo de comprimento a==b (quando o fim de um restauro é o
#    início do seguinte não há passo de transição).
#  * cidade s fora de 1..C  ->  "Task6 <s> -2"   (secção 4.1).
import math, re, itertools

RE_LINK = re.compile(r"(\d+) (\d+) (\d+\.\d\d)")
EXACT_K = 11          # até k ligações verifica-se o ÓPTIMO da Task6 (DP exacta)
OPT_N   = 1500        # até n cidades verifica-se o ÓPTIMO da Task5 (Prim O(n^2) em Python)

def d2(pos, a, b):
    return (pos[a][0] - pos[b][0]) ** 2 + (pos[a][1] - pos[b][1]) ** 2

def dd(pos, a, b):
    return math.sqrt(d2(pos, a, b))     # int -> float -> sqrt, igual a sqrt((double)long long) em C

def roots_of(n, edges):
    par = list(range(n + 1))
    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for a, b in edges:
        if 1 <= a <= n and 1 <= b <= n:
            par[f(a)] = f(b)
    return [0] + [f(c) for c in range(1, n + 1)]

def mst_links(n, root, pos):
    """MST entre clusters (Prim com clusters contraídos). Desempate pela ordem total
    (dist^2, menor, maior): sob esta ordem a MST é única -> é a resposta 'canónica'."""
    members = {}
    for c in range(1, n + 1):
        members.setdefault(root[c], []).append(c)
    if len(members) <= 1:
        return []
    key = [None] * (n + 1)
    intree = [False] * (n + 1)
    links = []
    def add_cluster(r):
        for i in members[r]:
            intree[i] = True
        for i in members[r]:
            xi, yi = pos[i]
            for j in range(1, n + 1):
                if intree[j]:
                    continue
                d = (pos[j][0] - xi) ** 2 + (pos[j][1] - yi) ** 2
                k = (d, i, j) if i < j else (d, j, i)
                if key[j] is None or k < key[j]:
                    key[j] = k
    add_cluster(root[1])
    for _ in range(len(members) - 1):
        bj = None
        for j in range(1, n + 1):
            if not intree[j] and key[j] is not None and (bj is None or key[j] < key[bj]):
                bj = j
        d, lo, hi = key[bj]
        links.append((lo, hi))
        add_cluster(root[bj])
    links.sort()
    return links

def mst_is_unique(n, root, pos, links):
    """True se nenhuma outra aresta (entre clusters) pode substituir uma da árvore (sem empates)."""
    adj = {}
    for a, b in links:
        w = d2(pos, a, b)
        adj.setdefault(root[a], []).append((root[b], w)); adj.setdefault(root[b], []).append((root[a], w))
    def pathmax(a, b):
        st = [(a, None, 0)]
        while st:
            u, p, m = st.pop()
            if u == b:
                return m
            for v, w in adj.get(u, []):
                if v != p:
                    st.append((v, u, max(m, w)))
        return -1
    chosen = set(links)
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if root[i] != root[j] and (i, j) not in chosen and d2(pos, i, j) <= pathmax(root[i], root[j]):
                return False
    return True

def route_opt(pos, links, s):
    """Extra mínimo da Task6 (Held-Karp sobre ligações orientadas). links=[(a,b)]."""
    k = len(links)
    if k == 0:
        return 0.0
    sc = [links[e][o] for e in range(k) for o in (0, 1)]
    ec = [links[e][1 - o] for e in range(k) for o in (0, 1)]
    m = 2 * k
    D = [[dd(pos, ec[a], sc[b]) for b in range(m)] for a in range(m)]
    INF = float("inf")
    dp = [[INF] * m for _ in range(1 << k)]
    for a in range(m):
        dp[1 << (a // 2)][a] = dd(pos, s, sc[a])
    for mask in range(1, 1 << k):
        row = dp[mask]
        for a in range(m):
            c = row[a]
            if c == INF:
                continue
            Da = D[a]
            for b in range(m):
                if (mask >> (b // 2)) & 1:
                    continue
                v = c + Da[b]
                nm = mask | (1 << (b // 2))
                if v < dp[nm][b]:
                    dp[nm][b] = v
    full = (1 << k) - 1
    return min(dp[full][a] + dd(pos, ec[a], s) for a in range(m))

def parse_links(lines):
    out = []
    for ln in lines:
        m = RE_LINK.fullmatch(ln)
        if not m:
            return None
        out.append((int(m.group(1)), int(m.group(2)), m.group(3)))
    return out

def check5(lines, n, root, pos, canon, unique, opt_check):
    """('OK'|'INFO'|'FALHA', detalhe)"""
    k = len(set(root[1:]))
    if k == 1:
        if lines == ["Task5 0.00"]:
            return "OK", ""
        if lines == ["Task5 -2"]:
            return "INFO", "1 cluster -> imprimiu 'Task5 -2' (ambíguo: o custo é 0.00 e não há ligações)"
        return "FALHA", f"1 cluster: esperado 'Task5 0.00' sem ligações; obtido {lines[:3]!r}"
    m = re.fullmatch(r"Task5 (\d+\.\d\d)", lines[0])
    if not m:
        return "FALHA", f"cabeçalho inválido (esperado 'Task5 <x.xx>'): {lines[0]!r}"
    header = m.group(1)
    ls = parse_links(lines[1:])
    if ls is None:
        bad = next(l for l in lines[1:] if not RE_LINK.fullmatch(l))
        return "FALHA", f"linha de ligação mal formatada (esperado '<a> <b> <d.dd>'): {bad!r}"
    if len(ls) != k - 1:
        return "FALHA", f"{k} clusters precisam de {k-1} ligações, o programa imprimiu {len(ls)}"
    par = {}
    def f(a):
        par.setdefault(a, a)
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    prev = None
    ds = []
    for a, b, ds_ in ls:
        if not (1 <= a <= n and 1 <= b <= n):
            return "FALHA", f"cidade fora de 1..{n} na ligação {a} {b}"
        if a >= b:
            return "FALHA", f"ligação '{a} {b}': a cidade de MENOR índice tem de vir primeiro"
        if prev is not None and (a, b) <= prev:
            return "FALHA", f"ligações fora de ordem / repetidas: '{prev[0]} {prev[1]}' antes de '{a} {b}'"
        prev = (a, b)
        if root[a] == root[b]:
            return "FALHA", f"ligação '{a} {b}' une cidades do MESMO cluster (inútil)"
        ra, rb = f(root[a]), f(root[b])
        if ra == rb:
            return "FALHA", f"ligação '{a} {b}' fecha um ciclo entre clusters (não é árvore)"
        par[ra] = rb
        d = dd(pos, a, b)
        if f"{d:.2f}" != ds_:
            return "FALHA", f"distância de '{a} {b}': esperado {d:.2f}, obtido {ds_}"
        ds.append(d)
    listed = math.fsum(ds)
    if header != f"{listed:.2f}":
        alt = f"{sum(float(f'{d:.2f}') for d in ds):.2f}"
        extra = " (igual à soma das distâncias JÁ arredondadas: somar os valores exactos e só depois arredondar)" if header == alt else ""
        return "FALHA", f"total {header} != soma das ligações impressas {listed:.2f}{extra}"
    if not opt_check or canon is None:
        return "INFO", "válido (árvore, ordem, formato), mas óptimo NÃO verificado (n grande)"
    opt = math.fsum(dd(pos, a, b) for a, b in canon)
    if listed > opt + 1e-6 * max(1.0, opt):
        return "FALHA", f"não é mínimo: total {listed:.2f} > óptimo {opt:.2f}"
    if listed < opt - 1e-6 * max(1.0, opt):
        return "FALHA", f"total {listed:.2f} < óptimo {opt:.2f} (impossível: ligações inválidas?)"
    if header != f"{opt:.2f}":
        return "FALHA", f"total {header} != óptimo {opt:.2f}"
    got = {(a, b) for a, b, _ in ls}
    if got == set(canon):
        return "OK", ""
    if unique:
        return "FALHA", f"MST é única mas as ligações diferem: esperado {sorted(set(canon)-got)[:4]} / obtido {sorted(got-set(canon))[:4]}"
    return "INFO", "empate: MST alternativa válida (total óptimo, ligações diferentes da canónica)"

def check6(lines, s, n, root, pos, req, opt_check):
    """req = lista (a,b) de ligações obrigatórias (as da Task5) ou None."""
    if not (1 <= s <= n):
        return ("OK", "") if lines == [f"Task6 {s} -2"] else ("FALHA", f"cidade {s} fora do mapa: esperado 'Task6 {s} -2', obtido {lines[:2]!r}")
    k = len(set(root[1:]))
    if k == 1:
        if lines == ["Task6 0.00"]:
            return "OK", ""
        if lines == [f"Task6 {s} -2"]:
            return "INFO", "1 cluster -> imprimiu 'Task6 s -2' (ambíguo: não há restauros, extra 0.00)"
        return "FALHA", f"1 cluster (nada a restaurar): esperado 'Task6 0.00' sem passos; obtido {lines[:3]!r}"
    m = re.fullmatch(r"Task6 (\d+\.\d\d)", lines[0])
    if not m:
        return "FALHA", f"cabeçalho inválido (esperado 'Task6 <x.xx>'): {lines[0]!r}"
    header = m.group(1)
    st = parse_links(lines[1:])
    if st is None:
        bad = next(l for l in lines[1:] if not RE_LINK.fullmatch(l))
        return "FALHA", f"passo mal formatado (esperado '<a> <b> <d.dd>'): {bad!r}"
    if not st:
        return "FALHA", "rota vazia (há ligações por restaurar)"
    cur = s
    total = []
    for i, (a, b, dstr) in enumerate(st, 1):
        if not (1 <= a <= n and 1 <= b <= n):
            return "FALHA", f"passo {i}: cidade fora de 1..{n}"
        if a == b:
            return "FALHA", f"passo {i}: '{a} {b}' tem origem = destino (não se imprimem passos nulos)"
        if a != cur:
            return "FALHA", f"passo {i}: devia partir de {cur} (onde a rota ficou) mas parte de {a}"
        d = dd(pos, a, b)
        if f"{d:.2f}" != dstr:
            return "FALHA", f"passo {i} ({a} {b}): distância esperada {d:.2f}, obtida {dstr}"
        total.append(d); cur = b
    if cur != s:
        return "FALHA", f"a rota termina em {cur} mas tem de regressar à cidade de partida {s}"
    if req is None:
        return "INFO", "rota válida (fecha em s) mas ligações a restaurar desconhecidas"
    seen = {(min(a, b), max(a, b)) for a, b, _ in st}
    miss = [e for e in req if e not in seen]
    if miss:
        return "FALHA", f"ligações por restaurar que não aparecem como passo: {miss[:4]}"
    cable = math.fsum(dd(pos, a, b) for a, b in req)
    extra = math.fsum(total) - cable
    if header != f"{max(extra, 0.0):.2f}":
        tot_alt = f"{math.fsum(total):.2f}"
        note = " (isto é o comprimento TOTAL da rota; o cabeçalho é só a parte sem cabo)" if header == tot_alt else ""
        return "FALHA", f"cabeçalho {header} != soma das transições {extra:.2f}{note}"
    if not opt_check or len(req) > EXACT_K:
        return "INFO", f"rota válida, extra={extra:.2f}; óptimo NÃO verificado (k={len(req)} > {EXACT_K} ou n grande)"
    opt = route_opt(pos, req, s)
    if extra > opt + 1e-6 * max(1.0, opt):
        return "FALHA", f"rota não óptima: extra {extra:.2f} > óptimo {opt:.2f}"
    if extra < opt - 1e-6 * max(1.0, opt):
        return "FALHA", f"extra {extra:.2f} < óptimo {opt:.2f} (impossível: faltam ligações?)"
    return "OK", ""

# ---------------------------------------------------------------- gerador de mapas
def gen_map(n, c, rnd, xmax, ymax):
    """n cidades em exactamente c clusters (cada cluster ligado), posições aleatórias."""
    cities = list(range(1, n + 1)); rnd.shuffle(cities)
    groups = [[] for _ in range(c)]
    for i, city in enumerate(cities):
        groups[i if i < c else rnd.randrange(c)].append(city)
    edges = []
    for g in groups:
        for a, b in zip(g, g[1:]):
            edges.append((a, b) if rnd.random() < .5 else (b, a))
        if len(g) > 2:
            for _ in range(rnd.randint(0, 2)):
                edges.append((rnd.choice(g), rnd.choice(g)))
    rnd.shuffle(edges)
    pos = {i: (rnd.randint(1, xmax), rnd.randint(1, ymax)) for i in range(1, n + 1)}
    return edges, pos

def gen_unique(n, c, seed, xmax=100000, ymax=100000):
    for t in range(500):
        rnd = random.Random(seed * 1000 + t)
        edges, pos = gen_map(n, c, rnd, xmax, ymax)
        root = roots_of(n, edges)
        links = mst_links(n, root, pos)
        if mst_is_unique(n, root, pos, links):
            return edges, pos
    raise RuntimeError("não consegui gerar caso com MST única")

# ---------------------------------------------------------------- execução de um caso
def f2_case(group, name, n, edges, pos, qlines, xmax=None, ymax=None, perf=False,
            force_tie=False, raw=None):
    d = tempfile.mkdtemp(prefix="hk2_")
    try:
        xm = xmax or max(p[0] for p in pos.values()); ym = ymax or max(p[1] for p in pos.values())
        open(f"{d}/t.quests", "w", newline="").write(raw if raw is not None else "\n".join(qlines) + "\n")
        open(f"{d}/t.map", "w").write(map_text(n, edges))
        open(f"{d}/t.position", "w").write(pos_text(pos, xm, ym))
        a = ["t.quests", "t.map", "t.position"]
        rc, so, se, el = run(BIN, d, a, timeout=PERF_KILL if perf else TL * 3)
        if rc is None:
            results.append((group, name, "LENTO (>10 s)", f"cortado aos {(PERF_KILL if perf else TL*3):.0f} s")); return
        if rc != 0:
            det = f"sinal {signal.Signals(-rc).name}" if rc < 0 else f"exit {rc}"
            if ASAN:
                _, _, se2, _ = run(ASAN, d, a)
                ln = [l for l in (se2 or b"").decode(errors="replace").splitlines() if "ERROR" in l or "runtime error" in l]
                det += " | ASan: " + (ln[0][:140] if ln else "-")
            results.append((group, name, "CRASH/EXIT≠0", det)); return
        if so or se:
            results.append((group, name, "OUTPUT EXTRA", "stdout/stderr não vazio")); return
        rp = f"{d}/t.results"
        if not os.path.exists(rp):
            results.append((group, name, "FALHA", "não criou o ficheiro .results")); return
        text = open(rp, newline="").read()
        v, det = f2_verify(text, qlines, n, edges, pos, d, force_tie, perf)
        if el > TL:
            results.append((group, name, "LENTO (>10 s)", f"{el:.2f}s " + det)); return
        results.append((group, name, v if v in ("OK", "INFO") else "FALHA",
                        (f"{el:.2f}s " + det).strip()))
    finally:
        shutil.rmtree(d, ignore_errors=True)

def f2_verify(text, qlines, n, edges, pos, d, force_tie, perf):
    if text == "":
        return "FALHA", ".results vazio: o programa não escreveu nada (Task5/Task6 ainda não implementadas?)"
    if not text.endswith("\n\n"):
        return "FALHA", "o ficheiro tem de terminar com uma linha em branco (cada bloco acaba em \\n\\n)"
    if "\n\n\n" in text:
        return "FALHA", "linhas em branco a mais entre blocos"
    if "\r" in text or re.search(r"[ \t]\n", text):
        return "FALHA", "espaço/tab/\\r no fim de uma linha do output"
    blocks = text[:-2].split("\n\n")
    if len(blocks) != len(qlines):
        return "FALHA", f"{len(qlines)} tarefas mas {len(blocks)} blocos de resposta (blocos: {[b.split(chr(10))[0] for b in blocks][:6]})"
    root = roots_of(n, edges)
    has56 = any(q.split()[0] in ("Task5", "Task6") for q in qlines)
    canon, unique = None, False
    if has56 and n <= OPT_N:
        canon = mst_links(n, root, pos)
        unique = (not force_tie) and n <= 80 and mst_is_unique(n, root, pos, canon)
    req = canon
    if has56 and canon is not None and not unique and any(q.startswith("Task6") for q in qlines):
        # empate: usa as ligações que o PRÓPRIO programa escolheu na Task5 (tem de existir uma)
        t5 = None
        for q, b in zip(qlines, blocks):
            if q.split()[0] == "Task5":
                t5 = parse_links(b.split("\n")[1:]); break
        if t5 is None:
            open(f"{d}/u.quests", "w").write("Task5\n")
            rc, _, _, _ = run(BIN, d, ["u.quests", "t.map", "t.position"])
            if rc == 0 and os.path.exists(f"{d}/u.results"):
                t5 = parse_links(open(f"{d}/u.results").read().strip("\n").split("\n")[1:])
        req = [(a, b) for a, b, _ in t5] if t5 else None
    worst = ("OK", "")
    for i, (q, b) in enumerate(zip(qlines, blocks), 1):
        t = q.split()
        if t[0] in ("Task1", "Task2", "Task3", "Task4"):
            if n > 3000:
                continue
            exp = reference(n, edges, pos, [q])[:-2]
            if b != exp:
                return "FALHA", f"linha {i} '{q}': esperado {exp[:80]!r} obtido {b[:80]!r}"
        elif t[0] == "Task5":
            v, det = check5(b.split("\n"), n, root, pos, canon, unique, n <= OPT_N)
            if v == "FALHA":
                return "FALHA", f"linha {i} '{q}': {det}"
            if v == "INFO" and worst[0] == "OK":
                worst = (v, f"linha {i}: {det}")
        elif t[0] == "Task6":
            v, det = check6(b.split("\n"), int(t[1]), n, root, pos, req, n <= OPT_N)
            if v == "FALHA":
                return "FALHA", f"linha {i} '{q}': {det}"
            if v == "INFO" and worst[0] == "OK":
                worst = (v, f"linha {i}: {det}")
    return worst

def f2_ambig(group, name, quests_txt, n=6, edges=None, pos=None, expect_k=None):
    """Entradas mal formadas na .quests que o enunciado não define por completo.
    Falha só se crashar ou deixar de processar as linhas seguintes; o resto é informativo."""
    edges = edges if edges is not None else [(1, 2)]
    pos = pos or mk_pos(n, 1000, 1000, seed=3)
    d = tempfile.mkdtemp(prefix="hk2_")
    try:
        open(f"{d}/t.quests", "w", newline="").write(quests_txt)
        open(f"{d}/t.map", "w").write(map_text(n, edges)); open(f"{d}/t.position", "w").write(pos_text(pos, 1000, 1000))
        rc, so, se, el = run(BIN, d, ["t.quests", "t.map", "t.position"])
        if rc is None:
            results.append((group, name, "LENTO (>10 s)", "bloqueou")); return
        if rc != 0:
            results.append((group, name, "CRASH/EXIT≠0", f"rc={rc}")); return
        got = open(f"{d}/t.results", newline="").read() if os.path.exists(f"{d}/t.results") else ""
        k = len(set(roots_of(n, edges)[1:]))
        cont = f"Task2 {k}" in got
        results.append((group, name, "INFO: continua" if cont else "FALHA", ("" if cont else "deixou de processar as linhas seguintes | ") + repr(got[:100])))
    finally:
        shutil.rmtree(d, ignore_errors=True)

# ================================================================== CASOS Task5
G = "H. Task5 - ligação mínima entre clusters"
f2_case(G, "2 cidades isoladas (√2 -> 1.41)", 2, [], {1: (1, 1), 2: (2, 2)}, ["Task5"], 100, 100)
f2_case(G, "2 cidades na MESMA coordenada (distância 0.00)", 2, [], {1: (5, 5), 2: (5, 5)}, ["Task5"], 10, 10)
f2_case(G, "soma exacta vs soma de arredondados (3×√2 = 4.24, não 4.23)", 4, [], {1: (1, 1), 2: (2, 2), 3: (3, 3), 4: (4, 4)}, ["Task5"], 10, 10)
f2_case(G, "1 só cluster -> 'Task5 0.00' e nenhuma ligação", 5, [(1, 2), (2, 3), (3, 4), (4, 5)], mk_pos(5, 100, 100), ["Task5"], 100, 100)
f2_case(G, "C=1 (uma cidade)", 1, [], {1: (3, 3)}, ["Task5", "Task6 1"], 10, 10)
f2_case(G, "cidades todas numa recta (colineares)", 7, [], {i: (i * i + 3, 50) for i in range(1, 8)}, ["Task5"], 100, 100)
f2_case(G, "cidades todas na mesma vertical, ordem de ids trocada", 6, [], {1: (9, 60), 2: (9, 10), 3: (9, 40), 4: (9, 20), 5: (9, 50), 6: (9, 30)}, ["Task5"], 10, 100)
for i, (nn, cc) in enumerate([(6, 3), (10, 4), (15, 6), (25, 9), (40, 14), (60, 30), (60, 60), (50, 2)], 1):
    e, p = gen_unique(nn, cc, 10 + i)
    f2_case(G, f"aleatório MST única: {nn} cidades, {cc} clusters", nn, e, p, ["Task5"], 100000, 100000)
e, p = gen_unique(12, 7, 77, 2_000_000_000, 2_000_000_000)
f2_case(G, "coordenadas até 2·10^9 (dist² perto de 2^63)", 12, e, p, ["Task5"], 2_000_000_000, 2_000_000_000)
grid = {i: (1 + (i - 1) % 5, 1 + (i - 1) // 5) for i in range(1, 26)}
f2_case(G, "grelha 5×5 (empates por todo o lado): válido e total óptimo", 25, [], grid, ["Task5"], 5, 5)
f2_case(G, "6 cidades TODAS na mesma coordenada (empates totais)", 6, [], {i: (7, 7) for i in range(1, 7)}, ["Task5"], 10, 10)
rg = random.Random(5)
f2_case(G, "100 cidades coords 1..10 (muitos empates)", 100, [], {i: (rg.randint(1, 10), rg.randint(1, 10)) for i in range(1, 101)}, ["Task5"], 10, 10)
e, p = gen_unique(30, 10, 21)
f2_case(G, "Task5 repetida 3× (resposta tem de ser idêntica)", 30, e, p, ["Task5", "Task5", "Task5"], 100000, 100000)
f2_case(G, "Task5 NÃO pode alterar os clusters (Task1-4 depois)", 30, e, p,
        ["Task1", "Task5", "Task1", "Task2", "Task3 1", "Task4 2", "Task5", "Task2", "Task4 7"], 100000, 100000)
f2_case(G, "Task5 com CRLF no .quests", 30, e, p, ["Task5", "Task1"], 100000, 100000, raw="Task5\r\nTask1\r\n")
f2_case(G, "Task5 sem \\n final", 30, e, p, ["Task5"], 100000, 100000, raw="Task5")
f2_ambig(G, "'Task5 7' (argumento a mais)", "Task1\nTask5 7\nTask2\n")
f2_ambig(G, "linha em branco antes de Task5", "Task1\n\nTask5\nTask2\n")
f2_ambig(G, "'task5' em minúsculas", "Task1\ntask5\nTask2\n")

# ================================================================== CASOS Task6
G = "I. Task6 - rota de restauro"
f2_case(G, "2 clusters, s = extremo da ligação (lo)", 2, [], {1: (1, 1), 2: (31, 41)}, ["Task5", "Task6 1"], 100, 100)
f2_case(G, "2 clusters, s = extremo da ligação (hi)", 2, [], {1: (1, 1), 2: (31, 41)}, ["Task5", "Task6 2"], 100, 100)
f2_case(G, "2 clusters, s = cidade longe (3.ª cidade no mesmo cluster)", 3, [(1, 3)], {1: (1, 1), 2: (31, 41), 3: (90, 90)}, ["Task5", "Task6 3", "Task6 1", "Task6 2"], 100, 100)
star = {1: (500, 500), 2: (600, 500), 3: (400, 500), 4: (500, 600), 5: (500, 400)}
f2_case(G, "estrela com hub no centro, s = hub", 5, [], star, ["Task5", "Task6 1"], 1000, 1000)
f2_case(G, "estrela com hub no centro, s = folha", 5, [], star, ["Task5", "Task6 2", "Task6 5"], 1000, 1000)
f2_case(G, "estrela grande: hub + 8 folhas, todas as partidas", 9,
        [], {1: (500, 500), 2: (600, 500), 3: (400, 500), 4: (500, 600), 5: (500, 400), 6: (571, 571), 7: (429, 429), 8: (571, 429), 9: (429, 571)},
        ["Task5"] + [f"Task6 {i}" for i in range(1, 10)], 1000, 1000)
for i, (nn, cc) in enumerate([(4, 3), (6, 4), (9, 5), (12, 7), (14, 9), (16, 12), (20, 12)], 1):
    e, p = gen_unique(nn, cc, 40 + i)
    f2_case(G, f"aleatório exacto: {nn} cidades, {cc} clusters ({cc-1} ligações), 4 partidas", nn, e, p,
            ["Task5"] + [f"Task6 {random.Random(i*7+j).randint(1, nn)}" for j in range(4)], 100000, 100000)
e, p = gen_unique(24, 14, 99)
f2_case(G, "13 ligações (óptimo exacto não verificado, só validade+tempo)", 24, e, p, ["Task5", "Task6 1", "Task6 9"], 100000, 100000)
e, p = gen_unique(30, 20, 98)
f2_case(G, "19 ligações (só validade+tempo; força bruta rebenta aqui)", 30, e, p, ["Task5", "Task6 5"], 100000, 100000)
e, p = gen_unique(40, 30, 97)
f2_case(G, "29 ligações (só validade+tempo)", 40, e, p, ["Task5", "Task6 12"], 100000, 100000)
e, p = gen_unique(10, 6, 55)
f2_case(G, "Task6 ANTES da Task5 (a ordem das tarefas não pode importar)", 10, e, p, ["Task6 3", "Task5", "Task6 3"], 100000, 100000)
f2_case(G, "Task6 sem nenhuma Task5 no ficheiro", 10, e, p, ["Task6 3"], 100000, 100000)
f2_case(G, "Task6 repetida várias vezes e partidas diferentes", 10, e, p, [f"Task6 {i}" for i in (1, 1, 2, 10, 5, 5)], 100000, 100000)
f2_case(G, "Task6 NÃO pode alterar clusters/posições (Task1-4 depois)", 10, e, p,
        ["Task6 4", "Task1", "Task2", "Task3 4", "Task4 4", "Task6 4", "Task5", "Task4 9"], 100000, 100000)
f2_case(G, "cidade de partida fora do mapa: 0, -1, C+1, 21", 10, e, p, ["Task6 0", "Task6 -1", "Task6 11", "Task6 21", "Task5"], 100000, 100000)
f2_case(G, "fora do mapa com 1 só cluster (continua a ser -2)", 4, [(1, 2), (2, 3), (3, 4)], mk_pos(4, 100, 100), ["Task6 0", "Task6 5", "Task6 2"], 100, 100)
f2_case(G, "1 só cluster: Task6 válida -> 'Task6 0.00' sem passos", 4, [(1, 2), (2, 3), (3, 4)], mk_pos(4, 100, 100), ["Task6 2", "Task5"], 100, 100)
f2_case(G, "coordenadas até 2·10^9 na Task6", 10, *gen_unique(10, 6, 56, 2_000_000_000, 2_000_000_000), ["Task5", "Task6 3"], 2_000_000_000, 2_000_000_000)
f2_case(G, "grelha 5×5 isolada, Task5+Task6 (empates)", 25, [], grid, ["Task5", "Task6 1", "Task6 13", "Task6 25"], 5, 5)
f2_case(G, "6 cidades na mesma coordenada, Task6 (todas as distâncias 0)", 6, [], {i: (7, 7) for i in range(1, 7)}, ["Task5", "Task6 3"], 10, 10)
f2_case(G, "s numa posição interior de um cluster grande (não é extremo de ligação)", 12,
        [(i, i + 1) for i in range(1, 9)] + [(10, 11)], {1: (10, 10), 2: (20, 10), 3: (30, 10), 4: (40, 10), 5: (50, 10), 6: (60, 10), 7: (70, 10), 8: (80, 10), 9: (90, 10), 10: (50, 90), 11: (60, 90), 12: (95, 50)},
        ["Task5", "Task6 5", "Task6 12", "Task6 10"], 100, 100)
f2_ambig(G, "'Task6' sem argumento", "Task1\nTask6\nTask2\n")
f2_ambig(G, "'Task6 abc'", "Task1\nTask6 abc\nTask2\n")
f2_ambig(G, "'Task6 1 2' (argumento a mais)", "Task1\nTask6 1 2\nTask2\n")
f2_ambig(G, "'Task6 1.5' (decimal)", "Task1\nTask6 1.5\nTask2\n")
f2_ambig(G, "'Task6 99999999999' (> int)", "Task1\nTask6 99999999999\nTask2\n")
f2_ambig(G, "'Task6 +2'", "Task1\nTask6 +2\nTask2\n")
f2_ambig(G, "'Task6' com tab/vários espaços antes do número", "Task1\nTask6   \t 2\nTask2\n")

# ================================================================== misturas
G = "J. mistura de todas as tarefas (Task1-6)"
for sd in range(6):
    rnd = random.Random(900 + sd)
    nn = rnd.choice([8, 12, 20, 30]); cc = rnd.randint(2, min(nn, 10))
    e, p = gen_unique(nn, cc, 300 + sd)
    ql = []
    for _ in range(rnd.randint(10, 20)):
        t = rnd.choice(["Task1", "Task2", "Task3", "Task4", "Task5", "Task6", "Task5", "Task6"])
        if t in ("Task3", "Task4", "Task6"):
            t += f" {rnd.choice([rnd.randint(1, nn), rnd.randint(1, nn), 0, nn + 1, -1])}"
        ql.append(t)
    f2_case(G, f"aleatório #{sd+1}: {nn} cidades, {cc} clusters, {len(ql)} tarefas", nn, e, p, ql, 100000, 100000)
e, p = gen_unique(20, 8, 888)
f2_case(G, "200 linhas alternando Task5/Task6/Task3 (estado preservado, sem fugas)", 20, e, p,
        [("Task5", "Task6 7", "Task3 4", "Task4 9")[i % 4] for i in range(200)], 100000, 100000)

# ================================================================== desempenho
G = "K. desempenho Task5/Task6 (limite 10 s)"
def perf2(name, n, c, qlines, verify_small=False, seed=1, singletons=False):
    if SKIP_PERF:
        return
    print(f"  [desempenho] a correr: {name} ...", flush=True)
    rnd = random.Random(seed)
    if singletons:
        edges = []
        pos = {i: (rnd.randint(1, 1_000_000), rnd.randint(1, 1_000_000)) for i in range(1, n + 1)}
    else:
        edges, pos = gen_map(n, c, rnd, 1_000_000, 1_000_000)
    t0 = time.time()
    f2_case(G, name, n, edges, pos, qlines, 1_000_000, 1_000_000, perf=True, force_tie=True)
    print(f"  [desempenho]   -> {results[-1][2]} {results[-1][3][:60]}", flush=True)
perf2("Task5 | 1200 cidades isoladas (óptimo verificado)", 1200, 1200, ["Task5"], singletons=True)
perf2("Task5 | 5.000 cidades isoladas", 5000, 5000, ["Task5"], singletons=True)
perf2("Task5 | 20.000 cidades isoladas", 20000, 20000, ["Task5"], singletons=True)
perf2("Task5 | 50.000 cidades isoladas", 50000, 50000, ["Task5"], singletons=True)
perf2("Task5 | 100.000 cidades isoladas (exige MST geométrica ~O(n log n))", 100000, 100000, ["Task5"], singletons=True)
perf2("Task5 | 300.000 cidades num só cluster (não pode fazer trabalho a mais)", 300000, 1, ["Task5"])
perf2("Task5+Task6 | 100.000 cidades, 2.000 clusters", 100000, 2000, ["Task5", "Task6 1"])
perf2("Task5+Task6 | 200.000 cidades, 20.000 clusters", 200000, 20000, ["Task5", "Task6 1"])
perf2("Task6 | 30 clusters (29 ligações)", 3000, 30, ["Task5", "Task6 1"])
perf2("Task6 | 200 clusters (199 ligações)", 20000, 200, ["Task5", "Task6 1"])
perf2("Task6 | 1.000 clusters (999 ligações)", 20000, 1000, ["Task5", "Task6 1"])
perf2("Task6 x200 | 200 clusters, 200 pedidos Task6", 20000, 200, ["Task5"] + [f"Task6 {i}" for i in range(1, 201)])
perf2("Task5 x500 | 2.000 clusters, 500 pedidos Task5", 20000, 2000, ["Task5"] * 500)

# ---------------------------------------------------------------- relatório
order = []
for g, n, v, d in results:
    if g not in order: order.append(g)
bad = 0
lines = ["# Relatório de casos-limite — HealkrISTin (" + ("só fase final: Task5/Task6" if FASE2_ONLY else "fase 1 + fase final") + ")\n"]
for g in order:
    lines.append(f"\n## {g}\n\n| # | Caso | Veredicto | Detalhe |\n|---|---|---|---|")
    for i, (gg, n, v, d) in enumerate([r for r in results if r[0] == g], 1):
        flag = "✅" if v.startswith("OK") else ("ℹ️" if v.startswith("INFO") else "❌")
        if flag == "❌": bad += 1
        lines.append(f"| {i} | {n} | {flag} {v} | {d.replace('|','/')} |")
lines.append(f"\n**Total: {len(results)} casos, {bad} falhas.**")
rep = "\n".join(lines)
print(rep)
open("relatorio_fase2.md" if FASE2_ONLY else "relatorio_casos_limite.md", "w").write(rep + "\n")
