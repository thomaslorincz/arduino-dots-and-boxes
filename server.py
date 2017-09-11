def coords_to_vertex(game_dict, coordinates):
    '''Given the coordinates of a vertex, returns its corresponding vertex
    number.

    Arguments:
        game_dict (dict): A dictionary that maps game graph vertices to their
            coordinates.

        coordinates (tuple): The requested x and y coordinates.

    Returns:
        The vertex related to the requested coordinates or -1 if none is found.
    '''
    for vertex_identifier, vertex_coordinates in game_dict.items():
        # If the coordinates match any in the dictionary, return their vertex.
        if coordinates == vertex_coordinates:
            return vertex_identifier
    return -1 # Return -1 if no vertex is found.

def vertex_to_coords(game_dict, vertex):
    '''Given a vertex identifier, returns its coordinates in the game graph.

    Arguments:
        game_dict (dict): A dictionary that maps game graph vertices to their
            coordinates.

        vertex (int): The requested vertex.

    Returns:
        The vertex coordinates or -1 if non are found.
    '''
    for vertex_identifier, vertex_coordinates in game_dict.items():
        # If the vertex matches any in the dictionary, return its coordinates.
        if vertex == vertex_identifier:
            return vertex_coordinates
    return -1 # Return -1 if no coordinates are found.

def draw_line(serial_in, serial_out, requested_edge):
    '''Determines whether requested_edge is a valid line to draw. If it is, the
    edge information is sent to the client to draw.

    Arguments:
        serial_in: Serial port input channel.

        serial_out: Serial port output channel.

        requested_edge (tuple): A requested game graph edge to draw.

    Runtime:
        O(n) where n is the number of edges in the strategy graph.

    Returns:
        -1 if there is an error, 0 if no line is drawn (invalid line), or 1 if
            the line is valid and sent to the client for drawing.
    '''
    # game_graph is a graph representation of the game board. game_dict is a
    # dictionary that maps vertices to their x and y coordinates. box_dict is a
    # dictionary that maps game vertcies to the edges that box them in.
    global game_graph, game_dict, box_dict

    # strat_graph is a graph representation of the inner chains of the game
    # graph. edge_intersect_dict is a dictionary mapping strategy graph edges
    # tothe game graph edges that intersect them.
    global strat_graph, edge_intersect_dict

    # The number of total moves in the game, the present player turn (1 or 2),
    # and the turn that the computer plays on (1 or 2).
    global num_moves, game_move, computer_move

    # If the line has already been drawn or coordinates are the same, do not
    # draw the line. The line request is invalid.
    if game_graph.is_edge(requested_edge) or \
        requested_edge[0] == requested_edge[1]:

        # tell client that the line request is invalid.
        send_msg_to_client(serial_out, "L 1")

        # Get client acknowledgement. Return -1 if there is communication error.
        client_acknowledged(serial_in)
        if error: return -1

        return 0 # Return 0 because a line was not drawn.

    # If line has not been drawn before, process the drawing of the line.
    num_moves -= 1 # Decrement number of total moves
    game_graph.add_edge(requested_edge) # Add the edge to the game_graph

    # This added line may break a chain. If it does, remove the intersected edge
    # in the strat_graph.
    # Tuples have order so the reverse of the request needs to be checked.
    rev_requested_edge = (requested_edge[1], requested_edge[0])
    for edge, intersecting_edge in edge_intersect_dict.items():
        # If the requested edge intersects a strategy graph edge:
        if requested_edge == intersecting_edge:
            # Remove the edge from the strategy graph
            strat_graph.remove_edge(edge)
            # Keep track that the strategy edge is now intersected.
            edge_intersect_dict[edge] = None

        # If the reverse requested edge interesects a strategy graph edge:
        elif rev_requested_edge == intersecting_edge:
            # Remove the edge from the strategy graph
            strat_graph.remove_edge(edge)
            # Keep track that the strategy edge is now interesected.
            edge_intersect_dict[edge] = None

    # If the line is valid and it is a computer turn:
    if computer_move == game_move:
        # Get the start vertex of the computer-chosen edge.
        start = vertex_to_coords(game_dict, min(requested_edge))

        # Send the x-coordinate of start vertex to the client.
        send_msg_to_client(serial_out, "E {}".format(start[0]))
        client_acknowledged(serial_in) # Get client acknowledgement.
        if error: return -1 # Return -1 if there is communication error.

        # Send the y-coordinate of the start vertex to the client.
        send_msg_to_client(serial_out, "E {}".format(start[1]))
        client_acknowledged(serial_in) # Get client acknowledgement.
        if error: return -1 # Return -1 if there is communication error.

        # Get the end vertex of the computer-chosen edge.
        end = vertex_to_coords(game_dict, max(requested_edge))

        # Send the x-coordinate of the end vertex to the client.
        send_msg_to_client(serial_out, "E {}".format(end[0]))
        client_acknowledged(serial_in) # Get client acknowledgement.
        if error: return -1 # Return -1 if there is communication error.

        # Send the y-coordinate of the end vertex to the client.
        send_msg_to_client(serial_out, "E {}".format(end[1]))
        client_acknowledged(serial_in) # Get client acknowledgement.
        if error: return -1 # Return -1 if there is communication error.

    # The line is valid and it is a human turn:
    else:
        # Tell client that a line was drawn
        send_msg_to_client(serial_out, "L 0")
        client_acknowledged(serial_in) # Get client acknowledgement.
        if error: return -1 # Return -1 if there is communication error.

    return 1 # Return 1 because a line was drawn successfully.

