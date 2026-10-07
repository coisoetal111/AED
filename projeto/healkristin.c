#include "healkristin.h"


int main(int argc, char **argv){

    FILE *map = NULL;
    FILE *quests = NULL;
    FILE *position = NULL;
    FILE *results = NULL;
    char result[1024];
    int cities = 0;

    //verificação do numero de argumentos corretos
    if(argc!=4) exit(0);
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
                else exit(0);
                continue;
           
            }
        }
    
    }
    if(map == NULL || position == NULL || quests == NULL || results == NULL) exit(0); 
 
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

    City *Cities = malloc(cities * sizeof(City));
    if(Cities == NULL) exit(0);
    int num, x, y;
    for(int i = 0; i < cities; i++){
        if(fscanf(position, "%d %d %d", &num, &x, &y) != 3) exit(0);
    
        if(num < 1 || num > cities || x <= 0 || y <= 0 || x > X_max || y > Y_max)exit(0);
    
        Cities[num - 1].city_number = num;
        Cities[num - 1].x = x;
        Cities[num - 1].y = y;
    }
 
    int *cluster_head = malloc(cities * sizeof(int));
    if(cluster_head == NULL) exit(0);


    int cluster_counter = ClusterMan(clusters, cities, cluster_head);

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




