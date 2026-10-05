/******************************************************************************
 * (c) 2010-2019 AED Team
 * Last modified: lms 2026-09-26
 *
 * NAME
 *   palTab.c
 *
 * DESCRIPTION
 *   Main program for unique word finding with tables
 *
 * COMMENTS
 *   Code variant for distribution
 *
 ******************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#define MAX_STR 100       /* assume max size word */

typedef struct _st_texto {
  int  n_total_palavras;      /* total number of words */
  int  n_dist_palavras;       /* number of distinct words*/
  char **palavras;            /* Table of strings for words */
  int  *ocorrencias;          /* Table of integers counting occurrence */
} st_texto;


/******************************************************************************
 * LePalavra()
 *
 * Arguments: f - pointer to file where word will be read
 * Returns:  pointer to word just read
 * Side-Effects: none
 *
 * Description:
 *   Return pointer to local buffer with word, or NULL if file read failed
 *   Maximum word size MAX_STR
 *****************************************************************************/

char *LePalavra ( FILE *f )
{
  static char palavra[MAX_STR];       /* note static local buffer returned */

  if ( fscanf ( f, "%s", palavra ) ==1 )
    return (palavra);
  else
    return ((char *) NULL);
}


/******************************************************************************
 * AbreFicheiro()
 *
 * Arguments: nome - pointer to string holding name of file to open
 *            mode - pointer to string with 'r'/'w' etc mode for file open
 * Returns: pointer to opened file
 * Side-Effects: exits if given file cannot be opened with given mode
 *
 * Description:
 *   Open named file in requested mode, message stderr and exit if open fails
 *****************************************************************************/

FILE *AbreFicheiro ( char *nome, char *mode )
{
  FILE *fp;
  fp = fopen ( nome, mode );
  if ( fp == NULL ) {
    fprintf ( stderr, "ERROR: cannot open file '%s'\n", nome);
    exit ( 1 );                                 /* non-zero exit status */
  }
  return (fp);
}


/******************************************************************************
 * AlocaTabelaPalavras()
 *
 * Arguments: ficheiro - pointer to string holding name of file to open
 *            st_texto - pointer to structure where information will be saved
 * Returns: (none)
 * Side-Effects: creates table of pointers for tables of words
 *
 * Description:
 *   Read input file to find dimensions, allocate and initialize tables
 *****************************************************************************/

void AlocaTabelaPalavras ( char *ficheiro, st_texto *t)
{
  FILE *fp;
  char *palavra;
  int i, len, n_max_caracteres = 0;

  /* initialize counters for #words and #distinct_words */
  (*t).n_total_palavras = 0;
  (*t).n_dist_palavras = 0;

  /* Open input file */
  fp = AbreFicheiro ( ficheiro, "r" );

  int j = 0;
  while ( ( palavra = LePalavra ( fp ) ) != NULL ) {
    (*t).n_total_palavras++;
    len = strlen ( palavra );
    if ( len > n_max_caracteres )
      n_max_caracteres = len;
  }
  fclose ( fp );
  printf ( "Words count: %d\n", (*t).n_total_palavras );

  /* Allocate space for tables where to store words */
  (*t).palavras =  malloc ( (*t).n_total_palavras * sizeof (char *) );
  if ( (*t).palavras == NULL ) {
    fprintf ( stderr, "ERROR: not enough memory available!\n" );
    exit ( 2 );
  }
  for ( i = 0; i < (*t).n_total_palavras; i++ ) {
    (*t).palavras[i] = malloc ( (n_max_caracteres + 1) * sizeof (char) );
    if ( (*t).palavras[i] == NULL ) {
      fprintf ( stderr, "ERROR: not enough memory available!\n" );
      exit ( 3 );
    }
  }
 
  /* Allocate space for counting the number of times each word appears */
  (*t).ocorrencias = malloc ( (*t).n_total_palavras * sizeof (int) );
  if ( (*t).ocorrencias == NULL ) {
    fprintf ( stderr, "ERROR: not enough memory available!\n" );
    exit ( 4 );
  }
  

  /* initialize data structures */
  for ( i = 0; i < (*t).n_total_palavras; i++ )   {
    (*t).palavras[i][0] = '\0';
    (*t).ocorrencias[i] = 0;
  }
  
  

  return;
}