def get_boxes(serial_in, serial_out, requested_edge):
    '''The requested_edge is removed from box_dict and strat_box_dict. If the
    edge is the last one needed to close one or two boxes, the information of
    these closed boxes is returned so that it may be sent to the client for
    drawing.

    Arguments:
        serial_in: Serial port input channel.

        serial_out: Serial port output channel.

        requested_edge (tuple): A requested game graph edge to draw.

    Runtime:
        O(n) where n is the number of vertices in the game graph.

    Returns:
        boxes (list): List of closed boxes (identified by an integer).
        len(boxes) (int): The number of closed boxes.
    '''
    # A dictionary mapping game vertices to the edges that box them in.
    global box_dict

    # A dictionary mapping strategy vertices to the edges that box them in.
    global strat_box_dict

    boxes = list() # A list of boxes to draw
    # Tuples have order so the reverse edge needs to be checked as well
    rev_requested_edge = (requested_edge[1], requested_edge[0])
    for box in box_dict:

        # If the requested edge is in the box dictionary, remove it.
        if requested_edge in box_dict[box]:
            box_dict[box].remove(requested_edge)

            # If the requested edge completes the box, put it in a list of
            # boxes to draw.
            if len(box_dict[box]) == 0:
                boxes.append(box)

        # Check the reverse requested edge similarly.
        elif rev_requested_edge in box_dict[box]:
            box_dict[box].remove(rev_requested_edge)

            # If the requested edge completes the box, put it in a list of
            # boxes to draw.
            if len(box_dict[box]) == 0:
                boxes.append(box)

    for box in strat_box_dict:
        # If the requested edge is in the box dictionary, remove it.
        if requested_edge in strat_box_dict[box]:
            strat_box_dict[box].remove(requested_edge)

        # Check the reverse requested edge similarly.
        elif rev_requested_edge in strat_box_dict[box]:
            strat_box_dict[box].remove(rev_requested_edge)

    # Return a list of boxes that were closed and the number of boxes that were
    # closed.
    return (boxes, len(boxes))

