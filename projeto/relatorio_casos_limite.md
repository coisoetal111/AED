# Relatório de casos-limite — HealkrISTin (fase 1 + fase final)


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
| 13 | L=0 com cabeçalho só | ✅ OK | 0.01s |
| 14 | L maior que nº de linhas reais | ✅ OK | 0.00s |
| 15 | L menor que nº de linhas reais (linhas extra) | ✅ OK | 0.01s |

## B. formato do .quests

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | fim de linha CRLF (Windows) | ✅ OK | 0.00s |
| 2 | sem \n no fim do ficheiro | ✅ OK | 0.00s |
| 3 | linha em branco no meio | ✅ OK | 0.00s |
| 4 | linha em branco no fim | ✅ OK | 0.00s |
| 5 | espaços no fim das linhas | ✅ OK | 0.00s |
| 6 | espaços/tab antes do número | ✅ OK | 0.00s |
| 7 | espaços no início da linha | ✅ OK | 0.00s |
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
| 6 | id duplicado (falta cidade 3) | ✅ OK | sem .results (correcto) |
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
| 15 | extensões trocadas (.map .quests .position) | ✅ OK | sem output |
| 16 | sem extensão | ✅ OK | sem output |
| 17 | duas .quests e nenhum .map | ✅ OK | sem output |
| 18 | extensão com maiúsculas (.QUESTS) | ✅ OK | sem output |
| 19 | string vazia como argumento | ✅ OK | sem output |
| 20 | argumento só '.quests' sem nome | ❌ FALHA | criou ficheiros: ['.results'] (devia não produzir output) |

## G. desempenho (limite 10 s)

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | Task1 | 200k cidades sem ligações | ✅ OK | 0.05s |
| 2 | Task2 | 50k cidades, todas isoladas | ✅ OK | 0.02s |
| 3 | Task2 | 100k cidades, todas isoladas | ✅ OK | 0.03s |
| 4 | Task2 | 100k cidades, ~metade ligadas (muitos clusters) | ✅ OK | 2.95s |
| 5 | Task1+Task2 | 300k cidades, 1 cluster (cadeia) | ✅ OK | 0.12s |
| 6 | Task3 x1000 | 100k cidades | ✅ OK | 0.88s |
| 7 | Task4 x20 | 100k cidades, clusters pequenos | ✅ OK | 1.05s |
| 8 | Task4 x1000 | 20k cidades | ✅ OK | 1.20s |
| 9 | Task4 x1 | 2 clusters grandes (50k+50k) | ✅ OK | 4.46s |
| 10 | Task4 x1 | cluster gigante + 1 cidade fora (n=300k) | ✅ OK | 0.11s |
| 11 | Task4 x100 | cluster gigante + 1 cidade fora (n=300k) | ✅ OK | 0.22s |
| 12 | mapa grande: 500k cidades, 2M ligações, Task1 | ✅ OK | 0.51s |

