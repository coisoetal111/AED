#ifndef HEALKRISTIN_H
#define HEALKRISTIN_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <limits.h>

typedef struct{
    int x;
    int y;
    int city_number;
} City;

typedef struct{
    double distance;
    int City_in;
    int City_out;
} Connect;

int ClusterMan(int* clusters, int cities, int* cluster_head,int operations);
void QuestsMan(FILE* results, FILE* quests, int* cluster_head, int cluster_counter, int cities, int* clusters, City *Cities);
void WCQU(int operations, FILE* map, int* clusters, int cities);
void Task1(int cluster_counter, FILE* results);
void Task2(int* cluster_head, int cluster_counter,int cities, int* clusters, FILE* results);
void Task3(FILE* quests, City *Cities, int cities, int *clusters, FILE* results, int cluster_counter);
void Task4(FILE* quests, City *Cities, int cities, int *clusters, FILE* results, int cluster_counter);
void Task5(City *Cities, int cities, int *cluster, FILE *results);
#endif