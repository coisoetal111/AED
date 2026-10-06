#ifndef HEALKRISTIN_H
#define HEALKRISTIN_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

typedef struct{
    int x;
    int y;
    int city_number;
} City;

int ClusterMan(int* clusters, int cities, int* cluster_head);
void QuestsMan(FILE* results, FILE* quests, int* cluster_head, int cluster_counter, int cities, int* clusters, City *Cities);
void WCQU(int operations, FILE* map, int* clusters, int cities);
void Task1(int cluster_counter, FILE* results);
void Task2(int* cluster_head, int cluster_counter,int cities, int* clusters, FILE* results);
void Task3(FILE* quests, City *Cities, int cities, int *clusters, FILE* results);
void Task4(FILE* quests, City *Cities, int cities, int *clusters, FILE* results);

#endif