## H. Task5 - ligação mínima entre clusters

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | 2 cidades isoladas (√2 -> 1.41) | ✅ OK | 0.01s |
| 2 | 2 cidades na MESMA coordenada (distância 0.00) | ✅ OK | 0.00s |
| 3 | soma exacta vs soma de arredondados (3×√2 = 4.24, não 4.23) | ✅ OK | 0.00s |
| 4 | 1 só cluster -> 'Task5 0.00' e nenhuma ligação | ✅ OK | 0.00s |
| 5 | C=1 (uma cidade) | ❌ FALHA | 0.01s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 0.00']) |
| 6 | cidades todas numa recta (colineares) | ✅ OK | 0.00s |
| 7 | cidades todas na mesma vertical, ordem de ids trocada | ✅ OK | 0.00s |
| 8 | aleatório MST única: 6 cidades, 3 clusters | ✅ OK | 0.00s |
| 9 | aleatório MST única: 10 cidades, 4 clusters | ✅ OK | 0.00s |
| 10 | aleatório MST única: 15 cidades, 6 clusters | ✅ OK | 0.00s |
| 11 | aleatório MST única: 25 cidades, 9 clusters | ✅ OK | 0.01s |
| 12 | aleatório MST única: 40 cidades, 14 clusters | ✅ OK | 0.00s |
| 13 | aleatório MST única: 60 cidades, 30 clusters | ✅ OK | 0.00s |
| 14 | aleatório MST única: 60 cidades, 60 clusters | ✅ OK | 0.01s |
| 15 | aleatório MST única: 50 cidades, 2 clusters | ✅ OK | 0.00s |
| 16 | coordenadas até 2·10^9 (dist² perto de 2^63) | ✅ OK | 0.00s |
| 17 | grelha 5×5 (empates por todo o lado): válido e total óptimo | ✅ OK | 0.00s |
| 18 | 6 cidades TODAS na mesma coordenada (empates totais) | ✅ OK | 0.00s |
| 19 | 100 cidades coords 1..10 (muitos empates) | ℹ️ INFO | 0.00s linha 1: empate: MST alternativa válida (total óptimo, ligações diferentes da canónica) |
| 20 | Task5 repetida 3× (resposta tem de ser idêntica) | ✅ OK | 0.00s |
| 21 | Task5 NÃO pode alterar os clusters (Task1-4 depois) | ✅ OK | 0.00s |
| 22 | Task5 com CRLF no .quests | ✅ OK | 0.00s |
| 23 | Task5 sem \n final | ✅ OK | 0.00s |
| 24 | 'Task5 7' (argumento a mais) | ℹ️ INFO: continua | 'Task1 5\n\nTask5 1002.47\n1 3 357.47\n1 6 176.56\n2 4 357.25\n4 5 111.20\n\nTask2 5\nCluster: 1 2\nCluster: 3\n' |
| 25 | linha em branco antes de Task5 | ℹ️ INFO: continua | 'Task1 5\n\nTask5 1002.47\n1 3 357.47\n1 6 176.56\n2 4 357.25\n4 5 111.20\n\nTask2 5\nCluster: 1 2\nCluster: 3\n' |
| 26 | 'task5' em minúsculas | ❌ FALHA | deixou de processar as linhas seguintes / 'Task1 5\n\n' |

