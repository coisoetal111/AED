/******************************************************************************
 * (c) 2010-2019 AED Team
 * Last modified: abl 2019-02-28
 *
 * NAME
 *   list.c
 *
 * DESCRIPTION
 *   Implement general linked list functions, the list contains items,
 *      addressable by a pointer (this) but it is agnostic to the type and
 *      content of each item (could be anything)
 *
 * COMMENTS
 *
 ******************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <strings.h>

#include "list.h"


/* Linked list  */
struct _t_lista {
  Item            this;
  struct _t_lista *prox;
};


/******************************************************************************
 * iniLista ()
 *
 * Arguments: none
 * Returns: t_lista *
 * Side-Effects: list is initialized (in essence nothing happens)
 *
 * Description: initializes list
 *****************************************************************************/

t_lista  *iniLista(void) {

  return NULL;
}


/******************************************************************************
 * criaNovoNoLista ()
 *
 * Arguments: nome - Item to save in list node
 * Returns: t_lista  *
 * Side-Effects: head of the list of words becomes the new word unless
 *                   there is an error
 *
 * Description: creates and returns a new node that is added to the list
 *****************************************************************************/

t_lista  *criaNovoNoLista (t_lista* lp, Item this, int *err) {
  t_lista *novoNo;

  /* create the new node */
  novoNo = (t_lista*) malloc(sizeof(t_lista));
  /* add it to the (top of the) list */
  if(novoNo!=NULL) {
    novoNo->this = this;
    novoNo->prox = lp;
    lp = novoNo;
    *err = 0;
  } else {
    *err = 1;
  }

  return lp;
}


/******************************************************************************
 * getItemLista ()
 *
 * Arguments: this - pointer to element
 * Returns: Item
 * Side-Effects: none
 *
 * Description: returns an Item from the list (through a pointer to it)
 *****************************************************************************/

Item getItemLista (t_lista *p) {

  return p -> this;
}


/******************************************************************************
 * getProxElementoLista ()
 *
 * Arguments: p - pointer to list element
 * Returns: pointer to next element in list
 * Side-Effects: none
 *
 * Description: returns a pointer to the next element of the list
 *
 *****************************************************************************/

t_lista *getProxElementoLista(t_lista *p) {

  return p -> prox;
}


/******************************************************************************
 * numItensNaLista ()
 *
 * Arguments: lp - pointer to list
 * Returns:  count of the number of items in list, i.e. size of list
 * Side-Effects: none
 *
 * Description: returns the number of items (nodes) in the list
 *
 *****************************************************************************/

int numItensNaLista(t_lista *lp) {
  t_lista *aux;  /* auxiliar pointers to travel through the list */
  int conta = 0;
  aux = lp;

  for(aux = lp; aux != NULL; aux = aux -> prox)
    conta++;

  return conta;
}

/******************************************************************************
 * libertaLista ()
 *
 * Arguments: lp - pointer to list
 * Returns:  (void)
 * Side-Effects: frees space occupied by list items and list elements
 *
 * Description: free list using local funtion as well as provided funtion to
 *              free space occupied by each item
 *
 *****************************************************************************/

void libertaLista(t_lista *lp, void freeItem(Item)) {
  t_lista *aux, *newhead;  /* auxiliar pointers to travel through the list */

  for(aux = lp; aux != NULL; aux = newhead) {
    newhead = aux->prox;
    freeItem(aux->this);
    free(aux);
  }

  return;
}
