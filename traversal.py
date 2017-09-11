def breadth_first_search(g, v):
    '''Discovers all vertices in graph g reachable from vertex v and returns
    the search graph. Paths on the search graph are guaranteed to follow
    shortest paths from v.

    Arguments:
        g (UndirectedAdjacencyGraph): Graph to search in.

        v (int): Vertex of the graph where the search starts.

    Runtime:
        O(n + m) where n is the number of vertices in the graph and m is the
            number of edges in the graph.

    Returns:
        reached (frozenset): A frozenset of the discovered vertices in the
            graph.
    '''
    import queue

    todolist = queue.deque([v])  # todolist also stores "from where"
    reached = {v}
    # While todolist is not empty:
    while todolist:
        u = todolist.popleft()
        for w in g.neighbours(u):
            # If the vertex has not been reached yet:
            if w not in reached:
                reached.add(w)  # w has been reached
                todolist.append(w) # w is now in todolist

    return frozenset(reached)

def get_components(g):
    '''Finds and returns all of the components of graph g.

    Arguments:
        g (UndirectedAdjacencyGraph): The game graph from which components are
            counted.

    Runtime:
        O(n*(n+m)) where n is the number of vertices in the graph and m is the
            number of edges in the graph.

    Returns:
        component_set (set): List of frozensets that contain vertices reachable
            from each vertex of the graph.
    '''
    component_set = set()
    for v in g.vertices():
        # Conduct a breadth first search to find the component that v is in.
        component = breadth_first_search(g, v)

        # If the component has already been found, continue.
        if component in component_set:
            continue

        # Else, add the component to the set of all components of the graph.
        else:
            component_set.add(component)

    return component_set
