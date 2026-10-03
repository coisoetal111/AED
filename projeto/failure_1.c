#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

typedef struct {
    int x;
    int y;
    int city_number;
    int cluster_root;
} City;


int ClusterMan(int* clusters, int cities, City *Cities);
void QuestsMan(FILE* results, FILE* quests,int cluster_counter, int cities, int* clusters, City *Cities);
void CityMan(City *Cities, int cities, int* clusters, FILE* position);
int SortAssist(const void *i, const void *j);
void WCQU(int operations, FILE* map, int* clusters, int cities);
void Task1(int cluster_counter, FILE* results);
void Task2(City *Citties, int cluster_counter, int cities, int* clusters, FILE* results);
void Task3(FILE* quests, City *Cities, int cities, int* clusters, FILE* results);
void Task4(FILE* quests, City *Cities, int cities, int* clusters, FILE* results);



int main(int argc, char **argv){

    FILE *map = NULL;
    FILE *quests = NULL;
    FILE *position = NULL;
    FILE *results = NULL;
    char result[1024];
    int cities = 0;

    //verificação do numero de argumentos corretos

    if(argc!=4) exit(EXIT_FAILURE);
    char *arg[3];
    for (int i = 1; i < argc; i++) {
        arg[i -1] =  argv[i];
    }


    //verificação do tipo de ficheiros corretos

    for (int i = 0; i < 3; i++){
        int j = strlen(arg[i]);
        char temp;
        char *temp_;
        for (int h = 0; h < j; h++){
            temp = arg[i][j - h];
            if(temp == '.'){  
                temp_ = &arg[i][j-h];
                if (strcmp(temp_, ".quests") == 0){
                    quests = fopen(arg[i], "r");
                    arg[i][j - h] = '\0';
                    sprintf(result, "%s.results", arg[i]);
                    arg[i][j - h] = '.';
                    results = fopen(result,"w");
                }
                else if (strcmp(temp_, ".map") == 0) map = fopen(arg[i], "r");
                else if( strcmp(temp_, ".position") == 0) position = fopen(arg[i], "r");
                else exit(EXIT_FAILURE);
                continue;
            }
        }
    }
    if(map == NULL || position == NULL || quests == NULL || results == NULL) exit(EXIT_FAILURE);

    //contagem do número de cidades

    int operations;
    if(fscanf(map, "%d %d", &cities, &operations) != 2) exit(EXIT_FAILURE);
    if(cities <= 0 || operations < 0) exit(EXIT_FAILURE);

    //agrupamento em clusters
    int *clusters = malloc(cities * sizeof(int));
    if (clusters == NULL) exit(EXIT_FAILURE);

    WCQU(operations, map, clusters, cities);

    City *Cities = malloc(cities * sizeof(City));
    CityMan(Cities, cities, clusters, position);

    int cluster_counter = ClusterMan(clusters, cities, Cities);

    QuestsMan(results, quests, cluster_counter,  cities,  clusters, Cities);

    fclose(map);
    fclose(quests);
    fclose(position);
    fclose(results);
    free(clusters);
    free(Cities);
    return 0;

}





void CityMan(City *Cities, int cities, int* clusters, FILE* position){

int X_max, Y_max;

    if(fscanf(position, "%d %d", &X_max, &Y_max) != 2) exit(EXIT_FAILURE);
    if(X_max <= 0 || Y_max <= 0) exit(EXIT_FAILURE);
    int x, y,num = 1;
    for(int i = 0; i < cities; i++){

        if(Cities == NULL) exit(EXIT_FAILURE);
        if(fscanf(position, "%d %d %d", &num, &x, &y) != 3) exit(EXIT_FAILURE);
        if(num < 1 || num > cities || x <= 0 || y <= 0 || x > X_max || y > Y_max)exit(EXIT_FAILURE);
        Cities[i].city_number = num;
        Cities[i].x = x;
        Cities[i].y = y;
        Cities[i].cluster_root = clusters[num - 1];


    }
    int first;
    int last;
    qsort(Cities, cities, sizeof(City), SortAssist);
    for(int i = 0; i < cities; i++){
        if(i == 0) first = i;
        if(Cities[i].cluster_root != Cities[first].cluster_root){
            last = i - 1;
            for(int j = first; j <= last; j++){
                Cities[j].cluster_root = Cities[first].city_number;
            }
            first = i;
        }else if(i == cities - 1){
            last = i;
            for(int j = first; j <= last; j++){
                Cities[j].cluster_root = Cities[first].city_number;
            }
        }

    }
    qsort(Cities, cities, sizeof(City), SortAssist);


}
int SortAssist(const void *i, const void *j) {
    City *c1 = (City *)i;
    City *c2 = (City *)j;
    
    
    if (c1->cluster_root == c2->cluster_root) {
        return (c1->city_number - c2->city_number);
    }
    
    return (c1->cluster_root - c2->cluster_root);
}
   
