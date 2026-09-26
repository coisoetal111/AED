/******************************************************************************
 * (c) 2010-2019 AED Team
 * Last modified: abl 2019-02-22
 *
 * NAME
 *   connectivity.c
 *
 * DESCRIPTION
 *   Algorithms for solving the connectivity problem -  QF QU WQU CWQU
 *   For each method count number of entry pairs and the number of links
 *
 * COMMENTS
 *   Code for public distribution
 ******************************************************************************/
#include<stdio.h>
#include<stdlib.h>

#include "connectivity.h"

#define DEBUG 0

/******************************************************************************
 * quick_find()
 *
 * Arguments: id - array with connectivity information
 *            N - size of array
 *            fp - file pointer to read data from
 *            quietOut - to reduce output to just final count
 * Returns: (void)
 * Side-Effects: pairs of elements are read and the connectivity array is
 *               modified
 *
 * Description: Quick Find algorithm
 *****************************************************************************/

void quick_find(int *id, int N, FILE * fp, int quietOut)
{
   int i, p, q, t;
   int pairs_cnt = 0;            /* connection pairs counter */
   int links_cnt = 0;            /* number of links counter */
   long int numOpsFind = 0;
   long int numOpsUnion = 0;

   /* initialize; all disconnected */
   for (i = 0; i < N; i++) {
      numOpsFind++;
      id[i] = i;
   }

   /* read while there is data */
   while (fscanf(fp, "%d %d", &p, &q) == 2) {
      pairs_cnt++;
      numOpsFind+=2;
      /* do search first */
      if (id[p] == id[q]) {
         /* already in the same set; discard */
#if (DEBUG == 1)
         printf("\t%d %d\n", p, q);
#endif
         
         continue;
      }

      /* pair has new info; must perform union */
      numOpsFind++;
      for (t = id[p], i = 0; i < N; i++) {
         numOpsFind++;
         if (id[i] == t) {
            numOpsUnion+=2;
            id[i] = id[q];
         }
      }
      links_cnt++;
      if (!quietOut)
         printf(" %d %d\n", p, q);
   }
   int h;
   int first = 1;
   int nconj = 0;
   unsigned long nops = 0;
   for(int i = 0; i < N; i++){
      nops++;
      if(id[i] != -1){
         nops++;
         h = id[i];
         for(int j = i; j < N; j++){
            nops++;
            if(id[j] == h){ 
               if(first == 0)printf("-");
               printf("%d", j);
               first = 0;
               nops++;
               id[j] = -1;
            }
         
      }
      printf("\n");
      first = 1;
      nconj++;

      }

   }
   printf("O número de conjuntos é: %d\n", nconj);
   printf("O número de ops para agrupar é: %ld.\n", nops);

   printf("QF: The number of links performed is %d for %d input pairs.\n",
          links_cnt, pairs_cnt);
   printf("QF: %ld(F)+%ld(U) relevant accesses were performed (total: %ld)\n",
          numOpsFind, numOpsUnion, numOpsFind+numOpsUnion);
   printf("QF: The number of finds performed is %ld.\n",
          numOpsFind);
   printf("QF: The number of unions performed is %ld.\n",
          numOpsUnion);
   return;
}


/******************************************************************************
 * quick_union()
 *
 * Arguments: id - array with connectivity information
 *            N - size of array
 *            fp - file pointer to read data from
 *            quietOut - to reduce output to just final count
 * Returns: (void)
 * Side-Effects: pairs of elements are read and the connectivity array is
 *               modified
 *
 * Description: Quick Union algorithm
 *****************************************************************************/

void quick_union(int *id, int N, FILE * fp, int quietOut)
{

   int i, j, p, q;
   int pairs_cnt = 0;            /* connection pairs counter */
   int links_cnt = 0;            /* number of links counter */
   long int numOpsFind = 0;
   long int numOpsUnion = 0;

   /* initialize; all disconnected */
   for (i = 0; i < N; i++) {
      numOpsFind++;
      id[i] = i;
   }

   /* read while there is data */
   while (fscanf(fp, "%d %d", &p, &q) == 2) {
      pairs_cnt++;
      i = p;
      j = q;

      /* do search first */
      
      while (i != id[i]) {
         numOpsFind+=2;
         i = id[i];
      }
      numOpsFind++;
      
      while (j != id[j]) {
         numOpsFind+=2;
         j = id[j];
      }
      numOpsFind++;
      if (i == j) {
         /* already in the same set; discard */
#if (DEBUG == 1)
         printf("\t%d %d\n", p, q);
#endif
         continue;
      }

      /* pair has new info; must perform union */
      
      id[i] = j;
      numOpsUnion++;
      links_cnt++;

      if (!quietOut)
         printf(" %d %d\n", p, q);
   }
   printf("QU: The number of links performed is %d for %d input pairs.\n",
          links_cnt, pairs_cnt);
   printf("QU: %ld(F)+%ld(U) relevant accesses were performed (total: %ld)\n",
          numOpsFind, numOpsUnion, numOpsFind+numOpsUnion);
   printf("QU: The number of finds performed is %ld.\n",
          numOpsFind);
   printf("QU: The number of unions performed is %ld.\n",
          numOpsUnion);
}


/******************************************************************************
 * weighted_quick_union()
 *
 * Arguments: id - array with connectivity information
 *            N - size of array
 *            fp - file pointer to read data from
 *            quietOut - to reduce output to just final count
 * Returns: (void)
 * Side-Effects: pairs of elements are read and the connectivity array is
 *               modified
 *
 * Description: Weighted Quick Union algorithm
 *****************************************************************************/