def process_line(serial_in, serial_out, requested_edge):
    '''Processes a requested edge by the human or computer. Calls draw_line to
    check if requested_edge is valid. Calls get_boxes to check if
    requested_edge causes any boxes to become enclosed. Send the information
    about closed boxes and whether the game is over to the client.

    Arguments:
        serial_in: Serial port input channel.

        serial_out: Serial port output channel.

        requested_edge (tuple): A requested game graph edge to draw.

    Runtime:
        O(n) where n is the number of closed boxes (max 2). However, calls
            draw_line and get_boxes which have their own runtimes.

    Returns:
        game_over (bool): Notifies whether the game is over.

        error (bool): Notifies whether there is a communication error.
    '''
    # game_over boolean notifies whether the game is over. error boolean
    # notifies whether there is a communication error.
    global game_over, error

    # Game dictionary mapping vertices to their coordinates.
    global game_dict

    # The current move number and the computer's move number
    global game_move, computer_move

    # Find out if a line was drawn (if the requested edge was a valid move)
    line_drawn = draw_line(serial_in, serial_out, requested_edge)
    # If a line was not drawn, return (game_over = False, error = False).
    if line_drawn < 1:
        return (game_over, error)

    # Find out if and how many boxes were closed by the last move.
    (boxes, num_boxes) = get_boxes(serial_in, serial_out, requested_edge)

    # Send the number of closed boxes to the client.
    send_msg_to_client(serial_out, "N {}".format(num_boxes))
    # If the client does not acknowledge, reset.
    client_acknowledged(serial_in)
    if error:
        return (game_over, error)

    # Send the coordinates of every box to draw to the client.
    for i in range(num_boxes):
        # Send the x-coordinate of the game vertex corresponding to the box to
        # draw to the client
        send_msg_to_client(serial_out, "B {}"\
            .format(vertex_to_coords(game_dict, boxes[i])[0]))

        # If the client does not acknowledge, reset.
        client_acknowledged(serial_in)
        if error: return (game_over, error)

        # Send the y-coordinate of the game vertex corresponding to the box to
        # draw to the client
        send_msg_to_client(serial_out, "B {}"\
            .format(vertex_to_coords(game_dict, boxes[i])[1]))

        # If the client does not acknowledge, reset.
        client_acknowledged(serial_in)
        if error: return (game_over, error)

    # If no points were scored, the player turn is switched.
    if num_boxes == 0:
        if game_move == 1:
            game_move = 2
        else:
            game_move = 1

    # If all possible moves have been played, the game is over.
    if (num_moves == 0):
        game_over = True # The game is over.

        # Send that the game is over to the client.
        send_msg_to_client(serial_out, "O 1")

        # The game will reset whether the client acknowledges or not.
        client_acknowledged(serial_in)
        # Client will send an extra 'A' to ensure that the player has clicked
        # the joystick to play again.
        client_acknowledged(serial_in)
    else:
        game_over = False # The game is not over.

        # Send that the game is not over to the client.
        send_msg_to_client(serial_out, "O 0")

        # If the client does not acknowledge, reset.
        client_acknowledged(serial_in)
        if error: return (game_over, error)

    return (game_over, error)

