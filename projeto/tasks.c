#include "healkristin.h"

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

void Task3(FILE *quests, City *Cities, int cities, int *clusters, FILE *results){
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
            if(best_distance == -1 || distance < best_distance || (distance == best_distance && clusters[i] < clusters[closest_city-1])){ //primeira vez ou comparando
            best_distance = distance;
            closest_city = Cities[i].city_number;
            }
        }
    }
    fprintf(results, "Task3 %d %d\n\n", city_ref, closest_city);
}
void Task4(FILE* quests, City *Cities, int cities, int *clusters, FILE* results){
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
                    if(best_distance_cluster == -1 || distance_cluster < best_distance_cluster || (distance_cluster == best_distance_cluster && clusters[j] < clusters[closest_city_cluster-1])){
                        best_distance_cluster = distance_cluster;
                        closest_city_cluster = Cities[j].city_number;
                    }
                }
            }
        }
    }
    fprintf(results, "Task4 %d %d\n\n", city_ref, closest_city_cluster);
}