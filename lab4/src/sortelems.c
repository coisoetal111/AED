/******************************************************************************
 * (c) 2024-2020 IST AED Team - Luis Miguel Silveira
 * Last modified: lms 2024-10-02
 *
 * NAME
 *   sortelems.c
 *
 * DESCRIPTION
 *   Main program for sorting elements with tables
 *
 * COMMENTS
 *
 ******************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#include "elem.h"

enum sort_order {ascending, descending};

enum sort_criteria {magnitude, occurrences};


int compCnt = 0;     /* global variable, to simplify complexity assessment */
int exchCnt = 0;


/******************************************************************************
 * sort ()
 *
 * Arguments: a - table of items to sort
 *            l, r - limits on table to consider
 *            less - item comparison function
 * Returns: (void)
 * Side-Effects: table is sorted in place
 *
 * Description: implements "some" sorting algorithm for abstract type (Item),
 *       using also an abstract type comparison function (*less)
 *           a[] - array of abstract type Item to be sorted
 *           l - index of first element in the array to be sorted
 *           r - last element ofde the array to be sorted
 *           (*less)(Item,Item) - abstract type comparison function
 *****************************************************************************/

void sort(Item arr[], int l, int r, int (*less) (Item, Item))
{
  int swapped = 1;
  int i, j = 0;
  Item tmp;

  while (swapped) {
    swapped = 0;
    for (i = r-1; i >= (l + j); i--) {

      /*==== TODO ====*/

      if (less(arr[i+1], arr[i])) {

        /*==== TODO ====*/

        tmp = arr[i];
        arr[i] = arr[i + 1];
        arr[i + 1] = tmp;

        swapped = 1;
      }
    }
    j++;
  }

  return;
}



/******************************************************************************
 * usage ()
 *
 * Arguments: (none)
 * Returns: (void)
 * Side-Effects: shows usage information
 *
 * Description: implements "some" sorting algorithm for abstract type (Item),
 *       using also an abstract type comparison function (*less)
 *           a[] - array of abstract type Item to be sorted
 *           l - index of first element in the array to be sorted
 *           r - last element of the array to be sorted
 *           (*less)(Item,Item) - abstract type comparison function
 *****************************************************************************/

void usage(char *argv0) {

  fprintf(stdout, "usage: %s _criteria_ [-a|-d]\n", argv0);
  fprintf(stdout,
          "\t where a or d means ascending or decreasing\n");
  fprintf(stdout,
          "\t where _criteria_ = magnitude | ocorrencias\n");

  return;
}


/******************************************************************************
* main ()
*
*****************************************************************************/

int main(int argc, char **argv)
{
  int Nelems;            /* total number of elements in input file */
  int Ndistelems;        /* numbber of distinct elements found */
  IntO **vtab;           /* table holding the elements */
  FILE *fp;
  char *file;
  int i = 2;

  /* default initialization for alfabetic order and ascending */
  enum sort_criteria criterio = magnitude;
  enum sort_order sentido  = ascending;


  if (argc <= 1) {
    fprintf(stderr, "Need at least one parameter, the input file name.\n");
    exit(1);
  }
  file = argv[1];

  if (strcmp(file, "-h") == 0) {
    usage(argv[0]);
    exit(0);
  }

  /* parse other arguments*/
  while (i < argc) {
    if (strcmp(argv[i], "-magnitude") == 0)
      criterio = magnitude;
    else if (strcmp(argv[i], "-ocorrencias") == 0)
      criterio = occurrences;
    else if (strcmp(argv[i], "-a") == 0)
      sentido = ascending;
    else if (strcmp(argv[i], "-d") == 0)
      sentido = descending;
    else {
      fprintf(stderr, "Wrong arguments\n");
      usage(argv[0]);
      exit(3);
    }
    i++;
  }
  /* open input file */
  fp = OpenFile(file, "r");
  if (fp == ((FILE*) NULL)) {
    fprintf(stderr, "Cannot open file %s. Exiting.\n", file);
    exit(1);
  }

  Nelems = AllocArray(&vtab, fp);
  printf("Total number of elements: %d\n", Nelems);

  Ndistelems = FillInArray(vtab, Nelems, fp);

  /* close input file, do not need it anymore */
  fclose(fp);


  /*  Call the sorting function using as argument the
      appropriate comparison function selected by user option */

  if ((criterio == magnitude) && (sentido == ascending)) {

    /*==== TODO ====*/

  }
  else if ((criterio == magnitude) && (sentido == descending)) {

    /*==== TODO ====*/

  }
  else if ((criterio == occurrences) && (sentido == ascending)) {

    /*==== TODO ====*/

  }
  else if ((criterio == occurrences) && (sentido == descending)) {

    /*==== TODO ====*/

  }

  /* ---------------------------------------- */
  printf("Accesses count for sort: %d comps %d exch %d total\n",
         compCnt, exchCnt, compCnt+exchCnt);

  WriteFile(vtab, file, Ndistelems);

  /* -- Insert code to call functions to free allocated memory -- */

  /*==== TODO ====*/

  /* ------------------------------------------------------------ */

  return 0;
}