def computer_turn(serial_in, serial_out):
    '''A computer turn uses the long chain rule to determine what move to
    determine what line to draw.

    Long chain rule:
        - If a chain of three or more boxes (long) can be scored, take them.
        - If a chain of two boxes (short) can be scored, only take these chains
            if the computer has control over the game. Control in dots and
            boxes is determined by the player's move order and the number of
            long chains on the board.
        - If the computer does not have control, attempt to trick the user into
            opening a new long chain by not taking a short chain and instead
            baiting the user by making the short chain closeable.
        - If there is not enough chain information, play a random move.

    Arguments:
        serial_in: Serial port input channel.

        serial_out: Serial port output channel.

    Runtime:
        O(n*(n+m)) where n is the number of vertices in the strat_graph and m
            is the number of edges in the strat_graph (bounded by the
            get_components function in traversal.py).

    Returns:
        An integer (-1, 0, or 1) depending on whether process_line returns an
            error, no line drawn, or that a line was drawn.
    '''
    # game_graph is a graph representation of the game board. box_dict is a
    # dictionary that maps game vertcies to the edges that box them in.
    global game_graph, box_dict

    # strat_graph is graph representation of the chains of connected boxes in
    # the game board. stored_chain is a chain that the computer may be in the
    # process of taking. edge_intersect_dict is dictionary mapping strategy
    # graph edges to the game graph edges that interesect them.
    # computer_is_first is whether the computer played first or not.
    global strat_graph, stored_chain, edge_intersect_dict, computer_is_first
    # strat_box_dict maps strategy graph vertices to the edges that box them in.
    global strat_box_dict

    # Number of game columns and rows.
    global num_columns, num_rows

    # Used to visualize the components that the AI is working with.
    global debug

    # The number of dots in the game is used in addition to number of long
    # chains determining which player is in control.
    num_dots = ((num_columns + 1) * (num_rows + 1))

    # If a series of moves to score many boxes is present, finish the series and
    # score every box possible.
    if len(stored_chain) > 0:
        # Use take chain to get a suitable edge and a chosen vertex of the
        # stored chain.
        (requested_edge, chosen) = take_chain(stored_chain, strat_box_dict)
        if not chosen is None:
            stored_chain.remove(chosen)
        else:
            stored_chain = list()
        # If the requeste edge is not None, process it.
        if not requested_edge is None:
            return process_line(serial_in, serial_out, requested_edge)

    # Get all the dijoint components of the strat_graph
    components = get_components(strat_graph)
    if debug: print(components) # Visualize this

    # Create a list of subgraphs of the strat_graph
    subgraph_list = list()
    for vertex_set in components:
        # Each component is converted to a subgraph of the strat_graph
        subgraph = UndirectedAdjacencyGraph()

        # If there is a single vertex, do not factor into strategy.
        if len(vertex_set) == 1:
            continue

        # Add all of the vertices of the component into a new subgaph of the
        # main graph.
        for v in vertex_set:
            if not subgraph.is_vertex(v):
                subgraph.add_vertex(v)
        subgraph_list.append(subgraph)

        # If there is nothing obstructing the a strat_edge that relates to the
        # vertics of the subgaph, add the edge to the subgraph.
        for edge, intersect_edge in edge_intersect_dict.items():
            if not intersect_edge is None:
                if subgraph.is_vertex(edge[0]) and subgraph.is_vertex(edge[1]):
                    subgraph.add_edge(edge)

    long_chains = list() # A list of chains of 3 or more boxes
    short_chains = list() # A list of chain of 2 boxes
    for subgraph in subgraph_list:
        # If the subgraph is cyclic, it cannot be a chain.
        if subgraph.is_cyclic():
            if debug: print("Cyclic:")
            if debug: print(subgraph.vertices())
            continue
        else:
            if debug: print("Not cyclic:")
            if debug: print(subgraph.vertices())
            # Put long chains in one list, and short chains in another.
            if len(subgraph.vertices()) >= 3:
                long_chains.append({v for v in subgraph.vertices()})
            else:
                short_chains.append({v for v in subgraph.vertices()})

    # If a long chain has been opened, take it.
    if len(long_chains) > 0:
        # Sort the long chains from longest to shortest.
        sorted_long_chains = sorted(long_chains, key=len, reverse=True)

        # If there is more than one long chain, try to take the longest.
        for chain in sorted_long_chains:
            # If the chain is open, take it without question.
            if chain_is_open(chain, strat_box_dict):
                # Store the chain so that the AI takes all of it.
                stored_chain = chain
                # Score one of the boxes of the chain.
                (requested_edge, chosen) = \
                    take_chain(stored_chain, strat_box_dict)

                # Remove the chosen vertex from the chain being taken.
                if not chosen is None:
                    stored_chain.remove(chosen)
                else:
                    stored_chain = list()
                # If the requested_edge is not None, process it for drawing.
                if not requested_edge is None:
                    return process_line(serial_in, serial_out, requested_edge)

    # If a long chain is not open, determine whether the computer has control
    # over the game.
    if (num_dots + len(long_chains)) % 2 == 0 and computer_is_first:
        # The computer is in control. It should wait for a long chain to be
        # opened.
        computer_has_control = True
    elif (num_dots + len(long_chains)) % 2 != 0 and not computer_is_first:
        # The computer is in control. It should wait for a long chain to be
        # opened.
        computer_has_control = True
    else:
        # The human has control. The computer needs to trick the human into
        # losing control by baiting short chains.
        computer_has_control = False

    # If the computer has control over the game, play on open short chains or
    # play a random edge that will not ruin control.
    if computer_has_control:
        for chain in short_chains:
            # If a short chain is open and the computer has control, there is
            # no problem with taking a short chain.
            if chain_is_open(chain, strat_box_dict):
                # Store the chain so that the AI takes all of it.
                stored_chain = chain
                # Score one of the boxes of the chain.
                (requested_edge, chosen) = \
                    take_chain(stored_chain, strat_box_dict)

                # Remove the chosen vertex from the chain being taken.
                if not chosen is None:
                    stored_chain.remove(chosen)
                else:
                    stored_chain = list()
                # If the requested_edge is not None, process it for drawing.
                if not requested_edge is None:
                    return process_line(serial_in, serial_out, requested_edge)

    # If the computer does not have control, try to bait the user by
    # making a short chain closeable. The goal behind this is to make
    # the user have to play a move that makes a long chain closeable.
    else:
        for chain in short_chains:
            # Make sure the chain is not open, and then bait the player by
            # opening it.
            if not chain_is_open(chain, strat_box_dict):
                requested_edge = open_chain(stored_chain, strat_box_dict)
                # If the requested_edge is not None, process the edge for
                # drawing.
                if not requested_edge is None:
                    return process_line(serial_in, serial_out, requested_edge)

    # If there are not suitable chains to play on, choose a random edge to play.
    # Guaranteed to return an edge.
    requested_edge = get_random_edge(game_graph, box_dict)

    # Process the random edge for drawing.
    return process_line(serial_in, serial_out, requested_edge)

