#include "healkristin.h"


int main(int argc, char **argv){

    FILE *map = NULL;
    FILE *quests = NULL;
    FILE *position = NULL;
    FILE *results = NULL;
    char filenameResult[1024];
    int cities = 0;

    //verificação do numero de argumentos corretos
    if(argc!=4) exit(0);
    char *arg[3];

    for (int i = 1; i < argc; i++) {
        arg[i -1] =  argv[i];
        
    }
    
    
    //verificação do tipo de ficheiros corretos
    //for (int i = 0; i < 3; i++){
        int j = strlen(arg[0]);
        char temp;
        char *temp_;
        for (int h = 0; h < j; h++){
            temp = arg[0][j - h];
            if(temp == '.'){  
                temp_ = &arg[0][j-h];
                if (strcmp(temp_, ".quests") == 0){
                    quests = fopen(arg[0], "r");
                    arg[0][j - h] = '\0';
                    sprintf(filenameResult, "%s.results", arg[0]);
                    arg[0][j - h] = '.';
                     
                }
                else exit(0);
                break;
            }
        }
        j = strlen(arg[1]);
        for (int h = 0; h < j; h++){
            temp = arg[1][j - h];
            if(temp == '.'){  
                temp_ = &arg[1][j-h];
                if (strcmp(temp_, ".map") == 0) map = fopen(arg[1], "r");
                else exit(0);
                break;
            }
        }
        j = strlen(arg[2]);
        for (int h = 0; h < j; h++){
            temp = arg[2][j - h];
            if(temp == '.'){  
                temp_ = &arg[2][j-h];
                if( strcmp(temp_, ".position") == 0) position = fopen(arg[2], "r");
                else exit(0);
                break;
            }
        }
    //}
    if(map == NULL || position == NULL || quests == NULL) exit(0); 
   
    //contagem do número de cidades

    int operations;
    if(fscanf(map, "%d %d", &cities, &operations) != 2) exit(0);
    if(cities <= 0 || operations < 0) exit(0);
 
    //agrupamento em clusters
    int *clusters = malloc(cities * sizeof(int));
    if (clusters == NULL) exit(0);

    WCQU(operations, map, clusters, cities);
  
    //guardar informações do position
    int X_max, Y_max;
    if(fscanf(position, "%d %d", &X_max, &Y_max) != 2) exit(0);
    if(X_max <= 0 || Y_max <= 0) exit(0);

    City *Cities = calloc(cities, sizeof(City)); //inicializar a 0 para fazer comparação sem riscos
    if(Cities == NULL) exit(0);
    int num, x, y;
    for(int i = 0; i < cities; i++){
        if(fscanf(position, "%d %d %d", &num, &x, &y) != 3) exit(0);
    
        if(num < 1 || num > cities || x <= 0 || y <= 0 || x > X_max || y > Y_max)exit(0);
    
        // se repetir o id no ficheiro tipo duas cidades 3...
        if(Cities[num - 1].city_number == num) exit(0);
        Cities[num - 1].city_number = num;
        Cities[num - 1].x = x;
        Cities[num - 1].y = y;
    }

    int *cluster_head = malloc(cities * sizeof(int));
    if(cluster_head == NULL) exit(0);

    int cluster_counter = ClusterMan(clusters, cities, cluster_head);

    results = fopen(filenameResult, "w");
    QuestsMan(results,  quests,  cluster_head,  cluster_counter,  cities,  clusters, Cities);

    fclose(map);
    fclose(quests);
    fclose(position);
    fclose(results);
    free(clusters);
    free(Cities);
    free(cluster_head);
    return 0;
 
}




