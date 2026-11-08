#include "healkristin.h"

void Task1(int cluster_counter, FILE* results){

    fprintf(results, "Task1 %d\n\n", cluster_counter);
    
    return; 
}

void Task2(int* cluster_head, int cluster_counter, int cities, int* clusters, FILE* results){

    fprintf(results, "Task2 %d", cluster_counter);
    if(cluster_counter == cities){ 
        for(int i = 1; i <= cities; i++) fprintf(results, "\nCluster: %d", i);
        fprintf(results, "\n\n");
        return;
    }
    int j = 0;
    fprintf(results, "\nCluster: ");
    int first = 1;
    for(int i = 0; i < cities; i++) if(clusters[0] == clusters[i]){ fprintf(results, first ? "%d" : " %d", i + 1); first = 0; }
    while(cluster_head[j] != 0){
        fprintf(results, "\nCluster: ");
        first = 1;
        for(int i = 0; i < cities; i++){
            if(clusters[i] == cluster_head[j]){
                fprintf(results, first ? "%d" : " %d", i + 1);
                first = 0;
            }
        }
        j++;
    }
    fprintf(results, "\n\n");

    return;
}

void Task3(FILE *quests, City *Cities, int cities, int *clusters, FILE *results, int cluster_counter){
    
    int city_ref, cluster_ref;
    long long best_distance = -1; //nao existe ainda nao foi encontrado
    int closest_city = -2; //mesmo motivo que acima mas caso tudo pertença ao mesmo cluster ja temos que é -2 como pedido
    if(fscanf(quests, " %d", &city_ref) != 1) exit(0);

    if(cluster_counter == 1 || city_ref < 1 || city_ref > cities){
    fprintf(results, "Task3 %d -2\n\n", city_ref); 
    return;
    }
    if(city_ref >= 1 && city_ref <= cities){ 
        cluster_ref = clusters[city_ref - 1];
        for(int i = 0; i < cities;i++){
            if(clusters[i] == cluster_ref) continue;
            long long dy = Cities[city_ref -1].y - Cities[i].y; 
            long long dx = Cities[city_ref -1].x - Cities[i].x;
            long long distance = (dy*dy)+(dx*dx);
            if(best_distance == -1 || distance < best_distance){ //primeira vez ou comparando
            best_distance = distance;
            closest_city = Cities[i].city_number;
            }
        }
    }
    fprintf(results, "Task3 %d %d\n\n", city_ref, closest_city);
}


void Task4(FILE* quests, City *Cities, int cities, int *clusters, FILE* results, int cluster_counter){
    int city_ref, cluster_ref, k = 0, x = 0, inside_cities[cities], outside_cities[cities];
    long long best_distance_cluster = -1;
    int closest_city_cluster = -2;
    if(fscanf(quests, " %d", &city_ref) != 1) exit(0);
    if(cluster_counter == 1 || city_ref < 1 || city_ref > cities){
    fprintf(results, "Task4 %d -2\n\n", city_ref); 
    return;
    }
    cluster_ref = clusters[city_ref -1];
    for(int i = 0; i < cities; i++){ 
        if(clusters[i] != cluster_ref) outside_cities[k++] = i;
        else  inside_cities[x++] = i;
    }
    inside_cities[x] = -3; //flag de final de array, -3 para ser distinto das outras 2
    outside_cities[k] = -3;
    for(int i = 0; inside_cities[i] != -3; i++){        
        for(int j = 0; outside_cities[j] != -3; j++){
            if(clusters[outside_cities[j]] == cluster_ref) continue;
                long long dy = Cities[inside_cities[i]].y - Cities[outside_cities[j]].y; 
                long long dx = Cities[inside_cities[i]].x - Cities[outside_cities[j]].x;
                long long distance_cluster = (dy*dy)+(dx*dx);
                if(best_distance_cluster == -1 || distance_cluster < best_distance_cluster || (distance_cluster == best_distance_cluster && Cities[outside_cities[j]].city_number < closest_city_cluster)){
                    best_distance_cluster = distance_cluster;
                    closest_city_cluster = Cities[outside_cities[j]].city_number;
                }
        }
    
    }
    fprintf(results, "Task4 %d %d\n\n", city_ref, closest_city_cluster);
}

long long dist2(City *a, City *b, int *cluster) {
  if (cluster[a->city_number - 1] == cluster[b->city_number - 1]) return 0;
  long long dx = a->x - b->x;
  long long dy = a->y - b->y;
  return dx*dx + dy*dy;
}

// Ordena ligações por City_in e, em caso de empate, por City_out.
int cmpConnect(const void *x, const void *y) {
  Connect *l = (Connect *)x;
  Connect *r = (Connect *)y;
  if (l->City_in != r->City_in) return l->City_in - r->City_in;
  return l->City_out - r->City_out;
}

// Prim sobre as cidades: p[i] = pai de i, w[i] = distância² ao pai.
void prim(City *Cities, int cities, int *cluster, int p[], long long w[]) {
  char *naArvore = calloc(cities, 1);
  if (naArvore == NULL) exit(1);

  for (int i = 0; i < cities; i++) {
    w[i] = LLONG_MAX;
    p[i] = -1;
  }
  w[0] = 0;

  for (int k = 0; k < cities; k++) {
    // escolher a cidade fora da árvore com menor w
    int v = -1;
    for (int i = 0; i < cities; i++)
      if (!naArvore[i] && (v == -1 || w[i] < w[v])) v = i;

    naArvore[v] = 1;

    // atualizar as restantes com a distância a v
    for (int i = 0; i < cities; i++) {
      if (!naArvore[i]) {
        long long d = dist2(&Cities[v], &Cities[i], cluster);
        if (d < w[i]) {
          w[i] = d;
          p[i] = v;
        }
      }
    }
  }
  free(naArvore);
}

// Task5: comprimento mínimo de cabo para ficar com um só cluster.
void Task5(City *Cities, int cities, int *cluster, FILE *results) {
  int *p = malloc(cities * sizeof(int));
  long long *w = malloc(cities * sizeof(long long));
  Connect *ligs = malloc(cities * sizeof(Connect));
  if (p == NULL || w == NULL || ligs == NULL) exit(1);

  prim(Cities, cities, cluster, p, w);

  // guardar só as ligações que unem clusters diferentes
  int m = 0;
  double total = 0;
  for (int i = 0; i < cities; i++) {
    if (p[i] != -1 && cluster[i] != cluster[p[i]]) {
      int u = i + 1, v = p[i] + 1;
      ligs[m].City_in  = u < v ? u : v;
      ligs[m].City_out = u < v ? v : u;
      ligs[m].distance = sqrt((double)w[i]);
      total += ligs[m].distance;
      m++;
    }
  }
  qsort(ligs, m, sizeof(Connect), cmpConnect);

  fprintf(results, "Task5 %.2f\n", total);
  for (int j = 0; j < m; j++) fprintf(results, "%d %d %.2f\n", ligs[j].City_in, ligs[j].City_out, ligs[j].distance);
  fprintf(results, "\n");
  free(p);
  free(w);
  free(ligs);
}
