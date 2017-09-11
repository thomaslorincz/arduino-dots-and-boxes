class UndirectedAdjacencyGraph:
    '''Type to represent undirected graphs using adjacency storage.

    Attributes:
        _vertices (dict): A dictionary mapping a vertex to the other vertices
            that it is connected in an edge with.
    '''
    
    def __init__(self):
        self._vertices = dict()

    def add_vertex(self, v):
        ''' Adds a new vertex with identifier v to the graph.

        Arguments:
            v (int): The vertex identifier to be added.

        Raises:
            RuntimeError: If the vertex was already in the graph.
        '''
        if v not in self._vertices:
            self._vertices[v] = list()
        else:
            raise RuntimeError("Bad argument:"
                               " Vertex {} already in the graph".format(v))

    def is_vertex(self, v):
        '''Checks whether v is a vertex of the graph.

        Arguments:
            v (int): The vertex to be checked.

        Returns:
            bool: True if v is a vertex of the graph, False otherwise.
        '''
        return v in self._vertices

    def add_edge(self, e):
        ''' Adds edge e to the graph.

        Arguments:
            e (tuple): The edge to be added as a tuple. The edge goes from e[0]
                (an int) to e[1] (an int).

        Raises:
            RuntimeError: When one of the vertices in the edge is not a vertex
                in the graph.
        '''
        if not self.is_vertex(e[0]):
            raise RuntimeError("Attempt to create an edge with"
                                  " non-existent vertex: {}".format(e[0]))
        if not self.is_vertex(e[1]):
            raise RuntimeError("Attempt to create an edge with"
                                  "non-existent vertex: {}".format(e[1]))

        if not e[1] in self._vertices[e[0]]:
            self._vertices[e[0]].append(e[1])
        if not e[0] in self._vertices[e[1]]:
            self._vertices[e[1]].append(e[0])

    def is_edge(self, e):
        ''' Checks whether an edge e exists in the graph.

        Arguments:
            e (tuple): The edge to be checked. The edge goes from e[0] (an int)
                to e[1] (an int).

        Returns:
            bool: True if e is an edge of the graph, False otherwise.
        '''
        if (e[1] in self._vertices[e[0]]) or (e[0] in self._vertices[e[1]]):
            return True
        else:
            return False

    def remove_edge(self, e):
        ''' Removes an edge if it exists.

        Arguments:
            e (tuple): The edge to be removed. The edge goes from e[0]
                (an int) to e[1] (an int).
        '''
        if self.is_edge(e):
            self._vertices[e[0]].remove(e[1])
            self._vertices[e[1]].remove(e[0])

    def neighbours(self, v):
        '''Returns the list of vertices that are neighbours to v.

        Arguments:
            v (int): A vertex of the graph.
        '''
        return self._vertices[v]

    def vertices(self):
        '''Returns the set of all vertices in the graph.'''
        return set(self._vertices.keys())

    def clear(self):
        '''Method to clear the game graph for consecutive games played.'''
        self._vertices = dict()

    def is_cyclic_util(self, v, visited, parent):
        '''A recursive util for finding cycles. Used by the is_cyclic method.

        Arguments:
            v (int): A vertex of the strategy graph.

            visited (dict): A dictionary mapping verticess to whether they have
                been visited i nthe search or not.

            parent (int): The root vertex that started the search through the
                the neighbours of v.

        Runtime:
            O(n+m) where n is the number of vertices in the graph and m is the
                number of edges in the graph (this is dfs).

        Returns:
            bool: True if the graph has a cycle in it, False otherwise.
        '''
        visited[v] = True # The root vertex has now been visited.
        # Search all vertices that the root vertex is en edge with.
        for i in self.neighbours(v):
            # If the vertex has not been found yet, recurse.
            if visited[i] == False:
                if (self.is_cyclic_util(i, visited, v)):
                    return True

            # If a vertex finds an already found vertex that is not its parent,
            # there must be a cycle.
            elif parent != i:
                return True

        # If no cycles are detected, return False.
        return False

    def is_cyclic(self):
        '''Method to determine if graph is cyclic.

        Runtime:
            O(n+m) where n is the number of vertices in the graph and m is the
                number of edges in the graph (this is dfs).

        Returns:
            bool: True if the graph has a cycle in it, False otherwise.
        '''
        # Create a dictionary mapping vertices to whether they have been
        # visited yet.
        visited = {v:False for v in self.vertices()}

        for i in self.vertices():
            # If the vertex has not been visited:
            if visited[i] == False:
                # Determine whether the vertex loops to an already seen vertex.
                if (self.is_cyclic_util(i, visited, -1)) == True:
                    return True

        # If no cycles are detected, return False.
        return False
