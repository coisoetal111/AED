#include "healkristin.h"



int ClusterMan(int* clusters, int cities, int* cluster_head){
for (int i = 0; i < cities; i++) cluster_head[i] = 0;

 int temp_ = 0;
 int found = 0;
 int cluster_counter = 1;
 for(int i = 1; i < cities; i++) if(clusters[i] != clusters[0]){ 
    
    if(temp_ == 0){
         cluster_counter++;
         temp_ ++;
         cluster_head[0] = clusters[i];
    }else{
        for(int j = 0; j < temp_; j++){
            found = 0;
            if(cluster_head[j] == clusters[i]){
                found = 1;
                break;
            }
        }
        if(found == 0){
            cluster_head[temp_] = clusters[i];
            temp_ ++;
            cluster_counter++;         
        }
    }
}
 return cluster_counter;
}



void QuestsMan(FILE* results, FILE* quests, int* cluster_head, int cluster_counter, int cities, int* clusters, City *Cities){
    int quest = 0;
    int h;
    while ((fscanf(quests, "Task%d", &quest) == 1)){
        switch (quest){
            case 1:
                Task1(cluster_counter, results);
                break;
            case 2:
                 Task2(cluster_head, cluster_counter, cities, clusters, results);
                 break;
            //coming soon (im here baby ;;;)))))) LEEEEEEEESSSSSSSSSS GOOOOOOOOOOOOOO
            case 3:
                Task3(quests, Cities, cities, clusters, results);
                break;
            //task4 coming soon... fds despachate la (começando as 1 da manha)
            case 4:
                Task4(quests, Cities, cities, clusters, results);
                break;
        }
         while((h = fgetc(quests)) != '\n' && h != EOF);
    }
    return;
}


void WCQU(int operations, FILE* map, int* clusters, int cities){

   int i, j, p, q, t, x;
   int *size = (int *) malloc(cities * sizeof(int));
   if (size == NULL) exit(0);
  
   for (i = 0; i < cities; i++) {
      clusters[i] = i + 1;
      size[i] = 1;
   }
   
   while ((fscanf(map, "%d %d", &p, &q) == 2)) {
    
      for (i = p; i != clusters[i - 1]; i = clusters[i - 1]); 
      for (j = q; j != clusters[j - 1]; j = clusters[j - 1]);
      if (i == j) {
         continue;
      }
      if (size[i -1] < size[j - 1]) {
         clusters[i - 1] = j;
         size[j - 1] += size[i - 1];
         t = j;
      }
      else {
         clusters[j - 1] = i;
         size[i - 1] += size[j - 1];
         t = i;
      }
      
      for (i = p; i != clusters[i - 1]; i = x) {
         x = clusters[i - 1];
         clusters[i - 1] = t;
      }
      for (j = q; j != clusters[j - 1]; j = x) {   
         x = clusters[j - 1];
         clusters[j - 1] = t;
      }
}
 for(int k = 1; k <= cities; k++){
         int root = k;
         while(root != clusters[root - 1]) root = clusters[root - 1];
         clusters[k - 1] = root;
      }
 free(size);
 return;
}