def human_turn(serial_in, serial_out):
    '''A human turn relies on a request from the client. When a request is
    received, the edge is validated and this information is sent to the
    client using process_line.

    Arguments:
        serial_in: Serial port input channel.

        serial_out: Serial port output channel.

    Runtime:
        O(1) because a human turn only sends information to the client.

    Returns:
        An integer (-1, 0, or 1) depending on whether process_line returns an
            error, no line drawn, or that a line was drawn.
    '''
    # game_graph is a graph representation of the game board. game_dict is a
    # dictionary that maps vertices to their x and y coordinates. box_dict is a
    # dictionary that maps game vertcies to the edges that box them in.
    global game_graph, game_dict, box_dict

    # The number of total moves in the game.
    global num_moves

    # Get a request message from the client.
    msg = receive_msg_from_client(serial_in).split()
    log_msg(msg)

    # If the request is not of the form "R # # # #", then it is invalid.
    if len(msg) != 5 or msg[0] != 'R':
        print("Invalid request received.")
        return 0

    # Map the coordinates to their vertex.
    start_vertex = coords_to_vertex(game_dict, (int(msg[1]), int(msg[2])))
    # Tuples have order, so if the edge is -1, try the reverse tuple.
    if start_vertex == -1:
        start_vertex = coords_to_vertex(game_dict, (int(msg[2]), int(msg[1])))

    # Map the coordinates to their vertex.
    end_vertex = coords_to_vertex(game_dict, (int(msg[3]), int(msg[4])))
    # Tuples have order, so if the edge is -1, try the reverse tuple.
    if end_vertex == -1:
        end_vertex = coords_to_vertex(game_dict, (int(msg[4]), int(msg[3])))

    # The requested edge is stored as a tuple of the two integer vertices.
    requested_edge = (start_vertex, end_vertex)

    # Process the requested edge, ensuring it is not an invalid operation.
    return process_line(serial_in, serial_out, requested_edge)

def client_acknowledged(serial_in):
    '''A function to handle client acknowledgements. If an acknowledgement is
    not properly read, both the client and server should reset to the start
    of the game. Sets a global boolean ("error") based on whether there was an
    error in communication or not.
    '''
    global error # A global boolean notifying functions about errors.

    # Receive a message from the client.
    msg = receive_msg_from_client(serial_in).rstrip()
    log_msg(msg)

    # If the server does receive proper acknowledgement:
    if len(msg) > 1 or msg[0] != 'A':
        # There was a timeout if a 'T' is received.
        if msg[0] == 'T':
            print("Client took too long to respond.")
            print("Resetting...")

        # There was an unexpected character.
        else:
            print("Client sent unexpected character.")
            print("Client sent {}.".format(msg[0]))
            print("Resetting...")
        error = True

    # Proper acknowledgement was received.
    else:
        error = False

