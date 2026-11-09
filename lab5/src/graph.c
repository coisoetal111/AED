/******************************************************************************
 * (c) 2026-2027 IST AED Team
 * Last modified: 2026-11-05
 *
 * NAME
 *   graph.c
 *
 * DESCRIPTION
 *   Implementation of the Abstract Data Types (ADTs) Edge and Graph.
 *   Includes Adjacency Matrix and Adjacency List representations,
 *   representation conversions, and Depth-First Search (DFS) traversal.
 *
 * COMMENTS
 *   Code for student distribution - sections marked with TODO must be
 *   completed during the laboratory session.
 ******************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include "graph.h"
#include "LinkedList.h"

/*
 * Data type: struct edge
 *
 * Description: Internal structure of the Edge ADT.
 *              - v, w: endpoints of the edge
 *              - wt:   weight of the edge
 */
struct edge {
  int v;
  int w;
  int wt;
};

/*
 * Data type: AdjNode
 *
 * Description: Item stored in each node of a vertex's adjacency list.
 *              Stores the adjacent vertex index (v) and the edge weight (wt).
 */
typedef struct {
  int v;
  int wt;
} AdjNode;

/*
 * Data type: struct graph
 *
 * Description: Internal structure of the Graph ADT.
 *              - V:    number of vertices
 *              - E:    number of edges
 *              - adj:  adjacency matrix (V x V matrix of edge weights)
 *              - ladj: array of V adjacency lists (each list holds AdjNode* items)
 */
struct graph {
  int V;
  int E;
  int **adj;
  LinkedList **ladj;
};


/* =========================================================================
 * Auxiliary Functions for Adjacency List Items (AdjNode)
 * ========================================================================= */

/******************************************************************************
 * newAdjNode ()
 *
 * Arguments:    v  - adjacent vertex index
 *               wt - weight of the edge
 * Returns:      AdjNode* - pointer to newly allocated AdjNode
 *
 * Description:  Allocates and initializes a new adjacency list entry.
 *****************************************************************************/
AdjNode *newAdjNode(int v, int wt)
{
  AdjNode *node = (AdjNode *) malloc(sizeof(AdjNode));

  if (node == NULL) {
    fprintf(stderr, "ERROR: Not enough memory for AdjNode.\n");
    exit(1);
  }
  node->v = v;
  node->wt = wt;

  return node;
}

/******************************************************************************
 * freeAdjNode ()
 *
 * Arguments:    item - generic Item pointer to an AdjNode
 * Returns:      (void)
 *
 * Description:  Callback passed to freeLinkedList() to free each AdjNode.
 *****************************************************************************/

void freeAdjNode(Item item)
{
  free(item);
}

/******************************************************************************
 * compareAdjNodes ()
 *
 * Arguments:    it1, it2 - generic Item pointers to two AdjNodes
 * Returns:      int - negative if it1 < it2, 0 if equal, positive if it1 > it2
 *
 * Description:  Comparison callback passed to insertSortedLinkedList() so
 *               that adjacency lists are kept sorted by vertex index.
 *****************************************************************************/

int compareAdjNodes(Item it1, Item it2)
{
  AdjNode *a1 = (AdjNode *) it1;
  AdjNode *a2 = (AdjNode *) it2;
  
  return (a1->v - a2->v);
}


/* =========================================================================
 * A) Edge ADT Operations
 * ========================================================================= */

/******************************************************************************
 * EDGE ()
 *
 * Arguments:    v, w - endpoints of the edge
 *               wt   - weight of the edge
 * Returns:      Edge* - pointer to newly allocated Edge ADT
 *
 * Description:  Allocates and initializes an Edge with vertices (v, w) and
 *               weight wt.
 *****************************************************************************/

Edge *EDGE(int v, int w, int wt)
{
  Edge *e = (Edge *) malloc(sizeof(struct edge));

  if (e == NULL) {
    fprintf(stderr, "ERROR: Not enough memory for Edge.\n");
    exit(1);
  }
  e->v = v;
  e->w = w;
  e->wt = wt;
  return e;
}


