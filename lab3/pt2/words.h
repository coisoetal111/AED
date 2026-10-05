/******************************************************************************
 * (c) 2010-2019 AED Team
 * Last modified: abl 2019-03-01
 *
 * NAME
 *   words.h
 *
 * DESCRIPTION
 *   Structure and prototypes for type t_words
 *   t_palavra includes a string (nome) and an int (ocorrencias)
 *
 * COMMENTS
 *   Needs list.h definitions
 ******************************************************************************/

#ifndef _WORDS_H
#define _WORDS_H

/* type definition for structure to hold word */
typedef struct _t_words t_words;

  
/* Interface functions for type t_words */
void	wordsCreateData();
void    wordsAddWord(char*);
void	wordsWriteUniqueWordsFrequency(FILE*);
int	wordsNumUniqueWords();
void	wordsFreeData();

#endif
