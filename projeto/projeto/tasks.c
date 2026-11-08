#include "healkristin.h"

void Task1(int cluster_counter, FILE* results){

    fprintf(results, "Task1 %d\n\n", cluster_counter);
    
    return; 
}

void Task2(int* cluster_head, int cluster_counter, int cities, int* clusters, FILE* results){

    fprintf(results, "Task2 %d", cluster_counter);
    if(cluster_counter == cities){ 
        for(int i = 1; i <= cities; i++) fprintf(results, "\nCluster: %d", i);
        fprintf(results, "\n\n");
        return;
    }
    int j = 0;
    fprintf(results, "\nCluster: ");
    int first = 1;
    for(int i = 0; i < cities; i++) if(clusters[0] == clusters[i]){ fprintf(results, first ? "%d" : " %d", i + 1); first = 0; }
    while(cluster_head[j] != 0){
        fprintf(results, "\nCluster: ");
        first = 1;
        for(int i = 0; i < cities; i++){
            if(clusters[i] == cluster_head[j]){
                fprintf(results, first ? "%d" : " %d", i + 1);
                first = 0;
            }
        }
        j++;
    }
    fprintf(results, "\n\n");

    return;
}

void Task3(FILE *quests, City *Cities, int cities, int *clusters, FILE *results, int cluster_counter){
    
    int city_ref, cluster_ref;
    long long best_distance = -1; //nao existe ainda nao foi encontrado
    int closest_city = -2; //mesmo motivo que acima mas caso tudo pertença ao mesmo cluster ja temos que é -2 como pedido
    if(fscanf(quests, " %d", &city_ref) != 1) exit(0);

    if(cluster_counter == 1 || city_ref < 1 || city_ref > cities){
    fprintf(results, "Task3 %d -2\n\n", city_ref); 
    return;
    }
    if(city_ref >= 1 && city_ref <= cities){ 
        cluster_ref = clusters[city_ref - 1];
        for(int i = 0; i < cities;i++){
            if(clusters[i] == cluster_ref) continue;
            long long dy = Cities[city_ref -1].y - Cities[i].y; 
            long long dx = Cities[city_ref -1].x - Cities[i].x;
            long long distance = (dy*dy)+(dx*dx);
            if(best_distance == -1 || distance < best_distance){ //primeira vez ou comparando
            best_distance = distance;
            closest_city = Cities[i].city_number;
            }
        }
    }
    fprintf(results, "Task3 %d %d\n\n", city_ref, closest_city);
}


void Task4(FILE* quests, City *Cities, int cities, int *clusters, FILE* results, int cluster_counter){
    int city_ref, cluster_ref, k = 0, x = 0, inside_cities[cities], outside_cities[cities];
    long long best_distance_cluster = -1;
    int closest_city_cluster = -2;
    if(fscanf(quests, " %d", &city_ref) != 1) exit(0);
    if(cluster_counter == 1 || city_ref < 1 || city_ref > cities){
    fprintf(results, "Task4 %d -2\n\n", city_ref); 
    return;
    }
    cluster_ref = clusters[city_ref -1];
    for(int i = 0; i < cities; i++){ 
        if(clusters[i] != cluster_ref) outside_cities[k++] = i;
        else  inside_cities[x++] = i;
    }
    inside_cities[x] = -3; //flag de final de array, -3 para ser distinto das outras 2
    outside_cities[k] = -3;
    for(int i = 0; inside_cities[i] != -3; i++){        
        for(int j = 0; outside_cities[j] != -3; j++){
            if(clusters[outside_cities[j]] == cluster_ref) continue;
                long long dy = Cities[inside_cities[i]].y - Cities[outside_cities[j]].y; 
                long long dx = Cities[inside_cities[i]].x - Cities[outside_cities[j]].x;
                long long distance_cluster = (dy*dy)+(dx*dx);
                if(best_distance_cluster == -1 || distance_cluster < best_distance_cluster || (distance_cluster == best_distance_cluster && Cities[outside_cities[j]].city_number < closest_city_cluster)){
                    best_distance_cluster = distance_cluster;
                    closest_city_cluster = Cities[outside_cities[j]].city_number;
                }
        }
    
    }
    fprintf(results, "Task4 %d %d\n\n", city_ref, closest_city_cluster);
}