int EDGEgetV(Edge *e)
{
  return e->v;
}


int EDGEgetW(Edge *e)
{
  return e->w;
}


int EDGEgetWT(Edge *e)
{
  return e->wt;
}


void EDGEdestroy(Edge *e)
{
  free(e);
}


/* =========================================================================
 * B) Graph Initialization, Destruction & Basic Accessors
 * ========================================================================= */

/******************************************************************************
 * GRAPHinit ()
 *
 * Arguments:    V - number of vertices in the graph
 * Returns:      Graph* - pointer to newly allocated Graph ADT
 *
 * Description:  Allocates memory for a Graph with V vertices, initializes
 *               its V x V adjacency matrix with zeros, and sets the
 *               adjacency list pointer to NULL (allocated on conversion).
 *****************************************************************************/

Graph *GRAPHinit(int V)
{
  int i, j;
  Graph *G = (Graph *) malloc(sizeof(struct graph));

  if (G == NULL) {
    fprintf(stderr, "ERROR: Not enough memory for Graph.\n");
    exit(1);
  }
  
  G->V = V;
  G->E = 0;
  
  /* Allocate V x V adjacency matrix */
  G->adj = (int **) malloc(V * sizeof(int *));
  if (G->adj == NULL) {
    fprintf(stderr, "ERROR: Not enough memory for adjacency matrix.\n");
    exit(1);
  }
  for (i = 0; i < V; i++) {
    G->adj[i] = (int *) malloc(V * sizeof(int));
    if (G->adj[i] == NULL) {
      fprintf(stderr, "ERROR: Not enough memory for matrix row.\n");
      exit(1);
    }
    for (j = 0; j < V; j++) {
      G->adj[i][j] = 0;
    }
  }
  
  /* Adjacency lists will be allocated when GRAPHmatToList() is called */
  G->ladj = NULL;
  
  return G;
}


/******************************************************************************
 * GRAPHdestroy ()
 *
 * Arguments:    G - pointer to Graph ADT
 * Returns:      (void)
 *
 * Description:  Frees all memory allocated for the Graph (both the adjacency
 *               matrix and, if allocated, the adjacency lists).
 *****************************************************************************/

void GRAPHdestroy(Graph *G)
{
  int i;
  
  if (G == NULL) return;
  
  if (G->adj != NULL) {
    for (i = 0; i < G->V; i++) {
      free(G->adj[i]);
    }
    free(G->adj);
  }
  
  if (G->ladj != NULL) {
    for (i = 0; i < G->V; i++) {
      freeLinkedList(G->ladj[i], freeAdjNode);
    }
    free(G->ladj);
  }
  
  free(G);

  return;
}


/******************************************************************************
 * GRAPHnumVertices () / GRAPHnumEdges ()
 *
 * Description:  Accessor functions returning V and E of the Graph ADT.
 *****************************************************************************/

int GRAPHnumVertices(Graph *G)
{
  return G->V;
}


int GRAPHnumEdges(Graph *G)
{
  return G->E;
}


/* =========================================================================
 * C) Adjacency Matrix Operations & Properties
 * ========================================================================= */

/******************************************************************************
 * GRAPHinsertE ()
 *
 * Arguments:    G - pointer to Graph ADT
 *               e - pointer to Edge ADT to insert
 * Returns:      (void)
 *
 * Description:  Inserts undirected weighted edge e = (v, w, wt) into the
 *               adjacency matrix of G.
 *****************************************************************************/

void GRAPHinsertE(Graph *G, Edge *e)
{
  int v = e->v, w = e->w, wt = e->wt;
  
  if (G->adj[v][w] == 0) {
    G->E++;
  }
  G->adj[v][w] = wt;
  G->adj[w][v] = wt;

  return;
}