def protocol(serial_in, serial_out):
    '''Allows the python server to communicate with the arduino using
    cs_message. The protocol begins by getting user-inputted information about
    the type and size of game to be played. Once this information is
    communicated to the client, the protocol will loop through the human/human
    or human/computer turns of the game. Protocol runs indefinitely.

    Arguments:
        serial_in: Serial port input channel.

        serial-out: Serial port output channel.

    Runtime:
        O(n*m) where n is the number of columns of the game board and m is the
            number of rows in the game board (bounded by the build.py functions
            that are sued to build the scaled game board). Building only
            happens once, the cycling of turns is bounded by a lower runtimes.

    Returns:
        Runs indefinitely.
    '''
    # game_over notifies whether the game is over. error notifies whether there
    # is an error.
    global game_over, error

    # game_graph is a graph representation of the game board. game_dict is a
    # dictionary that maps vertices to their x and y coordinates. box_dict is a
    # dictionary that maps game vertcies to the edges that box them in.
    global game_graph, game_dict, box_dict

    # strat_graph is graph representation of the chains of connected boxes in
    # the game board. strat_dict is a dictionary that maps strat_graph vertices
    # to the edges they are a part of. strat_box_dict maps strategy graph
    # vertices to the edges that box them in. computer_is_first is whether the
    # computer played first or not.
    global strat_graph, strat_dict, strat_box_dict, computer_is_first
    # edge_intersect_dict is dictionary mapping strategy graph edges to the
    # game graph edges that interesect them.
    global edge_intersect_dict

    # Number of game board columns and rows and the number of total moves in
    # the game.
    global num_columns, num_rows, num_moves

    # The current turn in the game and the computer's turn in the game.
    global game_move, computer_move

    # Infinite game loop
    while True:
        print("Welcome to Ardunio Dots and Boxes.")
        # Reset game state variables.
        game_over = False
        error = False
        computer_move = 0

        # Game type prompt
        while True:
            # Get the number of human players.
            game_type = int()
            print("How many human players? (1-2)")
            num_humans = input()

            # If the number of humans is invalid, ask for it again.
            if not num_humans.isdigit():
                print("Invalid number of players selected. Try again.")
                continue

            # If there is 1 human player, it is a human versus computer game.
            if int(num_humans) == 1:
                print("1 vs Computer game chosen.")
                game_type = 0
                send_msg_to_client(serial_out, "G {}".format(game_type))
                client_acknowledged(serial_in) # Will set error if needed.
                break

            # If there is 2 humans players, it is a human versus human game.
            elif int(num_humans) == 2:
                print("1 vs 1 game chosen.")
                game_type = 1
                send_msg_to_client(serial_out, "G {}".format(game_type))
                client_acknowledged(serial_in) # Will set error if needed.
                break

            # Else, the input was an invalid number, try again.
            else:
                print("Invalid number of players selected. Try again.")
                continue

        if error: continue # Reset to beginning if there was an error.

        # Number of columns prompt
        while True:
            # Get the number of game board columns
            print("How many columns? (1-7)")
            num_columns = input()

            # If the number of columns is invalid, try again.
            if not num_columns.isdigit() or int(num_columns) < 1 \
                or int(num_columns) > 7:
                print("Invalid number of columns selected. Try again.")
                continue

            # If the number of columns is valid, send to client.
            else:
                num_columns = int(num_columns)
                print("The board will have {} columns.".format(num_columns))
                send_msg_to_client(serial_out, "C {}".format(num_columns))
                client_acknowledged(serial_in) # Will set error if needed.
                break

        if error: continue # Reset to beginning if there was an error.

        # Number of rows prompt
        while True:
            # Get the number of game board rows.
            print("How many rows? (1-8)")
            num_rows = input()

            # If the number of rows is invalid, try again.
            if not num_rows.isdigit() or int(num_rows) < 1 or int(num_rows) > 8:
                print("Invalid number of rows selected. Try again.")
                continue

            # If the number of rows is valid, send to client.
            else:
                num_rows = int(num_rows)
                print("The board will have {} rows.".format(num_rows))
                send_msg_to_client(serial_out, "R {}".format(num_rows))
                client_acknowledged(serial_in) # Will set error if needed.
                break

        if error: continue # Reset to beginning if there was an error.

        # Build the game board graph and related vertex/edge information.
        (game_graph, game_dict, box_dict, strat_box_dict) = \
            build_game_graph(num_columns, num_rows)

        # Build the graph used by the AI in its strategy and related
        # vertex/edge information.
        (strat_graph, strat_dict) = \
            build_strat_graph(game_dict, num_columns, num_rows)

        # Build a dictionary that maps AI graph edges to the game graph edges
        # that intersect over them.
        edge_intersect_dict = \
            build_edge_intersect_dict(strat_dict, num_columns, num_rows)

        num_dots = ((num_columns + 1) * (num_rows + 1))
        num_boxes = (num_columns  * num_rows)
        # The total number of move in the game (determines end of game).
        num_moves = num_dots + num_boxes - 1

        # The game starts with the first move.
        game_move = 1

        # If the game is human versus computer
        if game_type == 0:
            # Determining who will go first.
            while True:
                # Get who goes first.
                print("Who will go first? (H|C)")
                msg = input().rstrip()
                log_msg(msg)

                # If the human goes first, send to client.
                if len(msg) == 1 and (msg[0] == 'H' or msg[0] == 'h'):
                    print("The human will go first.")
                    computer_is_first = False # Computer plays second.
                    computer_move = 2 # Computer plays second.
                    send_msg_to_client(serial_out, "F 2")
                    client_acknowledged(serial_in) # Will set error if needed.
                    break

                # If the computer goes first, send to client.
                elif len(msg) == 1 and (msg[0] == "C" or msg[0] == 'c'):
                    print("The computer will go first.")
                    computer_is_first = True # Computer plays first.
                    computer_move = 1 # Computer plays first.
                    send_msg_to_client(serial_out, "F 1")
                    client_acknowledged(serial_in) # Will set error if needed.
                    break

                # If the input is invalid, try again.
                else:
                    print("Incorrect character. Please try again.")
                    continue

            if error: continue # Reset to beginning if there was an error.

            # If no error yet, notify that the human/computer game has started.
            print("Game start!")

            # Turn sequence loop.
            while True:
                # If it is the computer's move, process it.
                if computer_move == game_move:
                    (game_over, error) = computer_turn(serial_in, serial_out)
                    if game_over:
                        print("Game is finished. Resetting.")
                        break
                    if error: continue # Reset to start if there was an error.
                # If it is the human's move, process it.
                else:
                    (game_over, error) = human_turn(serial_in, serial_out)
                    if game_over:
                        print("Game is finished. Resetting.")
                        break
                    if error: continue # Reset to start if there was an error.

        # If the game is human versus human
        elif game_type == 1:
            # Notify that the human/human game has started.
            print("Game start!")

            # Turn sequence loop.
            while True:
                # Continuously process human moves.
                (game_over, error) = human_turn(serial_in, serial_out)
                if game_over:
                    print("Game is finished. Resetting.")
                    break
                if error: continue # Reset to start if there was an error.

