#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <unistd.h>
#include <math.h>

typedef struct{
    int x;
    int y;
    int city_number;
} City;

int ClusterMan(int* clusters, int cities, int* cluster_head, int operations);
void QuestsMan(FILE* results, FILE* quests, int* cluster_head, int cluster_counter, int cities, int* clusters, City *Cities);
void Task1(int cluster_counter, FILE* results);
void Task2(int* cluster_head, int cluster_counter,int cities, int* clusters, FILE* results);
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
 for (int i = 0; i < 3; i++)
 {
    int j = strlen(arg[i]);
    char temp;
    char *temp_;
    for (int h = 0; h < j; h++)
    {
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
           
        }
    }
    
 }
 if(map == NULL || position == NULL || quests == NULL || results == NULL) exit(EXIT_FAILURE); 
 
 //contagem do número de cidades

 int operations;
 if(fscanf(map, "%d %d", &cities, &operations) != 2)exit(EXIT_FAILURE);
 if(cities <= 0 || operations < 0)exit(EXIT_FAILURE);
 
 //agrupamento em clusters
 int clusters[cities]; 
 for(int i = 0; i < cities; i++) clusters[i] = i + 1;
 
 int p,q,r;
    
 for(int i = 0; i < operations; i++){
    if(fscanf(map, "%d %d", &p, &q) != 2) exit(EXIT_FAILURE);
    if(p < 1 || p > cities || q < 1 || q > cities) exit(EXIT_FAILURE);
    if(clusters[p - 1] == clusters[q - 1]) continue; 
    r = clusters[q - 1];
    for(int i = 0; i < cities; i++) if(clusters[i] == r) clusters[i] = clusters[p - 1];
 }
 rewind(map);
  
 //guardar informações do position
 int X_max, Y_max;
 if(fscanf(position, "%d %d", &X_max, &Y_max) != 2)exit(EXIT_FAILURE);
 if(X_max <= 0 || Y_max <= 0)exit(EXIT_FAILURE);

 City Cities[cities];
 int num, x, y;
for(int i = 0; i < cities; i++){
    if(fscanf(position, "%d %d %d", &num, &x, &y) != 3) exit(EXIT_FAILURE);
    
    if(num < 1 || num > cities || x <= 0 || y <= 0 || x > X_max || y > Y_max)exit(EXIT_FAILURE);
    
    Cities[num - 1].city_number = num;
    Cities[num - 1].x = x;
    Cities[num - 1].y = y;
}
 



 
 
 int cluster_head[cities];


 int cluster_counter = ClusterMan(clusters, cities, cluster_head, operations);

 QuestsMan(results,  quests,  cluster_head,  cluster_counter,  cities,  clusters, Cities);

    fclose(map);
    fclose(quests);
    fclose(position);
    fclose(results);
    return 0;
 
}




int ClusterMan(int* clusters, int cities, int* cluster_head, int operations){
 
if(operations > 0){
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
}else{
    int cluster_counter = cities;
    for (int i = 0; i < cities; i++) cluster_head[i] = i + 1;
    return cluster_counter;


}
}
  



void Task1(int cluster_counter, FILE* results){

    fprintf(results, "Task1 %d\n\n", cluster_counter);
    
    return;
}

void Task2(int* cluster_head, int cluster_counter, int cities, int* clusters, FILE* results){

    int j = 0;
    
    fprintf(results, "Task2 %d", cluster_counter);
    fprintf(results, "\nCluster: ");
    for(int i = 0; i < cities; i++) if(clusters[0] == clusters[i]) fprintf(results, "%d ", i + 1);
    while(cluster_head[j] != 0){
        fprintf(results, "\nCluster: ");
         for(int i = 0; i < cities; i++){
            if(clusters[i] == cluster_head[j]){
                fprintf(results, "%d ", i + 1);
            }
        }
        j++;
    }
 fprintf(results, "\n\n");

 return;
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
}

void QuestsMan(FILE* results, FILE* quests, int* cluster_head, int cluster_counter, int cities, int* clusters, City *Cities){
    int quest = 0;
    int h;
    while ((fscanf(quests, "Task%d", &quest) == 1)){
        switch (quest){
            case 1:
                Task1(cluster_counter, results);
                break;
            case 2:
                 Task2(cluster_head, cluster_counter, cities, clusters, results);
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