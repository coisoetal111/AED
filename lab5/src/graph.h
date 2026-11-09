/******************************************************************************
 * (c) 2026-2027 IST AED Team
 * Last modified: 2026-11-05
 *
 * NAME
 *   graph.h
 *
 * DESCRIPTION
 *   Header file for the Abstract Data Types (ADTs) Edge and Graph.
 *   Supports undirected weighted graphs represented via Adjacency Matrix
 *   and Adjacency Lists, conversions between representations (Matrix -> List ->
 *   Edge Vector), and Graph Traversal (Depth-First Search - DFS).
 *
 * COMMENTS
 *   Follows the definitions from the AED theoretical lectures.
 ******************************************************************************/

#ifndef _GRAPH_H_
#define _GRAPH_H_

#include <stdio.h>
#include <stdlib.h>

/*
 * Data type: Edge
 *
 * Description: Opaque structure representing an undirected weighted graph edge.
 *              Internal fields (endpoints v, w and weight wt) are hidden in
 *                  graph.c.
 */
typedef struct edge Edge;


/*
 * Data type: Graph
 *
 * Description: Opaque structure representing an abstract Graph ADT.
 *              Internal representation details (adjacency matrix and
 *              adjacency lists) are hidden in graph.c.
 */
typedef struct graph Graph;


/* =========================================================================
 * A) Edge ADT Operations
 * ========================================================================= */

Edge  *EDGE(int v, int w, int wt);
int    EDGEgetV(Edge *e);
int    EDGEgetW(Edge *e);
int    EDGEgetWT(Edge *e);
void   EDGEdestroy(Edge *e);


/* =========================================================================
 * B) Graph Initialization, Destruction & Basic Accessors
 * ========================================================================= */

Graph *GRAPHinit(int V);
void   GRAPHdestroy(Graph *G);

int    GRAPHnumVertices(Graph *G);
int    GRAPHnumEdges(Graph *G);


/* =========================================================================
 * C) Adjacency Matrix Operations & Properties
 * ========================================================================= */

void   GRAPHinsertE(Graph *G, Edge *e);
void   GRAPHremoveE(Graph *G, Edge *e);
Graph *GRAPHreadMat(FILE *fp);

int    GRAPHdegree(Graph *G, int v);
int    GRAPHmaxDegree(Graph *G);
double GRAPHdensity(Graph *G);


/* =========================================================================
 * D) Conversions Between Representations & File Output
 * ========================================================================= */

void   GRAPHmatToList(Graph *G);
void   GRAPHwriteList(Graph *G, FILE *fp);

int    GRAPHlistToEdges(Edge *a[], Graph *G);
void   GRAPHwriteEdges(Edge *a[], int E, int V, FILE *fp);


/* =========================================================================
 * E) Graph Traversal (Depth-First Search - DFS)
 * ========================================================================= */

int    GRAPHdfs(Graph *G, int pre[]);

#endif
