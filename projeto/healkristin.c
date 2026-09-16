#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <unistd.h>



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
  
 //cluster counter (Task1)
 int temp[cities];
 for (int i = 0; i < cities; i++) temp[i] = 0;
 int temp_ = 0;

 int cluster_couter = 1;
 for(int i = 1; i < cities; i++) if(clusters[0] != clusters[i]){ 
    

    if(temp_ == 0){
         cluster_couter++;
         temp_ ++;
         temp[0] = clusters[i];
    }else{
        for(int j = 0; j < temp_; j++){
            if(temp[j] == clusters[i]){
                continue;
            }else if(j == temp_ -1){
                temp[temp_] = clusters[i];
                temp_ ++;
                cluster_couter++;
            }
        }
        
    }
    

}

fprintf(results, "\nTask1 %d", cluster_couter);
 
 

}
