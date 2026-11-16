#include "healkristin.h"




void FileMan(int argc, char **argv, FILE **map, FILE **quests, FILE **position, char *filenameResult){
    //verificação do numero de argumentos corretos
    if(argc!=4) exit(0);
    //verificação do tipo de ficheiros corretos
    int j = strlen(argv[1]);
    if( j < 8) exit(0);
    char *temp_;
    temp_ = &argv[1][j-7];
    if (strcmp(temp_, ".quests") == 0){
        *quests = fopen(argv[1], "r");
        argv[1][j - 7] = '\0';
        sprintf(filenameResult, "%s.results", argv[1]);
        argv[1][j - 7] = '.';     
        }
        else exit(0);
    j = strlen(argv[2]);
    if( j < 5) exit(0);
            temp_ = &argv[2][j-4];
            if (strcmp(temp_, ".map") == 0) *map = fopen(argv[2], "r");
            else exit(0);
    j = strlen(argv[3]);
    if( j < 10) exit(0);  
        temp_ = &argv[3][j-9];
        if( strcmp(temp_, ".position") == 0) *position = fopen(argv[3], "r");
        else exit(0);    
   
}


void SortedCityMan(SortedCity *SortedCities, int cities, int* clusters){
    for(int i = 0; i < cities; i++){
        SortedCities[i].city_number = i + 1;
        SortedCities[i].cluster_root = clusters[i];
    }
  
    int first = 0, last, i;
    qsort(SortedCities, cities, sizeof(SortedCity), cmpSorted);
    for(i = 0; i < cities; i++){
        if(i == 0) first = i;
        if(SortedCities[i].cluster_root != SortedCities[first].cluster_root){
            last = i - 1;
            for(int j = first; j <= last; j++){
                SortedCities[j].cluster_root = SortedCities[first].city_number;
            }
            first = i;
          }
    }
        
    last = cities - 1;
    for(int j = first; j <= last; j++){
      SortedCities[j].cluster_root = SortedCities[first].city_number;
    }
    qsort(SortedCities, cities, sizeof(SortedCity), cmpSorted);
    return;
}



void CityMan(FILE* map, City *Cities, int cities, int X_max, int Y_max){
    int num, x, y;
    for(int i = 0; i < cities; i++){
        if(fscanf(map, "%d %d %d", &num, &x, &y) != 3) exit(0);
        if(num < 1 || num > cities || x <= 0 || y <= 0 || x > X_max || y > Y_max) exit(0);
        Cities[i].city_number = num;
        Cities[i].x = x;
        Cities[i].y = y;
    }
    
    return;
}

int ClusterMan(int cities, SortedCity *SortedCities, int operations){

if(operations == 0) return cities;

 int cluster_counter = 1, a = 0;
 for(int i = 1; i < cities; i++){
    if(SortedCities[i].cluster_root != SortedCities[a].cluster_root){
       cluster_counter++;
       a = i;
    }
 }
    
    
 return cluster_counter;
}



void QuestsMan(FILE* results, FILE* quests, SortedCity *SortedCities, int cluster_counter, int cities, int* clusters, City *Cities){
    int quest = 0;
    int h;
    while ((fscanf(quests, " Task%d", &quest) == 1)){
        switch (quest){
            case 1:
                Task1(cluster_counter, results);
                break;
            case 2:
                 Task2(SortedCities, cluster_counter, cities, results);
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


int cmpSorted(const void *x, const void *y) {
    SortedCity *c1 = (SortedCity *)x;
    SortedCity *c2 = (SortedCity *)y;
    
    if (c1->cluster_root == c2->cluster_root) {
        return (c1->city_number - c2->city_number);
    }
    
    return (c1->cluster_root - c2->cluster_root);
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