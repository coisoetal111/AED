#include "healkristin.h"


int main(int argc, char **argv){

    FILE *map = NULL;
    FILE *quests = NULL;
    FILE *position = NULL;
    FILE *results = NULL;
    char filenameResult[1024];
    int cities = 0;

    
    
    FileMan(argc, argv, &map, &quests, &position, filenameResult);
    if(map == NULL || position == NULL || quests == NULL) exit(0); 
    
   
    //contagem do número de cidades

    int operations;
    if(fscanf(map, "%d %d", &cities, &operations) != 2) exit(0);
    if(cities <= 0 || operations < 0) exit(0);
 
    //agrupamento em clusters
    int *clusters = malloc(cities * sizeof(int));
    if (clusters == NULL) exit(0);

    int X_max, Y_max;
    if(fscanf(position, "%d %d", &X_max, &Y_max) != 2) exit(0);
    if(X_max <= 0 || Y_max <= 0) exit(0);

    City *Cities = malloc(cities * sizeof(City));
    if(Cities == NULL) exit(0);

    CityMan(position, Cities, cities , X_max, Y_max);

    WCQU(operations, map, clusters, cities);

    SortedCity *SortedCities = malloc(cities * sizeof(SortedCity));
    if(SortedCities == NULL) exit(0);

    SortedCityMan(SortedCities, cities, clusters);


    int cluster_counter = ClusterMan(cities, SortedCities, operations);

    //guardar informações do position
   

    

    

    results = fopen(filenameResult, "w");
    QuestsMan(results,  quests,  SortedCities,  cluster_counter,  cities,  clusters, Cities);

    fclose(map);
    fclose(quests);
    fclose(position);
    fclose(results);
    free(clusters);
    free(Cities);
    free(SortedCities);
    return 0;
 
}

