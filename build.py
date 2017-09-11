def build_game_graph(num_columns, num_rows):
    '''A function that builds the game graph, a graphical representation of the
    dots and edges that are drawn to the Arduino screen. To assist in drawing
    capabilities and AI strategy, dictionaries store knowledge about vertices
    and edges in the graph.

    Arguments:
        num_columns (int): The number of columns that the game board has.

        num_rows (int): The number of rows that the game board has.

    Runtime:
        O(n*m) where n is the number of columns of the game board and m is the
            number of rows of the game board.

    Returns:
        game_graph (UndirectedAdjacencyGraph): An UndirectedAdjacencyGraph with
            vertices that correspond to the dots of the game board. Will be
            used to keep track of lines (edges) drawn throughout game. Vertices
            are labelled starting from 0 increasing left to right, top to
            bottom.

        game_dict (dict): A dictionary that maps vertices of game_graph to
            their coordinate position (x, y) on the game board.

        box_dict (dict): A dictionary that maps the the top left corner of a
            box to the edges that make up the box.

        strat_box_dict (UndirectedAdjacencyGraph): A dictionary that maps the
            vertices of strat_graph to the edges that surround it.
    '''
    from graph import UndirectedAdjacencyGraph

    # The game graph is the board seenand interacted with by the players.
    game_graph = UndirectedAdjacencyGraph()
    # Game dict maps vertices to their coordinates.
    game_dict = dict()
    vertex_number = int()
    for i in range(num_rows+1):
        for j in range(num_columns+1):
            # Add the vertex to the graph.
            game_graph.add_vertex(vertex_number)
            # Add map the vertex to its coordinates.
            game_dict[vertex_number] = (j, i)
            vertex_number += 1

    # box_dict is a dict that maps the position of the top left
    # corner of a box to the edges that make up the box.
    box_dict = dict()
    # strat_box_dict maps vertices in the strat_graph to the game_graph edges
    # that surround it (used by the AI).
    strat_box_dict = dict()
    # Vertex numbering related to the strat_graph
    strat_vertex = int()
    # Vertex numbering related to the game_graph
    game_vertex = int()
    for i in range(num_rows):
        for j in range(num_columns):

            # Top edge of box
            edge1 = (game_vertex, game_vertex+1)
            # Left edge of box
            edge2 = (game_vertex, game_vertex+num_columns+1)
            # Right edge of box
            edge3 = (game_vertex+1, game_vertex+num_columns+2)
            # Bottom edge of box
            edge4 = (game_vertex+num_columns+1, game_vertex+num_columns+2)

            box_dict[game_vertex] = {edge1, edge2, edge3, edge4}
            strat_box_dict[strat_vertex] = {edge1, edge2, edge3, edge4}

            # There is one strategy vertex for every box. There is one game
            # vertex for every dot in the game board.
            strat_vertex += 1
            if j == num_columns-1:
                game_vertex += 2
            else:
                game_vertex += 1

    return (game_graph, game_dict, box_dict, strat_box_dict)