/******************************************************************************
 * NovaPalavra()
 *
 * Arguments: palavra - pointer to string holding a word
 *            st_texto - pointer to structure where run information is kept
 * Returns:  int index of word in table
 * Side-Effects: none
 *
 * Description:
 *   Search for a word in the table. If the word is not found returns -1,
 *   Otherwise returns the position of the word in the table
 *****************************************************************************/

int NovaPalavra ( char *palavra, st_texto *t )
{
  int i = 0;
  while ( i < (*t).n_dist_palavras ) {
    if ( strcmp ( (*t).palavras[i], palavra ) == 0 )
      return (i);
    i++;
  }
  return (-1);
}


/******************************************************************************
 * PreencheTabelaPalavras()
 *
 * Arguments: ficheiro - pointer to string holding name of file to open
 *            st_texto - pointer to structure where information will be saved
 * Returns: (none)
 * Side-Effects: none
 *
 * Description:
 *
 *****************************************************************************/

void PreencheTabelaPalavras ( char *ficheiro, st_texto *t )
{
  FILE *f;
  int n;
  char *palavra;

  /* Re-Open input file */
  f = AbreFicheiro ( ficheiro, "r" );

  /* read all the words from the input file and process accordingly */
  while ( ( palavra = LePalavra ( f ) ) != NULL ) {
    /* is this a new word or did we see it already */
    if ( ( n = NovaPalavra ( palavra, &(*t) ) ) == -1 ) {
      /* it is a new word */
      strcpy ( (*t).palavras[(*t).n_dist_palavras], palavra );
      (*t).ocorrencias[(*t).n_dist_palavras]++;
      (*t).n_dist_palavras++;
    }
    else {
      /* word was already seen */
      (*t).ocorrencias[n]++;
    }
  }
  fclose ( f );
  return;
}


/******************************************************************************
 * EscreveFicheiro()
 *
 * Arguments: ficheiro - pointer to string holding name of file to save
 *            st_texto - pointer to structure where information is kept
 * Returns: (none)
 * Side-Effects: none
 *
 * Description:
 *   Open output file, write table of words.
 *****************************************************************************/

void EscreveFicheiro ( char *ficheiro, st_texto *t )
{
  FILE *f;
  char *nomefich;
  int i = 0;

  nomefich =  malloc ( (strlen ( ficheiro ) + 10 ) * sizeof (char) );
  /* including dot (.) extension and string termination, see below */
  if ( nomefich == NULL ) {
    fprintf ( stderr, "ERROR: not enough memory available!\n" );
    exit ( 5 );
  }
  strcpy ( nomefich, ficheiro );
  strcat ( nomefich, ".palavras" );
  f = AbreFicheiro ( nomefich, "w" );
  for ( i = 0; i < (*t).n_dist_palavras; i++ ) {
    fprintf ( f, "%d: %s\n", (*t).ocorrencias[i], (*t).palavras[i] );
  }
  printf ( "Count of distinct words: %d\n", (*t).n_dist_palavras );
  fclose ( f );

  free ( nomefich );

  return;
}


/******************************************************************************
 * main()
 *
 * Arguments: argc - counter of number of arguments in call
 *            argv - pointer to array of strings holding the arguments
 * Returns: exit status
 * Side-Effects: none
 *
 * Description:
 *   Get filename, read input file and make word table, write output file
 *****************************************************************************/

int main ( int argc, char **argv )
{
  int i;
  st_texto st_palavras;
  st_texto *t = &st_palavras;

  if ( argc < 2 ) {
    fprintf ( stderr, "ERROR: missing filename in argument!\n" );
    exit ( 6 );
  }
  AlocaTabelaPalavras ( argv[1], &st_palavras );
  PreencheTabelaPalavras ( argv[1],&st_palavras );
  EscreveFicheiro ( argv[1], &st_palavras );
  
  for ( i = 0; i < (*t).n_total_palavras; i++ )   {
    free ( (*t).palavras[i] );
  }
  free ( (*t).palavras );
  free ( (*t).ocorrencias );
 
  return (0);
}
