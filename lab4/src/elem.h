/******************************************************************************
 *
 * File Name: vecs.c
 *	      (c) 2024 LMS
 * Author:    Luis Miguel Silveira
 * Revision:  1.0 - first light of day
 *
 * NAME
 *     vecs.h - definitions associated with vectors
 *
 * SYNOPSIS
 *       #include "yy.h"
 *
 * DESCRIPTION
 *
 *
 * DIAGNOSTICS
 *
 *****************************************************************************/


#ifndef _WORD_H_
#define _WORD_H_

#include "defs.h"

typedef struct _IntO IntO;

int ReadElem(FILE *);
FILE *OpenFile(char *, char *);

void ExitMemError(int);
int  AllocArray(IntO ***, FILE*);
int  NewElem(IntO**, int, int);
int  FillInArray(IntO**, int, FILE*);
void WriteFile(IntO**, char *, int);
void FreeArray(IntO**, int);

int  LessMagnitude(Item a, Item b);
int  MoreMagnitude(Item a, Item b);
int  LessNumUses(Item a, Item b);
int  MoreNumUses(Item a, Item b);

#endif