def build_strat_graph(game_dict, num_columns, num_rows):
    '''A function that builds the AI strategy graph, a graphical representation
    of the chains that link columns and rows within the graph. A strategy
    dictionary is also built to assist in the building of another dictionary
    used in AI strategy.

    Arguments:
        game_dict (dict): A dictionary that maps vertices to their x and y
            coordinates.

        num_columns (int): The number of columns that the game board has.

        num_rows (int): The number of rows that the game board has.

    Runtime:
        O(n*m) where n is the number of columns of the game board and m is the
            number of rows in the game board.

    Returns:
        strat_graph (UndirectedAdjacencyGraph): An UndirectedAdjacencyGraph
            with vertices that correspond to the centers of the boxes in the
            game. The initial edges connect all the vertices in a grid pattern.
            Is used to keep track of long chains for AI strategy.

        strat_dict (dict): A dictionary that maps the vertices of strat_graph
            to the edges that they are a part of. Used to build
            edge_intersect_dict.
    '''
    from graph import UndirectedAdjacencyGraph

    strat_graph = UndirectedAdjacencyGraph()

    # Add vertices to strat_graph.
    for v in range(num_columns*num_rows):
        strat_graph.add_vertex(v)

    # Add strat_graph edges and build strat_dict which maps strat_graph vertices
    # to the edges that they are a part of.
    strat_dict = dict()
    vertex_number = int()
    for i in range(num_rows):
        for j in range(num_columns):
            # strat_graph is built from top-left to bottom-right. Therefore,
            # the bottom-right vertex should not add any edges.
            if i == (num_rows - 1) and j == (num_columns - 1):
                pass

            # Bottom vertices should only add an edge to their right.
            elif i == (num_rows - 1):
                # Add the edge to the strategy graph.
                edge = (vertex_number, vertex_number+1)
                strat_graph.add_edge(edge)

                # Add the edge to the set of edges mapped to by the vertex
                if vertex_number not in strat_dict:
                    strat_dict[vertex_number] = set()
                strat_dict[vertex_number].add(edge)

                # Add the edge to the set of edges mapped to by the vertex
                if vertex_number+1 not in strat_dict:
                    strat_dict[vertex_number+1] = set()
                strat_dict[vertex_number+1].add(edge)

            # Right vertices should only add an edge below them.
            elif j == (num_columns - 1):
                # Add the edge to the strategy graph.
                edge = (vertex_number, vertex_number+num_columns)
                strat_graph.add_edge(edge)

                # Add the edge to the set of edges mapped to by the vertex
                if vertex_number not in strat_dict:
                    strat_dict[vertex_number] = set()
                strat_dict[vertex_number].add(edge)

                # Add the edge to the set of edges mapped to by the vertex
                if vertex_number+num_columns not in strat_dict:
                    strat_dict[vertex_number+num_columns] = set()
                strat_dict[vertex_number+num_columns].add(edge)

            # Vertices that are not on the right or bottom edges will add edges
            # to their right and below them.
            else:
                # Add the edges to the strategy graph.
                edge1 = (vertex_number, vertex_number+1)
                edge2 = (vertex_number, vertex_number+num_columns)
                strat_graph.add_edge(edge1)
                strat_graph.add_edge(edge2)

                # Add both edges to the set of edges mappes to by the vertex
                if vertex_number not in strat_dict:
                    strat_dict[vertex_number] = set()
                strat_dict[vertex_number].add(edge1)
                strat_dict[vertex_number].add(edge2)

                # Add the edge to the set of edges mapped to by vertex
                if vertex_number+1 not in strat_dict:
                    strat_dict[vertex_number+1] = set()
                strat_dict[vertex_number+1].add(edge1)

                # Add the edge to the set of edges mapped to by vertex
                if vertex_number+num_columns not in strat_dict:
                    strat_dict[vertex_number+num_columns] = set()
                strat_dict[vertex_number+num_columns].add(edge2)

            vertex_number += 1 # Increment the vertex number

    return (strat_graph, strat_dict)

def build_edge_intersect_dict(strat_dict, num_columns, num_rows):
    '''A function that builds a dictionary that maps strat_graph edges to
    game_graph edges that intersect them. This dictionary helps the AI determine
    what components of the graph are connected. If a drawn line interesects a
    certain chain of strat_graph vertices, the chain may go from a long chain
    to a short chain.

    Arguments:
        strat_dict (dict): A dictionary that maps strat_graph vertices to the
            edges that they are a part of.

        num_columns (int): The number of columns in the game board.

        num_rows (int): The number of rows in the game board.

    Runtime:
        O(n*m) where n is the number of vertices in the strat_graph and m is
            the number edges that the vertex belongs to (at most 4).

    Returns:
        edge_intersect_dict (dict): A dictionary that maps the initial edges of
            strat_graph to the edges in game_graph that intersect them. Used
            for removing edges from strat_graph when lines are drawn that
            intersect them.
    '''
    edge_intersect_dict = dict()
    # Iterate through the vertices of strat_graph
    for vertex, edges in strat_dict.items():
        visited = set() # Keep track of edges that have been seen already

        # A vertex can be a part of at most 4 edges.
        for edge in edges:
            # If the edge has been visited already, contnue.
            if edge in visited:
                continue

            # If the edge is new, map it to a game_graph edge that, when drawn,
            # will interesect it.
            else:
                # If the strat_graph edge is horizontal:
                if (max(edge) - min(edge)) == 1:
                    # Depth accounts for disparity between game vertex numbering
                    # and strat vertex numbering
                    depth = (max(edge) // num_columns)
                    coordinate1 = min(edge) + depth + 1
                    coordinate2 = max(edge) + num_columns + depth + 1

                    # Map a strat edge to the game edge that will interesect it
                    # when it is drawn.
                    edge_intersect_dict[edge] = (coordinate1, coordinate2)

                # if the strat_graph edge is vertical:
                elif (max(edge) - min(edge)) > 1:
                    # Depth accounts for disparity between game vertex numbering
                    # and strat vertex numbering
                    depth = (max(edge) // num_rows)
                    coordinate1 = min(edge) + num_rows + depth
                    coordinate2 = min(edge) + num_rows + depth + 1
                    # Map a strat edge to the game edge that will interesect it
                    # when it is drawn.
                    edge_intersect_dict[edge] = (coordinate1, coordinate2)

                # The strat edge has now been visited
                visited.add(edge)

    return edge_intersect_dict
