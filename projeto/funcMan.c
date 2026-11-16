#include "healkristin.h"



int ClusterMan(int* clusters, int cities, int* cluster_head, int operations){
if(operations == 0){
    for (int i = 0; i < cities; i++) cluster_head[i] = i + 1; 
    return cities;
}
for (int i = 0; i < cities; i++) cluster_head[i] = 0;

 int temp_ = 0;
 int found = 0;
 int cluster_counter = 1;
 for(int i = 1; i < cities; i++) if(clusters[i] != clusters[0]){ 
    
    if(temp_ == 0){
         cluster_counter++;
         temp_ ++;
         cluster_head[0] = clusters[i];
    }else{
        for(int j = 0; j < temp_; j++){
            found = 0;
            if(cluster_head[j] == clusters[i]){
                found = 1;
                break;
            }
        }
        if(found == 0){
            cluster_head[temp_] = clusters[i];
            temp_ ++;
            cluster_counter++;         
        }
    }
}
 return cluster_counter;
}



void QuestsMan(FILE* results, FILE* quests, int* cluster_head, int cluster_counter, int cities, int* clusters, City *Cities){
    int quest = 0;
    int h;
    while ((fscanf(quests, " Task%d", &quest) == 1)){
        switch (quest){
            case 1:
                Task1(cluster_counter, results);
                break;
            case 2:
                 Task2(cluster_head, cluster_counter, cities, clusters, results);
                 break;
            case 3:
                Task3(quests, Cities, cities, clusters, results, cluster_counter);
                break;
            case 4:
                Task4(quests, Cities, cities, clusters, results, cluster_counter);
                break;
            case 5:
                Task5(Cities, cities, clusters, results);
        }
         while((h = fgetc(quests)) != '\n' && h != EOF);
    }
    return;
}


void WCQU(int operations, FILE* map, int* clusters, int cities){
    
    if(operations == 0){
         for (int i = 0; i < cities; i++) clusters[i] = i + 1; 
        return;
    }

   int i, j, p, q, t, x, k = 0;
   int *size = (int *) malloc(cities * sizeof(int));
   if (size == NULL) exit(0);
  
   for (i = 0; i < cities; i++) {
      clusters[i] = i + 1;
      size[i] = 1;
   }
   
   while (k < operations && fscanf(map, " %d %d", &p, &q) == 2) {
      k++;
      if(p < 1 || p > cities || q < 1 || q > cities) exit(0);
      for (i = p; i != clusters[i - 1]; i = clusters[i - 1]); 
      for (j = q; j != clusters[j - 1]; j = clusters[j - 1]);
      if (i == j) {
         continue;
      }
      if (size[i -1] < size[j - 1]) {
         clusters[i - 1] = j;
         size[j - 1] += size[i - 1];
         t = j;
      }
      else {
         clusters[j - 1] = i;
         size[i - 1] += size[j - 1];
         t = i;
      }
      
      for (i = p; i != clusters[i - 1]; i = x) {
         x = clusters[i - 1];
         clusters[i - 1] = t;
      }
      for (j = q; j != clusters[j - 1]; j = x) {   
         x = clusters[j - 1];
         clusters[j - 1] = t;
      }
}

 for(int k = 1; k <= cities; k++){
         int root = k;
         while(root != clusters[root - 1]) root = clusters[root - 1];
         clusters[k - 1] = root;
      }
 free(size);
 return;
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