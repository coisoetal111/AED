#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <unistd.h>



int main(int argc, char **argv){

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
           if (!(strcmp(temp_, ".quests") == 0 || strcmp(temp_, ".map") == 0 || strcmp(temp_, ".position") == 0)) exit(EXIT_FAILURE);
           
        }
    }
    
 }
  
 

}