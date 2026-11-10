/******************************************************************************
 * (c) 2026-2027 IST AED Team
 * Last modified: 2026-11-05
 *
 * NAME
 *   main.c
 *
 * DESCRIPTION
 *   Client program for Lab 05 - Graphs: Representations, Conversions, and
 *   Traversal (DFS).
 *
 * COMMENTS
 *   Code for student distribution - complete the steps indicated by the
 *   comments below.
 ******************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "graph.h"


/******************************************************************************
 * usage ()
 *
 * Description: Prints command-line usage instructions and exits.
 *****************************************************************************/

void usage(char *progName)
{
  fprintf(stderr, "Usage: %s <graph_file>.adj\n", progName);
  exit(1);
}


/******************************************************************************
 * makeOutFilename ()
 *
 * Arguments:   inName - input filename (e.g., "grafo6.adj")
 *              newExt - desired extension (e.g., ".ladj" or ".edge")
 * Returns:     char*  - newly allocated string with the output filename
 *
 * Description: Replaces the extension of inName (after the last '.') with
 *              newExt, or appends newExt if no '.' is found.
 *****************************************************************************/

char *makeOutFilename(const char *inName, const char *newExt)
{
  const char *dot = strrchr(inName, '.');
  size_t baseLen = (dot != NULL) ? (size_t)(dot - inName) : strlen(inName);
  char *outName = (char *) malloc((baseLen + strlen(newExt) + 1) * sizeof(char));

  if (outName == NULL) {
    fprintf(stderr, "ERROR: Not enough memory for filename.\n");
    exit(1);
  }
  strncpy(outName, inName, baseLen);
  outName[baseLen] = '\0';
  strcat(outName, newExt);

  return outName;
}


/******************************************************************************
 * main ()
 *****************************************************************************/

int main(int argc, char *argv[])
{
    if (argc < 2) {
        usage(argv[0]);
    }
    FILE *fpIn, *fpLadj, *fpEdge;
    Graph *G;
    char *ladjFile, *edgeFile;
    Edge **edges;
    int numE, i;
    /* =====================================================================
     * STEP 1: Read the graph from the input .adj file into an Adjacency Matrix
     *   - Open the input file argv[1] for reading.
     *   - Call GRAPHreadMat(fpIn) to create and populate the Graph ADT.
     *   - Close the input file.
     * ===================================================================== */

    fpIn = fopen(argv[1], "r");
    if (fpIn == NULL) {
        fprintf(stderr, "ERROR: Cannot open input file '%s'.\n", argv[1]);
        exit(2);
    }

    G = GRAPHreadMat(fpIn);
    fclose(fpIn);


    /* =====================================================================
     * STEP 2: Compute and print Graph properties from the Adjacency Matrix
     *   - Print the number of vertices (V) and edges (E).
     *   - Compute and print the graph density using GRAPHdensity(G).
     *   - Compute and print the maximum vertex degree using GRAPHmaxDegree(G).
     * ===================================================================== */

    printf("Graph: %s\n", argv[1]);
    printf("  Vertices (V)   = %d\n", GRAPHnumVertices(G));
    printf("  Edges (E)      = %d\n", GRAPHnumEdges(G));
    printf("  Density        = %.3f\n", GRAPHdensity(G));
    printf("  Maximum Degree = %d\n", GRAPHmaxDegree(G));


    /* =====================================================================
     * STEP 3: Convert Adjacency Matrix to Adjacency List & write .ladj file
     *   - Call GRAPHmatToList(G) to build the adjacency list representation.
     *   - Generate the output filename with extension ".ladj" using
     *     makeOutFilename(argv[1], ".ladj").
     *   - Open the .ladj file for writing, call GRAPHwriteList(G, fpLadj),
     *     close the file, and free the output filename string.
     * ===================================================================== */

    
    GRAPHmatToList(G);

    ladjFile = makeOutFilename(argv[1], ".ladj");
    fpLadj = fopen(ladjFile, "w");
    if (fpLadj == NULL) {
        fprintf(stderr, "ERROR: Cannot open output file '%s'.\n", ladjFile);
        exit(3);
    }
    GRAPHwriteList(G, fpLadj);
    fclose(fpLadj);
    free(ladjFile);
    


    /* =====================================================================
     * STEP 4: Convert Adjacency List to Edge Vector & write .edge file
     *   - Allocate an array of Edge* pointers (Edge **edges) of size
     *     GRAPHnumEdges(G).
     *   - Call GRAPHlistToEdges(edges, G) to fill the edge vector from the
     *     adjacency list representation.
     *   - Generate the output filename with extension ".edge" using
     *     makeOutFilename(argv[1], ".edge").
     *   - Open the .edge file for writing, call GRAPHwriteEdges(...),
     *     and close the file.
     *   - Free each Edge* in edges[] using EDGEdestroy(), then free the
     *     edges array and the output filename string.
     * ===================================================================== */

    
    edges = (Edge **) malloc(GRAPHnumEdges(G) * sizeof(Edge *));
    if (edges == NULL && GRAPHnumEdges(G) > 0) {
        fprintf(stderr, "ERROR: Not enough memory for edge vector.\n");
        exit(1);
    }

    numE = GRAPHlistToEdges(edges, G);

    edgeFile = makeOutFilename(argv[1], ".edge");
    fpEdge = fopen(edgeFile, "w");
    if (fpEdge == NULL) {
        fprintf(stderr, "ERROR: Cannot open output file '%s'.\n", edgeFile);
        exit(3);
    }
    GRAPHwriteEdges(edges, numE, GRAPHnumVertices(G), fpEdge);
    fclose(fpEdge);
    free(edgeFile);

    for (i = 0; i < numE; i++) {
        EDGEdestroy(edges[i]);
    }
    free(edges);
    

    /* =====================================================================
     * STEP 5: Perform Graph Traversal (DFS) & print results
     *   - Allocate an integer array pre[] of size GRAPHnumVertices(G).
     *   - Call GRAPHdfs(G, pre) to traverse the graph and obtain the number
     *     of connected components and the discovery order of each vertex.
     *   - Print the number of connected components and the pre[v] visit order
     *     for each vertex v (0 <= v < V).
     *   - Free the pre[] array.
     * ===================================================================== */

    /*==== TODO (Step 5) ====*/
    int *pre = (int *) malloc(GRAPHnumVertices(G) * sizeof(int));
    int comps, v;
    if (pre == NULL) {
        fprintf(stderr, "ERROR: Not enough memory for pre[].\n");
        exit(1);
    }
    comps = GRAPHdfs(G, pre);
    printf("  Connected components = %d\n", comps);
    

    /* =====================================================================
     * STEP 6: Clean up and free all memory allocated for the Graph ADT
     *   - Call GRAPHdestroy(G).
     * ===================================================================== */

    for (v = 0; v < GRAPHnumVertices(G); v++) {
        printf("  pre[%d] = %d\n", v, pre[v]);
    }
    free(pre);
    GRAPHdestroy(G);

    return 0;
}