void weighted_quick_union(int *id, int N, FILE * fp, int quietOut)
{

   int i, j, p, q;
   int *sz = (int *) malloc(N * sizeof(int));
   int pairs_cnt = 0;            /* connection pairs counter */
   int links_cnt = 0;            /* number of links counter */
   long int numOpsFind = 0;
   long int numOpsUnion = 0;
   long int numOpsUnionBalance = 0;

   /* initialize; all disconnected */
   for (i = 0; i < N; i++) {
      id[i] = i;
      sz[i] = 1;
      numOpsFind += 2;
   }

   /* read while there is data */
   while (fscanf(fp, "%d %d", &p, &q) == 2) {
      pairs_cnt++;

      /* do search first */
      for (i = p; i != id[i]; i = id[i])numOpsFind+=2;
      
      for (j = q; j != id[j]; j = id[j])numOpsFind+=2;
      

      if (i == j) {
         /* already in the same set; discard */
#if (DEBUG == 1)
         printf("\t%d %d\n", p, q);
#endif
         continue;
      }

      /* pair has new info; must perform union; pick right direction */
      numOpsFind +=2;
      if (sz[i] < sz[j]) {
         
         numOpsUnionBalance += 2;
         numOpsUnion++;
         id[i] = j;
         sz[j] += sz[i];
      }
      else {
         numOpsUnionBalance += 2;
         numOpsUnion++;
         
         id[j] = i;
         sz[i] += sz[j];
      }
      links_cnt++;

      if (!quietOut)
         printf(" %d %d\n", p, q);
   }
   printf("WQU: The number of links performed is %d for %d input pairs.\n",
          links_cnt, pairs_cnt);
   printf("WQU: %ld(F)+%ld(U)+%ld(W) relevant accesses were performed (total: %ld)\n",
          numOpsFind, numOpsUnion, numOpsUnionBalance,
          numOpsFind+numOpsUnion+numOpsUnionBalance);
   printf("WQU: The number of finds performed is %ld.\n",
          numOpsFind);
   printf("WQU: The number of unions performed is %ld.\n",
          numOpsUnion);
    printf("WQU: The number of balance unions performed is %ld.\n",
          numOpsUnionBalance);
   

   free(sz);
   return;
}


/******************************************************************************
 * compressed_weighted_quick_union()
 *
 * Arguments: id - array with connectivity information
 *            N - size of array
 *            fp - file pointer to read data from
 *            quietOut - to reduce output to just final count
 * Returns: (void)
 * Side-Effects: pairs of elements are read and the connectivity array is
 *               modified
 *
 * Description: Compressed Weighted Quick Union algorithm
 *****************************************************************************/

void compressed_weighted_quick_union(int *id, int N, FILE * fp, int quietOut)
{
   int i, j, p, q, t, x;
   int *sz = (int *) malloc(N * sizeof(int));
   int pairs_cnt = 0;            /* connection pairs counter */
   int links_cnt = 0;            /* number of links counter */
   long int numOpsFind = 0;
   long int numOpsUnion = 0;
   long int numOpsUnionBalance = 0;
   long int numOpsUnionCompress = 0;

   /* initialize; all disconnected */
   for (i = 0; i < N; i++) {
      numOpsFind += 2;
      id[i] = i;
      sz[i] = 1;
   }

   /* read while there is data */
   while (fscanf(fp, "%d %d", &p, &q) == 2) {
      pairs_cnt++;

      /* do search first */
      for (i = p; i != id[i]; i = id[i]) numOpsFind+=2;
      for (j = q; j != id[j]; j = id[j]) numOpsFind+=2;

      if (i == j) {
         /* already in the same set; discard */
#if (DEBUG == 1)
         printf("\t%d %d\n", p, q);
#endif
         continue;
      }

      /* pair has new info; must perform union; pick right direction */
      numOpsFind+=2;
      if (sz[i] < sz[j]) {
         numOpsUnionBalance+=2;
         numOpsUnion++;
         
         id[i] = j;
         sz[j] += sz[i];
         t = j;
      }
      else {
         numOpsUnionBalance+=2;
         numOpsUnion++;
         
         id[j] = i;
         sz[i] += sz[j];
         t = i;
      }
      links_cnt++;

      /* retrace the path and compress to the top */
      for (i = p; i != id[i]; i = x) {
         numOpsUnionCompress+=3;
         x = id[i];
         id[i] = t;
      }
      for (j = q; j != id[j]; j = x) {
         numOpsUnionCompress+=3;
         x = id[j];
         id[j] = t;
      }
      if (!quietOut)
         printf(" %d %d\n", p, q);
   }
   printf("CWQU: The number of links performed is %d for %d input pairs.\n",
          links_cnt, pairs_cnt);
   printf("CWQU: %ld(F)+%ld(U)+%ld(W)+%ld(C) relevant accesses were performed (total: %ld)\n",
          numOpsFind, numOpsUnion, numOpsUnionBalance, numOpsUnionCompress,
          numOpsFind+numOpsUnion+numOpsUnionBalance+numOpsUnionCompress);
   printf("CWQU: The number of finds performed is %ld.\n",
          numOpsFind);
   printf("CWQU: The number of unions performed is %ld.\n",
          numOpsUnion);
   printf("CWQU: The number of balance unions performed is %ld.\n",
          numOpsUnionBalance);
   printf("CWQU: The number of compress unions performed is %ld.\n",
          numOpsUnionCompress);

   free(sz);
   return;
}
