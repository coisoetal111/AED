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
    int j = sizeof(arg[i]);
    char temp;
    char *temp_;
    for (int h = 0; h < j; h++)
    {
        temp = arg[i][j - h];
        if(temp == '.'){
            temp_ = &arg[i][j-h];
           if (strcmp(temp_, ".quests") == 0) quests = fopen(arg[i], "r");
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
  for(int i = 0; i < cities; i++) printf("%d", clusters[i]) ;
 
 

}