int ClusterMan(int* clusters, int cities, City *Cities){

    int cluster_counter = 1;
    
    for(int i = 0; i < cities - 1; i++){
        if(Cities[i].cluster_root != Cities[i + 1].cluster_root)cluster_counter++;
    }
    

    return cluster_counter;
}





void QuestsMan(FILE* results, FILE* quests, int cluster_counter, int cities, int* clusters, City *Cities){

    int quest = 0;
    int h;
    while ((fscanf(quests, "Task%d", &quest) == 1)){
        switch (quest){
            case 1:
                Task1(cluster_counter, results);
                break;
            case 2:
                 Task2(Cities, cluster_counter, cities, clusters, results);
                 break;
            //coming soon (im here baby ;;;)))))) LEEEEEEEESSSSSSSSSS GOOOOOOOOOOOOOO
            case 3:
                Task3(quests, Cities, cities, clusters, results);
                break;
            //task4 coming soon... fds despachate la (começando as 1 da manha)
            case 4:
                Task4(quests, Cities, cities, clusters, results);
                break;

        }
         while((h = fgetc(quests)) != '\n' && h != EOF);
    }

    return;
}





void WCQU(int operations, FILE* map, int* clusters, int cities){


   int i, j, p, q, t, x;

   int *sz = (int *) malloc(cities * sizeof(int));
   if (sz == NULL) exit(EXIT_FAILURE);

   // initialize; all disconnected

   for (i = 0; i < cities; i++) {

      clusters[i] = i + 1;
      sz[i] = 1;

   }

   /* read while there is data */

   while ((fscanf(map, "%d %d", &p, &q) == 2)) {

      /* do search first */

      for (i = p; i != clusters[i - 1]; i = clusters[i - 1]);
      for (j = q; j != clusters[j - 1]; j = clusters[j - 1]);

      if (i == j) continue;

      if (sz[i -1] < sz[j - 1]) {

         clusters[i - 1] = j;
         sz[j - 1] += sz[i - 1];
         t = j;
      }else {

         clusters[j - 1] = i;
         sz[i - 1] += sz[j - 1];
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

 free(sz);

 return;

}


void Task1(int cluster_counter, FILE* results){

    fprintf(results, "Task1 %d\n\n", cluster_counter);
    return; //o return é necessario?

}


void Task2(City *Citties, int cluster_counter, int cities, int* clusters, FILE* results){
    fprintf(results, "Task2 %d", cluster_counter);

    for(int j = 0; j < cities; j++){
        // O ciclo agora começa em 0 e deteta a quebra usando !=
        if(j == 0 || Citties[j].cluster_root != Citties[j - 1].cluster_root){
            fprintf(results, "\nCluster: ");
        }
        fprintf(results, "%d ", Citties[j].city_number);
    }
    fprintf(results, "\n\n");

}

void Task3(FILE* quests, City *Cities, int cities, int* clusters, FILE* results){

    int city_ref, cluster_ref;
    double best_distance = -1; //nao existe ainda nao foi encontrado
    int closest_city = -2; //mesmo motivo que acima mas caso tudo pertença ao mesmo cluster ja temos que é -2 como pedido
    if(fscanf(quests, " %d", &city_ref) != 1) exit(EXIT_FAILURE);
    if(city_ref >= 1 && city_ref <= cities){
        cluster_ref = clusters[city_ref - 1];
        for(int i = 0; i < cities;i++){
            if(clusters[i] == cluster_ref) continue;
            int dy = Cities[city_ref -1].y - Cities[i].y;
            int dx = Cities[city_ref -1].x - Cities[i].x;
            double distance = (double) sqrt((dy*dy)+(dx*dx));
            if(best_distance == -1 || distance < best_distance){ //primeira vez ou comparando
            best_distance = distance;
            closest_city = Cities[i].city_number;
            }
        }
    }

    fprintf(results, "Task3 %d %d\n\n", city_ref, closest_city);

}

void Task4(FILE* quests, City *Cities, int cities, int* clusters, FILE* results){

    int city_ref, cluster_ref;
    double best_distance_cluster = -1;
    int closest_city_cluster = -2;
    if(fscanf(quests, " %d", &city_ref) != 1) exit(EXIT_FAILURE);
    if(city_ref >= 1 && city_ref <= cities){
        cluster_ref = clusters[city_ref -1];
        for(int i = 0; i < cities; i++){
            if(clusters[i] == cluster_ref){
                for(int j = 0; j < cities; j++){
                    if(clusters[j] == cluster_ref) continue;
                    int dy = Cities[i].y - Cities[j].y;
                    int dx = Cities[i].x - Cities[j].x;
                    double distance_cluster = (double) sqrt((dy*dy)+(dx*dx));
                    if(best_distance_cluster == -1 || distance_cluster < best_distance_cluster){
                        best_distance_cluster = distance_cluster;
                        closest_city_cluster = Cities[j].city_number;
                    }
                }
            }
        }
    }
    fprintf(results, "Task4 %d %d\n\n", city_ref, closest_city_cluster);
    return;
} 