## I. Task6 - rota de restauro

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | 2 clusters, s = extremo da ligação (lo) | ❌ FALHA | 0.00s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 50.00']) |
| 2 | 2 clusters, s = extremo da ligação (hi) | ❌ FALHA | 0.00s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 50.00']) |
| 3 | 2 clusters, s = cidade longe (3.ª cidade no mesmo cluster) | ❌ FALHA | 0.00s 4 tarefas mas 1 blocos de resposta (blocos: ['Task5 50.00']) |
| 4 | estrela com hub no centro, s = hub | ❌ FALHA | 0.00s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 400.00']) |
| 5 | estrela com hub no centro, s = folha | ❌ FALHA | 0.00s 3 tarefas mas 1 blocos de resposta (blocos: ['Task5 400.00']) |
| 6 | estrela grande: hub + 8 folhas, todas as partidas | ❌ FALHA | 0.00s 10 tarefas mas 1 blocos de resposta (blocos: ['Task5 636.86']) |
| 7 | aleatório exacto: 4 cidades, 3 clusters (2 ligações), 4 partidas | ❌ FALHA | 0.00s 5 tarefas mas 1 blocos de resposta (blocos: ['Task5 33014.40']) |
| 8 | aleatório exacto: 6 cidades, 4 clusters (3 ligações), 4 partidas | ❌ FALHA | 0.00s 5 tarefas mas 1 blocos de resposta (blocos: ['Task5 53677.42']) |
| 9 | aleatório exacto: 9 cidades, 5 clusters (4 ligações), 4 partidas | ❌ FALHA | 0.00s 5 tarefas mas 1 blocos de resposta (blocos: ['Task5 76518.18']) |
| 10 | aleatório exacto: 12 cidades, 7 clusters (6 ligações), 4 partidas | ❌ FALHA | 0.00s 5 tarefas mas 1 blocos de resposta (blocos: ['Task5 58595.21']) |
| 11 | aleatório exacto: 14 cidades, 9 clusters (8 ligações), 4 partidas | ❌ FALHA | 0.00s 5 tarefas mas 1 blocos de resposta (blocos: ['Task5 104990.77']) |
| 12 | aleatório exacto: 16 cidades, 12 clusters (11 ligações), 4 partidas | ❌ FALHA | 0.01s 5 tarefas mas 1 blocos de resposta (blocos: ['Task5 185703.47']) |
| 13 | aleatório exacto: 20 cidades, 12 clusters (11 ligações), 4 partidas | ❌ FALHA | 0.01s 5 tarefas mas 1 blocos de resposta (blocos: ['Task5 112032.84']) |
| 14 | 13 ligações (óptimo exacto não verificado, só validade+tempo) | ❌ FALHA | 0.01s 3 tarefas mas 1 blocos de resposta (blocos: ['Task5 152058.88']) |
| 15 | 19 ligações (só validade+tempo; força bruta rebenta aqui) | ❌ FALHA | 0.00s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 196698.54']) |
| 16 | 29 ligações (só validade+tempo) | ❌ FALHA | 0.01s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 306000.67']) |
| 17 | Task6 ANTES da Task5 (a ordem das tarefas não pode importar) | ❌ FALHA | 0.00s 3 tarefas mas 1 blocos de resposta (blocos: ['Task5 62744.17']) |
| 18 | Task6 sem nenhuma Task5 no ficheiro | ❌ FALHA | 0.00s .results vazio: o programa não escreveu nada (Task5/Task6 ainda não implementadas?) |
| 19 | Task6 repetida várias vezes e partidas diferentes | ❌ FALHA | 0.01s .results vazio: o programa não escreveu nada (Task5/Task6 ainda não implementadas?) |
| 20 | Task6 NÃO pode alterar clusters/posições (Task1-4 depois) | ❌ FALHA | 0.00s 8 tarefas mas 6 blocos de resposta (blocos: ['Task1 6', 'Task2 6', 'Task3 4 9', 'Task4 4 9', 'Task5 62744.17', 'Task4 9 4']) |
| 21 | cidade de partida fora do mapa: 0, -1, C+1, 21 | ❌ FALHA | 0.00s 5 tarefas mas 1 blocos de resposta (blocos: ['Task5 62744.17']) |
| 22 | fora do mapa com 1 só cluster (continua a ser -2) | ❌ FALHA | 0.00s .results vazio: o programa não escreveu nada (Task5/Task6 ainda não implementadas?) |
| 23 | 1 só cluster: Task6 válida -> 'Task6 0.00' sem passos | ❌ FALHA | 0.00s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 0.00']) |
| 24 | coordenadas até 2·10^9 na Task6 | ❌ FALHA | 0.00s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 2065224302.16']) |
| 25 | grelha 5×5 isolada, Task5+Task6 (empates) | ❌ FALHA | 0.00s 4 tarefas mas 1 blocos de resposta (blocos: ['Task5 24.00']) |
| 26 | 6 cidades na mesma coordenada, Task6 (todas as distâncias 0) | ❌ FALHA | 0.00s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 0.00']) |
| 27 | s numa posição interior de um cluster grande (não é extremo de ligação) | ❌ FALHA | 0.01s 4 tarefas mas 1 blocos de resposta (blocos: ['Task5 93.46']) |
| 28 | 'Task6' sem argumento | ℹ️ INFO: continua | 'Task1 5\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluster: 6\n\n' |
| 29 | 'Task6 abc' | ℹ️ INFO: continua | 'Task1 5\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluster: 6\n\n' |
| 30 | 'Task6 1 2' (argumento a mais) | ℹ️ INFO: continua | 'Task1 5\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluster: 6\n\n' |
| 31 | 'Task6 1.5' (decimal) | ℹ️ INFO: continua | 'Task1 5\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluster: 6\n\n' |
| 32 | 'Task6 99999999999' (> int) | ℹ️ INFO: continua | 'Task1 5\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluster: 6\n\n' |
| 33 | 'Task6 +2' | ℹ️ INFO: continua | 'Task1 5\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluster: 6\n\n' |
| 34 | 'Task6' com tab/vários espaços antes do número | ℹ️ INFO: continua | 'Task1 5\n\nTask2 5\nCluster: 1 2\nCluster: 3\nCluster: 4\nCluster: 5\nCluster: 6\n\n' |

