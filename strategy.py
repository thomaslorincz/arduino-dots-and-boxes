def chain_is_open(chain, strat_box_dict):
    '''Checks if a chain is open (all boxes of the chain can be enclosed in
    consecutive moves).

    Arguments:
        chain (set): A set of vertices representing an open chain.

        strat_box_dict (dict): A dictionary that maps strategy graph vertices
            to the edges that surround it.

    Runtime:
        O(n) where n is the number of vertices i nthe strategy graph.

    Returns:
        bool: True if the chain is open, False otherwise.
    '''
    count_of_threes = int()
    count_of_ones = int()
    count_of_zeroes = int()

    # count the number of vertices that have zero, one, or three drawn
    # edges surrounding them.
    for vertex in chain:
        # A strat_box_dict entry with only 1 value means
        # that 3 edges have been drawn (removed from strat_box_dict).
        if len(strat_box_dict[vertex]) == 1:
            count_of_threes += 1
        if len(strat_box_dict[vertex]) == 3:
            count_of_ones += 1
        if len(strat_box_dict[vertex]) == 4:
            count_of_zeroes += 1

    # if this condition is satisfied then the chain is open
    if (count_of_threes - 1) >= (2*count_of_zeroes + count_of_ones):
        return True
    else:
        return False


def take_chain(chain, strat_box_dict):
    ''' Updates requested_edge to be an edge that will enclose at least one box
    in a long chain (3 or more boxes), allowing the computer to play until all
    boxes in the chain are enclosed. Taking long chains is the primary method
    of scoring points using the long chain rule.

    Arguments:
        chain (set): A set of vertices representing an open chain.

        strat_box_dict (dict): A dictionary that maps strategy graph vertices
            to the edges that surround it.

    Runtime:
        O(n) where n is the number of vertices in the strategy graph.

    Returns:
        requested_edge (tuple): The edge to be taken in the chain.

        vertex (int): The vertex that maps to the edge that was taken in
            strat_box_dict.
    '''
    for vertex in chain:
        # If a vertex has 3 edges surrounding it already, the last edge should
        # be taken so that the move completes the box and scores a point.
        if len(strat_box_dict[vertex]) == 1:
            possible_edge = list(strat_box_dict[vertex])
            # Choose the edge.
            requested_edge = possible_edge[0]
            # Let the user know what move is performed.
            print("Taking chain")
            return (requested_edge, vertex)

    # Return None if an edge cannot be found. The AI will then move on to see
    # if other moves can be performed instead.
    return (None, None)

def open_chain(chain, strat_box_dict):
    '''Updates requested_edge to be a move that opens a short chain (2 boxes).
    The AI should only try to open a chain if it is not in control of the game.
    By the long chain rule, the AI should try and take a long chain in its
    last move. If it does not think it can do this, it should try to trick the
    player into taking an open short chain so that the user may have to open a
    long chain for it.

    Arguments:
        chain (set): A set of vertices representing a short chain component of
            the graph that the AI wants to open.

        strat_box_dict (dict): A dictionary that maps strategy graph vertices
            to the edges that surround it.

    Runtime:
        O(n) where n is the number of vertices in the strategy graph.

    Returns:
        requested_edge (tuple): The edge that the AI should take in order to
            open the short chain.
    '''
    for vertex in chain:
        # If the vertex has only two edges surrounding it, then one of the other
        # two edges must be taken to open this chain.
        if len(strat_box_dict[vertex]) == 2:
            possible_edges = list(strat_box_dict[vertex])
            # Arbitrarily choose the edge from the possible edges. Either one
            # will open the chain.
            requested_edge = possible_edges[0]
            # Let the user know what move is performed.
            print("Opening chain")
            return requested_edge
    # Return None if no edge can be found like this. The AI will then move on to
    # take a random edge instead.
    return None

def get_random_edge(game_graph, box_dict):
    '''Returns a random edge in the game graph that is a valid move.

    Arguments:
        game_graph (UndirectedAdjacencyGraph): A graph representation of the
            game board.

        box_dict (dict): A dictionary that maps vertices to the edges that
            surround it. As edges are taken in the game, edges are removes from
            the values of the dictionary.

    Runtime:
        O(n) where n is the number vertices in the game graph.

    Returns:
        chosen_edge (tuple): A valid edge that is yet to be taken in the game.
    '''
    from random import randint # Needed for the move to be pseudorandom

    possible_edges = set()
    # Iterate through all of the vertices of the game:
    for vertex in box_dict:
        # If not all of the edges have been taken surrounding a vertex:
        if len(box_dict[vertex]) > 0:
            # Add the untaken edges to the set of possible edges to take.
            possible_edges.update(box_dict[vertex])

    # Get a randomly generated index.
    edge_index = randint(0, len(possible_edges)-1)
    # Convert the set to a list.
    possible_edges = list(possible_edges)
    # Get the edge at the random index.
    chosen_edge = possible_edges[edge_index]

    print("Random move") # Let the user know what type of move is performed.
    return chosen_edge # Return the edge.
