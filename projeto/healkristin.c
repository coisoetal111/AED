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
 
    //verificação do tipo de ficheiros corretos
    int j = strlen(argv[1]);
    char *temp_;
    temp_ = &argv[1][j-7];
    if (strcmp(temp_, ".quests") == 0){
        quests = fopen(argv[1], "r");
        argv[1][j - 7] = '\0';
        sprintf(filenameResult, "%s.results", argv[1]);
        argv[1][j - 7] = '.';     
        }
        else exit(0);
    j = strlen(argv[2]);
            temp_ = &argv[2][j-4];
            if (strcmp(temp_, ".map") == 0) map = fopen(argv[2], "r");
            else exit(0);
    j = strlen(argv[3]);  
        temp_ = &argv[3][j-9];
        if( strcmp(temp_, ".position") == 0) position = fopen(argv[3], "r");
        else exit(0);    
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

    int cluster_counter = ClusterMan(clusters, cities, cluster_head, operations);

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