/******************************************************************************
 * GRAPHremoveE ()
 *
 * Arguments:    G - pointer to Graph ADT
 *               e - pointer to Edge ADT to remove
 * Returns:      (void)
 *
 * Description:  Removes undirected edge e = (v, w) from the adjacency matrix.
 *****************************************************************************/

void GRAPHremoveE(Graph *G, Edge *e)
{
  int v = e->v, w = e->w;
  
  if (G->adj[v][w] != 0) {
    G->E--;
  }
  G->adj[v][w] = 0;
  G->adj[w][v] = 0;

  return;
}


/******************************************************************************
 * GRAPHreadMat ()
 *
 * Arguments:    fp - open file pointer to a .adj file
 * Returns:      Graph* - pointer to the constructed Graph ADT
 *
 * Description:  Reads the number of vertices V from the first line of fp,
 *               initializes a Graph G with V vertices, and reads the V x V
 *               adjacency matrix entries, inserting edges where weight > 0.
 *****************************************************************************/

Graph *GRAPHreadMat(FILE *fp)
{
  Graph *G = NULL;
  
  /*==== TODO:
   *====*/
  
  return G;
}


/******************************************************************************
 * GRAPHdegree ()
 *
 * Arguments:    G - pointer to Graph ADT
 *               v - vertex index (0 <= v < V)
 * Returns:      int - degree of vertex v
 *
 * Description:  Computes and returns the degree of vertex v using the
 *               adjacency matrix representation.
 *****************************************************************************/

int GRAPHdegree(Graph *G, int v)
{
  int j, deg = 0;
  
  /*====
   * Count how many vertices j (0 <= j < G->V) have a positive edge weight
   * in G->adj[v][j].
   *====*/
  
  for (j = 0; j < G->V; j++) {
    if (G->adj[v][j] > 0) {
      deg++;
    }
  }

  return deg;
}


/******************************************************************************
 * GRAPHmaxDegree ()
 *
 * Arguments:    G - pointer to Graph ADT
 * Returns:      int - maximum vertex degree in the graph
 *
 * Description:  Computes the maximum degree across all vertices in G.
 *****************************************************************************/

int GRAPHmaxDegree(Graph *G)
{
  int maxDeg = 0;
  
  /*==== TODO:
   *====*/
  
  return maxDeg;
}


/******************************************************************************
 * GRAPHdensity ()
 *
 * Arguments:    G - pointer to Graph ADT
 * Returns:      double - density of the undirected graph (2*E / V)
 *
 * Description:  Computes and returns the density of the graph (average degree
 *               per vertex: 2.0 * E / V).
 *****************************************************************************/

double GRAPHdensity(Graph *G)
{
  /*==== TODO:
   * Compute and return the graph density: 2.0 * E / V.
   *====*/
  
  return 0.0;
}


/* =========================================================================
 * D) Conversions Between Representations & File Output
 * ========================================================================= */

/******************************************************************************
 * GRAPHmatToList ()
 *
 * Arguments:    G - pointer to Graph ADT
 * Returns:      (void)
 *
 * Description:  Converts the adjacency matrix representation (G->adj) into
 *               the adjacency list representation (G->ladj).
 *               Uses the LinkedList API to keep each vertex's adjacency list
 *               sorted in ascending order of adjacent vertex index.
 *****************************************************************************/

void GRAPHmatToList(Graph *G)
{
  int i;
  
  /* If adjacency lists were already allocated, free them first */
  if (G->ladj != NULL) {
    for (i = 0; i < G->V; i++) {
      freeLinkedList(G->ladj[i], freeAdjNode);
    }
    free(G->ladj);
  }
  
  /* Allocate array of V linked list heads */
  G->ladj = (LinkedList **) malloc(G->V * sizeof(LinkedList *));
  if (G->ladj == NULL) {
    fprintf(stderr, "ERROR: Not enough memory for adjacency lists.\n");
    exit(1);
  }
  for (i = 0; i < G->V; i++) {
    G->ladj[i] = initLinkedList();
  }
  
  /*==== TODO:
   *====*/


  return;
}