if __name__ == "__main__":
    '''server.py is designed to run on its own from the command line. When it is
    run, the edmonton game_graph will be read, an argparser will be defined, and
    the protocol function will run to communicate with the arduino.
    '''
    from build import * # Needed to build graphs and graph information dicts
    from cs_message import * # Needed for server/client communication
    from graph import UndirectedAdjacencyGraph # Needed for game boards
    from strategy import * # Needed for AI's strategy
    import sys # Needed for stdin/stdout communication
    from traversal import * # Needed to traverse the strategy graph

    # Game state variables
    game_over = bool() # Keeps track of whether the game is over.
    error = bool() # Keeps track of whether there is a communication error.

    # Game graph information
    game_graph = UndirectedAdjacencyGraph() # Graph representation of game board
    # Dictionary mapping vertices to their x and y coordinates.
    game_dict = dict()
    # Dictioanry mapping vertices to the edges that surround them.
    box_dict = dict()

    # Strategy (AI) graph information
    # Graph representation of connected box chains.
    strat_graph = UndirectedAdjacencyGraph()
    # Dictionary mapping strategy vertices to the edges that they are a part of.
    strat_dict = dict()
    # Dictionary mapping strategy vertices to the edges that box them in.
    strat_box_dict = dict()
    # Keeps track of a chain of boxes that the AI is in the process of taking.
    stored_chain = list()
    # Keeps track of whether the computer played first in the game.
    computer_is_first = bool()

    # Game dimension variables
    num_columns = int() # Number of columns in the game.
    num_rows = int() # Number of rows in the game.
    num_moves = int() # Number of total moves in the game.

    # Variables to determine whose move it is
    game_move = int() # The current turn (1 or 2)
    computer_move = int() # The turn that the computer moves on (1 or 2)

    import argparse
    parser = argparse.ArgumentParser(
        description='Client-server message test.',
        formatter_class=argparse.RawTextHelpFormatter)

    # Debugging is false unless specified.
    parser.add_argument("-d",
        help="Debug on",
        action="store_true",
        dest="debug")

    # Serial port is /dev/ttyACM0 unless specified.
    parser.add_argument("-s",
        help="Set serial port for protocol",
        nargs="?",
        type=str,
        dest="serial_port_name",
        default="/dev/ttyACM0")

    args = parser.parse_args()

    # Only log messages in debugging mode.
    debug = args.debug
    set_logging(debug)

    # this imports serial, and provides a useful wrapper around it
    import textserial

    serial_port_name = args.serial_port_name;
    log_msg("Opening serial port: {}".format(serial_port_name))

    # Open up the connection [bits/second]
    baudrate = 9600

    # The with statement ensures that if things go bad, then ser will still be
    # closed properly.
    with textserial.TextSerial(
        serial_port_name, baudrate, errors="ignore", newline=None) as ser:
        protocol(ser, ser)
