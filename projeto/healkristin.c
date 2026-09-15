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
 if(map == NULL || position == NULL || quests == NULL) exit(EXIT_FAILURE); 
 
 //contagem do número de cidades
 int ch;
 while((ch = fgetc(position)) != EOF){
    if(ch == '\n') cities ++;
 }
 rewind(position);

 //agrupamento em clusters
 int clusters[cities];
 for(int i = 0; i < cities; i++) clusters[i] = i;
 int i = 0;
 int p,q,r;
 while(fscanf(map, "%d %d", &p, &q) == 2){
    if(clusters[p] == clusters[q]) continue; 
    r = clusters[q];
    for(int i = 0; i < cities; i++) if(clusters[i] == r) clusters[i] = clusters[p];
 }
 rewind(map);
  
 //cluster counter
 int temp[cities];
 for (int i = 0; i < cities; i++) temp[i] = 0;
 int temp_ = 0;

 int cluster_couter = 1;
 for(int i = 2; i < cities; i++) if(clusters[1] != clusters[i]){ 
    

    if(temp_ == 0){
         cluster_couter++;
         temp_ ++;
         temp[0] = clusters[i];
    }else{
        for(int j = 0; j < temp_; j++){
            if(temp[j] == clusters[i]){
                continue;
            }
            temp[temp_] = clusters[i];
            temp_ ++;
            cluster_couter++;
        }
    }
    

}

fprintf(results, "Task1 %d", cluster_couter);
 
 

}
