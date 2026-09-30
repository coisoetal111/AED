import os
import subprocess
import glob

# ================= CONFIGURAÇÕES =================
PASTA_TESTES = "BabyOnes"
CODIGO_C = "healkristin.c"
EXECUTAVEL = "./healkristin"
EXTENSAO_PROF = ".ProfSol" # Altera aqui se a solução do prof tiver outra extensão (ex: .sol)
# =================================================

def compilar_codigo():
    print(f"⚙️ A compilar {CODIGO_C}...")
    # Inclui o -lm obrigatorio para o <math.h> e -O3 para velocidade maxima
    resultado = subprocess.run(["gcc", "-O3", "-o", "healkristin", CODIGO_C, "-lm"])
    if resultado.returncode != 0:
        print("❌ Erro na compilação! Corrige o código C primeiro.")
        exit(1)
    print("✅ Compilação concluída com sucesso!\n")

def comparar_ficheiros(ficheiro_aluno, ficheiro_prof):
    try:
        with open(ficheiro_aluno, 'r') as f_aluno, open(ficheiro_prof, 'r') as f_prof:
            # Lê as linhas, remove espaços em branco no início/fim e ignora linhas vazias
            linhas_aluno = [linha.strip() for linha in f_aluno.readlines() if linha.strip()]
            linhas_prof = [linha.strip() for linha in f_prof.readlines() if linha.strip()]

        if linhas_aluno == linhas_prof:
            return True, None
        
        # Se falhar, procura a primeira linha diferente para ajudar no debug
        for i, (linha_a, linha_p) in enumerate(zip(linhas_aluno, linhas_prof)):
            if linha_a != linha_p:
                return False, f"Diferença na linha {i+1} (ignorando linhas vazias):\n   Teu output: {linha_a}\n   Prof output: {linha_p}"
        
        # Se um ficheiro tiver mais linhas que o outro
        return False, f"Diferença no número de linhas (Tu tens {len(linhas_aluno)}, o Prof tem {len(linhas_prof)})"
        
    except Exception as e:
        return False, f"Erro ao ler os ficheiros: {e}"

def correr_testes():
    # Encontra todos os ficheiros .quests na pasta BabyOnes
    quests = glob.glob(os.path.join(PASTA_TESTES, "*.quests"))
    
    if not quests:
        print(f"⚠️ Não foram encontrados ficheiros .quests na pasta '{PASTA_TESTES}'.")
        return

    testes_passados = 0
    total_testes = len(quests)

    for quest_file in sorted(quests):
        # Extrai o nome base (ex: BabyOnes/t01)
        base_name = quest_file.replace(".quests", "")
        map_file = f"{base_name}.map"
        pos_file = f"{base_name}.position"
        prof_file = f"{base_name}{EXTENSAO_PROF}"
        results_file = f"{base_name}.results"
        
        nome_curto = os.path.basename(base_name)
        
        if not (os.path.exists(map_file) and os.path.exists(pos_file) and os.path.exists(prof_file)):
            print(f"⏭️  [{nome_curto}] Ignorado: Faltam ficheiros base ou a solução do professor.")
            continue

        # Executa o programa C com os 3 ficheiros
        subprocess.run([EXECUTAVEL, map_file, pos_file, quest_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not os.path.exists(results_file):
            print(f"❌ [{nome_curto}] FALHOU: O ficheiro .results não foi gerado.")
            continue

        # Compara os resultados
        sucesso, erro_msg = comparar_ficheiros(results_file, prof_file)
        
        if sucesso:
            print(f"✅ [{nome_curto}] PASSOU")
            testes_passados += 1
        else:
            print(f"❌ [{nome_curto}] FALHOU")
            print(f"   -> {erro_msg}")

    print("\n" + "="*30)
    print(f"📊 RESULTADO FINAL: {testes_passados}/{total_testes} testes passados.")
    if testes_passados == total_testes:
        print("🏆 PARABÉNS! O TEU ALGORITMO ESTÁ PERFEITO!")
    print("="*30)

if __name__ == "__main__":
    compilar_codigo()
    correr_testes()