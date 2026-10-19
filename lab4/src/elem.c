/******************************************************************************
 * (c) 2024 IST AED Team - Luis Miguel Silveira
 * Last modified: lms 2024-10-02
 *
 * NAME
 *   elem.c
 *
 * DESCRIPTION
 *   Data structure to hold element, in this case an integer and useage count
 *	Auxiliary functions to read and write text files
 *		functions to allocate and manipulate structures
 *		functions to sort abstract structures
 *		implementations of "less" functions for different criteria
 *
 * COMMENTS
 *   Code for preliminary distribution, to be completed
 ******************************************************************************/

#define MAX_CHARS 100
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "elem.h"

struct _IntO {      /* structure for integer with # ocurrences */
  int num;
  int numRepeat;
};


/******************************************************************************
 * ExitMemError ()
 *
 * Arguments:    k - exit status to use
 * Returns:      (void)
 * Side-Effects: executions ends
 *
 * Description: general function for memory allocation error and exit
 *****************************************************************************/

void ExitMemError(int k)
{
   fprintf(stderr, "ERROR: Not enough memory.\n");
   exit(k);
}


/******************************************************************************
 * ReadElem ()
 *
 * Arguments:    fp - file pointer to read from
 * Returns:      int - element read, -1 if cannot read
 * Side-Effects: none
 *
 * Description:
 *   Reads an integer number from open file, returns number read
 *
 *****************************************************************************/

int ReadElem(FILE * fp)  {
  int locx;

  if (fscanf(fp, "%d", &locx) == 1)
    return locx;
  else
    return -1;
}


/******************************************************************************
 * OpenFile ()
 *
 * Arguments: nome - pointer to string containing name of file to open
 *            mode - mode to use to open the file
 * Returns: FILE * - handle to file opened
 * Side-Effects: input file is opened
 *
 * Description: Open file for reading, returns handle, or exits if it fails
 *****************************************************************************/

FILE *OpenFile(char *name, char *mode)
{
   FILE *fp;

   fp = fopen(name, mode);
   if (fp == NULL) {
      fprintf(stderr, "Error: Unable to open file '%s'\n.", name);
      exit(1);
   }
   return fp;
}


/******************************************************************************
 * AllocArray ()
 *
 * Arguments: wtab - pointer to table
 *            fp - handle for input file
 * Returns: int - number of elements read
 * Side-Effects: elements are read, table is allocated; input file is closed
 *
 * Description: Reads the input file, counts the total number of elementss and
 *		allocates the memory for the table structure
 *****************************************************************************/

int AllocArray(IntO ***wtab, FILE *fp)
{
    int Nelems;

    /* read first number in file, which is array size */
    Nelems = ReadElem(fp);

    if (Nelems == -1) {
      fprintf(stderr, "Cannot read size. Exiting.\n");
      exit(1);
    }

    (*wtab) = (IntO**) malloc(Nelems * sizeof(IntO *));

    if (*wtab == NULL)
      ExitMemError(2);

    return Nelems;
}


/******************************************************************************
 * NewElem ()
 *
 * Arguments:    vtab - pointer to table
 *               elem - recently read element
 *               Nelems - number of distinct elements found so far
 * Returns:      int - index/status regarding element being new
 * Side-Effects: none
 *
 * Description: Search table for element, return index or -1 if not found
 *****************************************************************************/

int NewElem(IntO **vtab, int locx, int Nelems)
{
   int i = 0;

   while (i < Nelems) {
     if (vtab[i]->num == locx)
       return i;
      i++;
   }
   return -1;
}


/******************************************************************************
 * FillInArray ()
 *
 * Arguments:    wtab - pointer to table
 *               Nelems - number of elements expected to find in file
 *               fp - handle for input file
 * Returns:      (int) number of distinct elements read
 * Side-Effects: prints message with element count
 *
 * Description: Opens file, fills table with elements found;
 *              if found more or less than Nelems, complain and return
 *****************************************************************************/

int FillInArray(IntO **vtab, int Nelems, FILE *fp)
{
  int n;
  int locx;
  int Ncount = 0;

  while (fscanf(fp, "%d", &locx) == 1) {
    if (Ncount < Nelems) {
      if ((n = NewElem(vtab, locx, Ncount)) == -1) {
         /* element has not been seen; add to table */
        vtab[Ncount] = (IntO *) malloc(sizeof(IntO));

        if (vtab[Ncount] == NULL)
          ExitMemError(3);
        vtab[Ncount]->num = locx;
        vtab[Ncount]->numRepeat = 1;
        Ncount++;
      }
      else {
         /* element is not new; increment occurrence count */
         vtab[n]->numRepeat++;
      }

    } else {
      fprintf(stderr, "Already read %d elements. Stopped reading.\n", Nelems);
    }
  }

  return Ncount;
}


/******************************************************************************
* WriteFile ()
*
* Arguments: vtab - pointer to table
*            file - handle for output file
*            Ndistelems - number of distinct elements seen
* Returns: (void)
* Side-Effects: output file is written
*
* Description: Writes table to file
*****************************************************************************/

void WriteFile(IntO **vtab, char *file, int Ndistelems)
{
    FILE *f;
    char *fname;
    int i = 0;

    fname =
      (char *) malloc((strlen(file) + strlen(".sorted") + 1) * sizeof(char));
    if (fname == NULL) {
        fprintf(stderr,
            "Error: allocation of output filename. Not enough memory.\n");
        ExitMemError(4);
    }
    strcpy(fname, file);
    strcat(fname, ".sorted");

    f = OpenFile(fname, "w");
    for (i = 0; i < Ndistelems; i++) {
      fprintf(f, "%d: %d\n", vtab[i]->numRepeat, vtab[i]->num);
    }

    fclose(f);
    free(fname);

    return;
}


/******************************************************************************
 * FreeArray ()
 *
 * Arguments: wtab - pointer to table
 *            Ndistelems - number of elements actually used
 * Returns: (void)
 * Side-Effects: frees memory allocated for table and structs
 *
 * Description: Frees all the memory allocated in IntO
 *****************************************************************************/

void FreeArray(IntO **vtab, int Ndistelems)
{
   /** -- free all memory allocated for table of words -- */

   /*==== TODO ====*/

   return;
}


/******************************************************************************
* LessMagnitude ()
*
* Arguments: a, b - items to be compared
* Returns: int - result of comparison
* Side-Effects: none
*
* Description: Implements the comparision for magnitude ordering
*****************************************************************************/

int LessMagnitude(Item a, Item b)
{
  if ((((IntO *) a)->num < ((IntO *) b)->num))
    return 1;
  else
    return 0;
}


/*************************************************************************
 **  -- Add comparison functions for the remaining criteria --
*************************************************************************/

    /*==== TODO ====*/



int  MoreMagnitude(Item a, Item b)
{
  if ((((IntO *) a)->num > ((IntO *) b)->num))
    return 1;
  else
    return 0;
}
int  LessNumUses(Item a, Item b)
{
  if ((((IntO *) a)->numRepeat < ((IntO *) b)->numRepeat))
    return 1;
  else
    return 0;
}
int  MoreNumUses(Item a, Item b)
{
  if ((((IntO *) a)->numRepeat > ((IntO *) b)->numRepeat))
    return 1;
  else
    return 0;
}

