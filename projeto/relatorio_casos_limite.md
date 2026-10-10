# Relatório de casos-limite — HealkrISTin (fase 1)


## A. dados válidos / limites

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | 1 cidade, sem ligações, Task1-4 | ✅ OK | 0.01s |
| 2 | tudo ligado -> Task3/4 dão -2 | ✅ OK | 0.00s |
| 3 | nenhuma ligação (todos isolados) | ✅ OK | 0.00s |
| 4 | cidade 0 / negativa / C+1 (fora do mapa) | ✅ OK | 0.00s |
| 5 | ligações duplicadas, invertidas e auto-laços | ✅ OK | 0.00s |
| 6 | mesmo Task3 repetido para cidades diferentes | ✅ OK | 0.00s |
| 7 | empate de distância -> menor número de cidade (Task3) | ✅ OK | 0.00s |
| 8 | empate de distância em Task4 | ✅ OK | 0.00s |
| 9 | Task4 != Task3 (exemplo do enunciado) | ✅ OK | 0.00s |
| 10 | coordenadas 60000 (overflow int nas distâncias) | ✅ OK | 0.00s |
| 11 | coordenadas até 2e9 (long long necessário) | ✅ OK | 0.00s |
| 12 | ficheiro .quests vazio | ✅ OK | 0.00s |
| 13 | L=0 com cabeçalho só | ✅ OK | 0.00s |
| 14 | L maior que nº de linhas reais | ✅ OK | 0.00s |
| 15 | L menor que nº de linhas reais (linhas extra) | ✅ OK | 0.00s |

## B. formato do .quests

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | fim de linha CRLF (Windows) | ✅ OK | 0.00s |
| 2 | sem \n no fim do ficheiro | ✅ OK | 0.00s |
| 3 | linha em branco no meio | ❌ FALHA | esperado 'Task1 5\n\nTask3 1 5\n\n' / obtido 'Task1 5\n\n' |
| 4 | linha em branco no fim | ✅ OK | 0.00s |
| 5 | espaços no fim das linhas | ✅ OK | 0.00s |
| 6 | espaços/tab antes do número | ✅ OK | 0.00s |
| 7 | espaços no início da linha | ❌ FALHA | esperado 'Task1 5\n\nTask3 1 5\n\n' / obtido '(ficheiro vazio)' |
| 8 | Task3 sem argumento | ℹ️ INFO: pára de processar | 'Task1 5\n\n' |
| 9 | Task3 com argumento não numérico | ℹ️ INFO: pára de processar | 'Task1 5\n\n' |
| 10 | Task desconhecida (Task9) | ✅ OK (continua) | 'Task1 5\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluster: 6\n\n' |
| 11 | linha de lixo | ℹ️ INFO: pára de processar | 'Task1 5\n\n' |
| 12 | Task3 com número gigante (>int) | ✅ OK (continua) | 'Task1 5\n\nTask3 1215752191 -2\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluste' |
| 13 | Task3 com 2 argumentos | ✅ OK (continua) | 'Task1 5\n\nTask3 1 5\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluster: 6\n\n' |
| 14 | Task1 com argumento extra | ✅ OK (continua) | 'Task1 5\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluster: 6\n\n' |

## C. validação do .map (ids fora de {1..C})

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | ligação com cidade 0 | ✅ OK (sem crash) | 'NONE' |
| 2 | ligação com cidade C+1 | ✅ OK (sem crash) | 'NONE' |
| 3 | ligação com id negativo | ✅ OK (sem crash) | 'NONE' |
| 4 | ligação com id enorme | ✅ OK (sem crash) | 'NONE' |