/******************************************************************************
 * GRAPHwriteList ()
 *
 * Arguments:    G  - pointer to Graph ADT
 *               fp - open output file pointer (.ladj format)
 * Returns:      (void)
 *
 * Description:  Writes the adjacency list representation of G to file fp.
 *               First line: V. Next V lines: v1:wt1 v2:wt2 ... -1
 *****************************************************************************/

void GRAPHwriteList(Graph *G, FILE *fp)
{
  int i;
  LinkedList *aux;
  AdjNode *node;
  
  if (G == NULL || G->ladj == NULL) return;
  
  fprintf(fp, "%d\n", G->V);
  for (i = 0; i < G->V; i++) {
    for (aux = G->ladj[i]; aux != NULL; aux = getNextNodeLinkedList(aux)) {
      node = (AdjNode *) getItemLinkedList(aux);
      fprintf(fp, "%d:%d ", node->v, node->wt);
    }
    fprintf(fp, "-1\n");
  }

  return;
}


/******************************************************************************
 * GRAPHlistToEdges ()
 *
 * Arguments:    a - array of Edge* pointers to be filled (allocated by caller)
 *               G - pointer to Graph ADT
 * Returns:      int - total number of edges written into array a
 *
 * Description:  Extracts all undirected edges from the adjacency list
 *               representation (G->ladj) into the edge pointer vector a[].
 *               To avoid duplicating undirected edges, only edges (v, w)
 *               with v < w should be added to a[].
 *****************************************************************************/

int GRAPHlistToEdges(Edge *a[], Graph *G)
{
  int eCount = 0;
  
  /*==== TODO:
   *====*/
  
  return eCount;
}


/******************************************************************************
 * GRAPHwriteEdges ()
 *
 * Arguments:    a  - array of E Edge* pointers
 *               E  - number of edges
 *               V  - number of vertices
 *               fp - open output file pointer (.edge format)
 * Returns:      (void)
 *
 * Description:  Writes the edge vector representation to file fp.
 *               First line: V. Second line: E. Next E lines: v w wt.
 *****************************************************************************/

void GRAPHwriteEdges(Edge *a[], int E, int V, FILE *fp)
{
  int i;
  
  fprintf(fp, "%d\n%d\n", V, E);
  for (i = 0; i < E; i++) {
    fprintf(fp, "%d %d %d\n", EDGEgetV(a[i]), EDGEgetW(a[i]), EDGEgetWT(a[i]));
  }

  return;
}


/* =========================================================================
 * E) Graph Traversal (Depth-First Search - DFS)
 * ========================================================================= */

/******************************************************************************
 * dfsR ()
 *
 * Arguments:    G   - pointer to Graph ADT
 *               v   - current vertex being visited
 *               pre - array storing the visit order of each vertex
 *               cnt - pointer to the visit counter
 * Returns:      (void)
 *
 * Description:  Recursive Depth-First Search (DFS) helper function using
 *               the adjacency list representation (G->ladj).
 *****************************************************************************/

void dfsR(Graph *G, int v, int pre[], int *cnt)
{
  /*==== TODO:
   *====*/
}


/******************************************************************************
 * GRAPHdfs ()
 *
 * Arguments:    G   - pointer to Graph ADT
 *               pre - array of size V (allocated by caller) to store visit order
 * Returns:      int - number of connected components in G
 *
 * Description:  Performs a full Depth-First Search (DFS) traversal of G
 *               using its adjacency list representation (G->ladj).
 *               Fills pre[v] with the discovery index (0 to V-1) of each vertex
 *               and returns the total number of connected components.
 *****************************************************************************/

int GRAPHdfs(Graph *G, int pre[])
{
  int components = 0;
  
  /*==== TODO:
   *====*/
  
  return components;
}
