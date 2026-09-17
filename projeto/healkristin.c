#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <unistd.h>

void ClusterMan(int*, int, int*);
void QuestsMan(FILE* results, FILE* quests, int* cluster_head, int cluster_counter, int cities, int* clusters);
void Task1(int cluster_counter, FILE* results);
void Task2(int* cluster_head, int cluster_counter,int cities, int* clusters, FILE* results);


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
 fscanf(map, "%d %d", &cities, &operations);
 if(cities <= 0 || operations <= 0)exit(EXIT_FAILURE);
 
 //agrupamento em clusters
 int clusters[cities];
 for(int i = 0; i < cities; i++) clusters[i] = i + 1;
 
 int p,q,r;
    
 for(int i = 0; i < operations; i++){
    if(fscanf(map, "%d %d", &p, &q) != 2) exit(EXIT_FAILURE);
    if(clusters[p - 1] == clusters[q - 1]) continue; 
    r = clusters[q - 1];
    for(int i = 0; i < cities; i++) if(clusters[i] == r) clusters[i] = clusters[p - 1];
 }
 rewind(map);
  
 
 
 
 int cluster_head[cities];


 ClusterMan(clusters, cities, cluster_head);
 int cluster_counter = cluster_head[0];
 QuestsMan( results,  quests,  cluster_head,  cluster_counter,  cities,  clusters);

 return 0;
 
}




void ClusterMan(int* clusters, int cities, int* cluster_head){
 
 for (int i = 0; i < cities; i++) cluster_head[i] = 0;
 int temp_ = 0;

 int cluster_counter = 1;
 for(int i = 1; i < cities; i++) if(clusters[0] != clusters[i]){ 
    

    if(temp_ == 0){
         cluster_counter++;
         temp_ ++;
         cluster_head[1] = clusters[i];
    }else{
        for(int j = 0; j < temp_; j++){
            if(cluster_head[j + 1] == clusters[i]){
                continue;
            }else if(j == temp_ - 1){
                cluster_head[temp_ + 1] = clusters[i];
                temp_ ++;
                cluster_counter++;
            }
        }
        
    }
    

}

cluster_head[0] = cluster_counter;

}

void Task1(int cluster_counter, FILE* results){

    fprintf(results, "\nTask1 %d", cluster_counter);
}

void Task2(int* cluster_head, int cluster_counter, int cities, int* clusters, FILE* results){

    int j = 1;
    
    fprintf(results, "\n\nTask2 %d", cluster_counter);
    fprintf(results, "\nCluster: ");
    for(int i = 1; i <= cities; i++) if(clusters[1] == clusters[i]) fprintf(results, "%d ", i);
    while(cluster_head[j] != 0){
        fprintf(results, "\nCluster: ");
         for(int i = 0; i <= cities; i++){
            if(clusters[i] == cluster_head[j]){
                fprintf(results, "%d ", i + 1);
            }
        }
        j++;
    }

}

void QuestsMan(FILE* results, FILE* quests, int* cluster_head, int cluster_counter, int cities, int* clusters){
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
            //coming soon
        }
         while((h = fgetc(quests)) != '\n' && h != EOF);
    }
   
}
