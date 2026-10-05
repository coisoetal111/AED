/******************************************************************************
 * (c) 2010-2019 AED Team
 * Last modified: abl 2019-03-01
 *
 * NAME
 *   words.c
 *
 * DESCRIPTION
 *   Implements functions for type t_words
 *
 * COMMENTS
 *   Code variant for distribution
 ******************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>    /* strcasecmp() */

#include "list.h"
#include "words.h"


struct _t_words {
  char* pal;
  int ocorrencias;
};

t_lista *wordsListPt;

int wordsTotalUniqueWords = 0;


void	wordsIncOcorr(t_words*);

void 	wordsFreeWord(void*);
char 	*wordsGetWords(t_words*);
t_words *wordsCreateWord(char*);
void 	wordsMemoryError (char*);
  

/******************************************************************************
 * wordsCreateData ()
 *
 * Arguments: none
 * Returns: none
 * Side-Effects: none in reality, but initializes pointer to word list
 *
 * Description: initialize pointer to word list
 *****************************************************************************/

void wordsCreateData() {

  wordsListPt = iniLista();
  return;
}



/******************************************************************************
 * wordsIncOcorr ()
 *
 * Arguments: p - pointer to word structure
 * Returns: (void)
 * Side-Effects: none
 *
 * Description: increment counter for the number of times (ocorrencias)
 *              a word has been found
 *****************************************************************************/

void wordsIncOcorr(t_words *p)
{
  (p -> ocorrencias)++;
}



/******************************************************************************
 * wordsAddWord ()
 *
 * Arguments: novaPal - pointer to new word to be tested / inserted
 * Returns: void
 * Side-Effects: none
 *
 * Description: search for a word in the list
 *              if found increment occurrence count
 *              otherwise adds a new word to the list at the top of the list
 *****************************************************************************/

void wordsAddWord(char *novaPal)
{
  t_lista *aux;       /* pointer to scan the list */
  t_words *pal;
  int err;            /* error status, not checked */

  aux = wordsListPt;
  /* go through all the words already read */
  while (aux != NULL){
    /* get the next word; note that we do not know how it is stored, so
     * we call a function to return a pointer to the word
     */
    pal = (t_words*) getItemLista(aux);
    /* compare the supposedly new word with one already read */
    if( strcasecmp(wordsGetWords(pal),novaPal) == 0) {
      wordsIncOcorr(pal);
      return;
    }
    /* we do not know how the sequence of read words is organized, nor do we
       need to know; we simply ask for a pointer to the next element
     */
    aux = getProxElementoLista(aux);
  }

  /* if we are here, the word is new, i.e. it has not been seen before;
   * create structure for a new word and store it
   */
  pal = wordsCreateWord(novaPal);
  wordsTotalUniqueWords++;
  /* Insert; Expect insertion at the begin of the list (not sorted!) */
  wordsListPt = criaNovoNoLista(wordsListPt, pal, &err);

  return;
}



/******************************************************************************
 * wordsNumUniqueWords ()
 *
 * Arguments: (void)
 * Returns: int
 * Side-Effects: none
 *
 * Description: return number of unique words stored
 *****************************************************************************/

int wordsNumUniqueWords(Item this)
{
  return (wordsTotalUniqueWords);
}



/******************************************************************************
 * wordsErroMemoria ()
 *
 * Arguments: msg - pointer to message to print
 * Returns: (void)
 * Side-Effects: none
 *
 * Description: print to standard error output an allocation error message
 *
 *****************************************************************************/

void wordsMemoryError (char *msg) {

  fprintf(stderr, "Error during memory reserve attempt.\n");
  fprintf(stderr, "Msg: %s\n",msg);
  fprintf(stderr, "Exit Program due to unmanaged error.\n");

  exit(1);
}



/******************************************************************************
 * wordsCreateWord()
 *
 * Arguments: pal - word to be stored
 * Returns: t_words  *
 * Side-Effects: space is allocated for new word
 *
 * Description: Create and return a new word, set occurrence counter to 1
 *****************************************************************************/

t_words  *wordsCreateWord(char *pal)
{
  t_words *nova;

  nova = /* INSERT CODE to ALLOCATE MEMORY */

    if(nova == NULL)
      wordsMemoryError("Reserve memory for new word in criaWords" );

  nova -> pal = /* INSERT CODE to ALLOCATE MEMORY */


    if(nova == NULL)
      wordsMemoryError("Reserve of name in criaWords" );

  strcpy(nova -> pal,pal);
  nova -> ocorrencias = 1;

  return nova;
}


/******************************************************************************
 * wordsGetWords ()
 *
 * Arguments: p - pointer to word structure
 * Returns: (char *) pointer to actual word (string)
 * Side-Effects: none
 *
 * Description: returns a pointer to the string containing the actual word
 *****************************************************************************/

char *wordsGetWords(t_words *p)
{
  return p -> pal;
}


/******************************************************************************
 * wordGetNumOcorr ()
 *
 * Arguments: p - pointer to word structure
 * Returns: int
 * Side-Effects: none
 *
 * Description: returns the counter (ocorrencias) associated to a word
 *****************************************************************************/

int wordGetNumOcorr(t_words *p)
{
  return p -> ocorrencias;
}


/******************************************************************************
 * wordWriteWord ()
 *
 * Arguments: p - pointer to word structure
 *            fp - pointer to output file descriptor
 * Returns: (void)
 * Side-Effects: none
 *
 * Description: writes to given file the word and the number of times
 *              it was seen on the input (ocorrencias)
 *****************************************************************************/

void wordWriteWord(t_words *p, FILE *fp)
{
  fprintf(fp,"%4d : %s\n", p->ocorrencias, p->pal);

  return;
}


/******************************************************************************
 * wordsWriteUniqueWordsFrequency ()
 *
 * Arguments: fp - pointer to file to write to
 * Returns: (void)
 * Side-Effects: none
 *
 * Description: prints words and respetive frequency
 *****************************************************************************/

void wordsWriteUniqueWordsFrequency(FILE* fpOut) {

  t_lista *aux;       /* pointer to scan the list */

  /* write out words to output file */
  aux = wordsListPt;
  /*
   * we have a pointer for the first and from it to next, then the next, etc
   */
  while(aux != NULL) {
    /* note how we get the item, which is a word, from the list, without
     * knowing how the list is formed */
    wordWriteWord((t_words*) getItemLista(aux), fpOut);
    /* and now we get the next element in the list */
    aux = getProxElementoLista(aux);
  }

  return;
}


/******************************************************************************
 * wordsFreeWord ()
 *
 * Arguments: p - pointer to word structure
 * Returns: (void)
 * Side-Effects: allocated memory for word structure is freed
 *
 * Description: free memory reserved for word
 *****************************************************************************/

void wordsFreeWord(void*pv)
{
  t_words *p = (t_words*) pv;
  /* -- INSERT CODE TO FREE MEMORY RESERVED FOR WORD -- */
  
  return;
}


/******************************************************************************
 * wordsFreeData ()
 *
 * Arguments: none
 * Returns: (void)
 * Side-Effects: frees the entire list and data associated
 *
 * Description: frees the words list and th words themselves
 *****************************************************************************/

void wordsFreeData() {

  libertaLista(wordsListPt, wordsFreeWord);

  return;
}
