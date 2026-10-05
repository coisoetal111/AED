/******************************************************************************
 * (c) 2010-2019 AED Team
 * Last modified: abl 2019-03-01
 *
 * NAME
 *   main.c
 *
 * DESCRIPTION
 *   Main program for unique word finding with lists
 *
 * COMMENTS
 *   Code variant for distribution
 ******************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "words.h"

#define DIM_MAX_PALAVRA 200


/******************************************************************************
 * Usage ()
 *
 * Arguments: nomeProg - name of executable
 * Returns: (void)
 * Side-Effects: none
 *
 * Description: message function when arguments are missing
 *****************************************************************************/

void Usage(char *nomeProg)
{
  printf("Usage: %s [filename] [arguments options]\n", nomeProg);
  exit(1);
}


/******************************************************************************
 * main ()
 *
 * Arguments: argc - number of command-line arguments
 *            argv - table of pointers for string arguments
 * Returns: int status
 * Side-Effects: none
 *
 * Description: main Program
 *****************************************************************************/

int main(int argc, char *argv[])
{
  int numTotalPalavras = 0;
  int numPalavrasDiferentes;
  char extOut[] = ".palavras";
  char *nomeFicheiroIn, *nomeFicheiroOut;
  char novaPal[DIM_MAX_PALAVRA];
  FILE *fpIn,*fpOut;

  if(argc < 2)
    Usage(argv[0]);

  nomeFicheiroIn = argv[1];
  /* allocate memory for output file name */
  nomeFicheiroOut =
    (char *) malloc((strlen(nomeFicheiroIn)+strlen(extOut)+1) * sizeof(char));
  if(nomeFicheiroOut == NULL) {
    fprintf(stderr, "Memory allocation for nomeFicheiroOut in main\n" );
    exit(1);
  }

  strcpy(nomeFicheiroOut, nomeFicheiroIn);
  strcat(nomeFicheiroOut, extOut);

  /* open input file */
  fpIn  = fopen(nomeFicheiroIn,"r");
  if(fpIn == NULL) {
    printf("ERROR cannot read input file %s\n", nomeFicheiroIn);
    exit(2);
  }
  /* call words constructor; data structure ready */
  wordsCreateData();
  
  /* read input file, build word list */
  while(fscanf(fpIn, "%s", novaPal) == 1) {
    wordsAddWord(novaPal);
    numTotalPalavras++;
  }

  /* open output file */
  fpOut = fopen (nomeFicheiroOut, "w");
  if(fpOut == NULL) {
    printf("ERROR cannot write output file %s\n", nomeFicheiroOut);
    exit(3);
  }

  /* write out words to output file */
  wordsWriteUniqueWordsFrequency(fpOut);

  /* get statistics  */
  numPalavrasDiferentes = wordsNumUniqueWords();
  printf("Number of words = %d, Number of different words = %d\n",
         numTotalPalavras, numPalavrasDiferentes);

  /* free allocated memory for list of words */

  
  /* -- CLOSE ALL OPEN FILES -- */

  /* -- FREE ANY OTHER MEMORY YOU HAVE ALLOCATED -- */

  exit(0);
}