## D. validação do .position (deve terminar SEM output)

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | coordenada X > Xmax | ✅ OK | sem .results (correcto) |
| 2 | coordenada Y > Ymax | ✅ OK | sem .results (correcto) |
| 3 | coordenada 0 | ✅ OK | sem .results (correcto) |
| 4 | coordenada negativa | ✅ OK | sem .results (correcto) |
| 5 | falta uma cidade (menos linhas) | ✅ OK | sem .results (correcto) |
| 6 | id duplicado (falta cidade 3) | ❌ FALHA | .results criado (53 bytes) mas devia não haver output |
| 7 | id fora de {1..C} (4) | ✅ OK | sem .results (correcto) |
| 8 | id 0 | ✅ OK | sem .results (correcto) |
| 9 | valor não numérico | ✅ OK | sem .results (correcto) |
| 10 | linha incompleta | ✅ OK | sem .results (correcto) |
| 11 | ficheiro vazio | ✅ OK | sem .results (correcto) |
| 12 | Xmax=0 | ✅ OK | sem .results (correcto) |
| 13 | só cabeçalho | ✅ OK | sem .results (correcto) |
| 14 | coordenada decimal (1.5) | ✅ OK | sem .results (correcto) |

## E. validação do .map (cabeçalho)

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | C=0 | ✅ OK | sem .results (correcto) |
| 2 | C negativo | ✅ OK | sem .results (correcto) |
| 3 | L negativo | ✅ OK | sem .results (correcto) |
| 4 | ficheiro vazio | ✅ OK | sem .results (correcto) |
| 5 | só um número | ✅ OK | sem .results (correcto) |
| 6 | cabeçalho não numérico | ✅ OK | sem .results (correcto) |

## F. invocação / nomes de ficheiros

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | nome com vários pontos (a.b.quests) | ✅ OK | 0.00s |
| 2 | caminho relativo ./x.quests ./x.map ./x.position | ✅ OK | 0.00s |
| 3 | caminho com directório com ponto (dir.v1/t.quests) | ✅ OK | 0.00s |
| 4 | nome só números (013.quests) | ✅ OK | 0.00s |
| 5 | nome com espaço (a b.quests) | ✅ OK | 0.00s |
| 6 | nome com 200 caracteres | ✅ OK | 0.00s |
| 7 | mesmo nome base nos 3 (x.quests x.map x.position) | ✅ OK | 0.00s |
| 8 | 0 argumentos | ✅ OK | sem output |
| 9 | 2 argumentos | ✅ OK | sem output |
| 10 | 4 argumentos | ✅ OK | sem output |
| 11 | ficheiro .quests não existe | ✅ OK | sem output |
| 12 | ficheiro .map não existe | ✅ OK | sem output |
| 13 | ficheiro .position não existe | ✅ OK | sem output |
| 14 | extensão errada (.txt) | ✅ OK | sem output |
| 15 | extensões trocadas (.map .quests .position) | ❌ FALHA | criou ficheiros: ['t.results'] (devia não produzir output) |
| 16 | sem extensão | ✅ OK | sem output |
| 17 | duas .quests e nenhum .map | ✅ OK | sem output |
| 18 | extensão com maiúsculas (.QUESTS) | ✅ OK | sem output |
| 19 | string vazia como argumento | ✅ OK | sem output |
| 20 | argumento só '.quests' sem nome | ✅ OK | sem output |

## G. desempenho (limite 10 s)

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | Task1 | 200k cidades sem ligações | ✅ OK | 8.68s |
| 2 | Task2 | 50k cidades, todas isoladas | ✅ OK | 1.70s |
| 3 | Task2 | 100k cidades, todas isoladas | ✅ OK | 6.84s |
| 4 | Task2 | 100k cidades, ~metade ligadas (muitos clusters) | ✅ OK | 3.06s |
| 5 | Task1+Task2 | 300k cidades, 1 cluster (cadeia) | ✅ OK | 0.12s |
| 6 | Task3 x1000 | 100k cidades | ✅ OK | 0.90s |
| 7 | Task4 x20 | 100k cidades, clusters pequenos | ✅ OK | 1.03s |
| 8 | Task4 x1000 | 20k cidades | ✅ OK | 1.00s |
| 9 | Task4 x1 | 2 clusters grandes (50k+50k) | ✅ OK | 4.56s |
| 10 | Task4 x1 | cluster gigante + 1 cidade fora (n=300k) | ❌ LENTO (>10 s) | cortado aos 15 s |
| 11 | Task4 x100 | cluster gigante + 1 cidade fora (n=300k) | ❌ LENTO (>10 s) | cortado aos 15 s |
| 12 | mapa grande: 500k cidades, 2M ligações, Task1 | ✅ OK | 0.48s |

**Total: 85 casos, 6 falhas.**