## J. mistura de todas as tarefas (Task1-6)

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | aleatório #1: 12 cidades, 7 clusters, 11 tarefas | ❌ FALHA | 0.00s 11 tarefas mas 9 blocos de resposta (blocos: ['Task2 7', 'Task4 12 2', 'Task3 -1 -2', 'Task5 76188.07', 'Task5 76188.07', 'Task5 76188.07']) |
| 2 | aleatório #2: 30 cidades, 6 clusters, 11 tarefas | ❌ FALHA | 0.00s 11 tarefas mas 9 blocos de resposta (blocos: ['Task3 31 -2', 'Task5 29557.92', 'Task5 29557.92', 'Task5 29557.92', 'Task2 6', 'Task2 6']) |
| 3 | aleatório #3: 20 cidades, 8 clusters, 17 tarefas | ❌ FALHA | 0.00s 17 tarefas mas 12 blocos de resposta (blocos: ['Task2 8', 'Task3 19 3', 'Task3 0 -2', 'Task3 21 -2', 'Task5 94388.64', 'Task3 21 -2']) |
| 4 | aleatório #4: 8 cidades, 7 clusters, 20 tarefas | ❌ FALHA | 0.00s 20 tarefas mas 16 blocos de resposta (blocos: ['Task2 7', 'Task5 150087.22', 'Task5 150087.22', 'Task5 150087.22', 'Task2 7', 'Task4 0 -2']) |
| 5 | aleatório #5: 20 cidades, 10 clusters, 16 tarefas | ❌ FALHA | 0.00s 16 tarefas mas 13 blocos de resposta (blocos: ['Task1 10', 'Task5 108676.19', 'Task2 10', 'Task5 108676.19', 'Task1 10', 'Task5 108676.19']) |
| 6 | aleatório #6: 20 cidades, 7 clusters, 18 tarefas | ❌ FALHA | 0.00s 18 tarefas mas 14 blocos de resposta (blocos: ['Task5 69829.74', 'Task3 -1 -2', 'Task5 69829.74', 'Task2 7', 'Task2 7', 'Task1 7']) |
| 7 | 200 linhas alternando Task5/Task6/Task3 (estado preservado, sem fugas) | ❌ FALHA | 0.00s 200 tarefas mas 150 blocos de resposta (blocos: ['Task5 52542.03', 'Task3 4 12', 'Task4 9 1', 'Task5 52542.03', 'Task3 4 12', 'Task4 9 1']) |

## K. desempenho Task5/Task6 (limite 10 s)

| # | Caso | Veredicto | Detalhe |
|---|---|---|---|
| 1 | Task5 | 1200 cidades isoladas (óptimo verificado) | ✅ OK | 0.01s |
| 2 | Task5 | 5.000 cidades isoladas | ℹ️ INFO | 0.16s linha 1: válido (árvore, ordem, formato), mas óptimo NÃO verificado (n grande) |
| 3 | Task5 | 20.000 cidades isoladas | ℹ️ INFO | 3.33s linha 1: válido (árvore, ordem, formato), mas óptimo NÃO verificado (n grande) |
| 4 | Task5 | 50.000 cidades isoladas | ❌ LENTO (>10 s) | cortado aos 15 s |
| 5 | Task5 | 100.000 cidades isoladas (exige MST geométrica ~O(n log n)) | ❌ LENTO (>10 s) | cortado aos 15 s |
| 6 | Task5 | 300.000 cidades num só cluster (não pode fazer trabalho a mais) | ❌ LENTO (>10 s) | cortado aos 15 s |
| 7 | Task5+Task6 | 100.000 cidades, 2.000 clusters | ❌ LENTO (>10 s) | cortado aos 15 s |
| 8 | Task5+Task6 | 200.000 cidades, 20.000 clusters | ❌ LENTO (>10 s) | cortado aos 15 s |
| 9 | Task6 | 30 clusters (29 ligações) | ❌ FALHA | não criou o ficheiro .results |
| 10 | Task6 | 200 clusters (199 ligações) | ❌ FALHA | 3.37s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 87803.03']) |
| 11 | Task6 | 1.000 clusters (999 ligações) | ❌ FALHA | 3.38s 2 tarefas mas 1 blocos de resposta (blocos: ['Task5 912191.39']) |
| 12 | Task6 x200 | 200 clusters, 200 pedidos Task6 | ❌ FALHA | 3.35s 201 tarefas mas 1 blocos de resposta (blocos: ['Task5 87803.03']) |
| 13 | Task5 x500 | 2.000 clusters, 500 pedidos Task5 | ❌ LENTO (>10 s) | cortado aos 15 s |

**Total: 165 casos, 47 falhas.**
