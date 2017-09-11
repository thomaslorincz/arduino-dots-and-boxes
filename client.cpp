#include <Arduino.h>
#include <Adafruit_ST7735.h>

#include "serial_handling.h"

// Global constants
static const uint8_t TFT_CS = 6; // TFT pin
static const uint8_t TFT_DC = 7; // TFT pin
static const uint8_t TFT_RST = 8; // TFT pin
// Arduino analog input pin for the horizontal on the joystick.
static const uint8_t JOY_PIN_X = 1;
// Arduino analog input pin for the vertical on the joystick.
static const uint8_t JOY_PIN_Y = 0;
// Digital pin for the joystick button on the Arduino.
static const uint8_t JOY_PIN_BUTTON = 4;
// The deadzone for joystick input movement.
static const uint8_t JOY_DEADZONE = 64;
// Screen constants (can be set based on different screen dimensions)
static const uint8_t SCREEN_WIDTH = 128; // Drawable width
static const uint8_t SCREEN_HEIGHT = 148; // Drawable height
static const uint8_t MAX_NUM_COLUMNS = 7; // Max game columns
static const uint8_t MAX_NUM_ROWS = 8; // Max game rows
// Define a shortened word for the TFT colours.
static const uint16_t BLACK = ST7735_BLACK;
static const uint16_t GREEN = ST7735_GREEN;
static const uint16_t BLUE = ST7735_BLUE;
static const uint16_t WHITE = ST7735_WHITE;
static const uint16_t RED = ST7735_RED;

// Globally accessible screen
Adafruit_ST7735 TFT = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);

// Global variables
int8_t GAME_TYPE = -1; // The type of game (1v1 or 1vCPU)
int8_t NUM_COLUMNS = -1; // The number of columns in the graph.
int8_t NUM_ROWS = -1; // The number of rows in the graph.
uint8_t COL_WIDTH = 0; // x-spacing of drawn dots in the graph.
uint8_t ROW_HEIGHT = 0; // y-spacing of drawn dots in the graph.
uint8_t DOT_SIZE = 0; // The size of the drawn dot representing a vertex.
uint8_t X_MARGIN = 0; // 2.5% of the screen width as left and right margins.
uint8_t Y_MARGIN = 0; // 2.5% of the screen height as top and bottom margins.
uint8_t PREV_X = 0; // The previous cursor x position.
uint8_t PREV_Y = 0; // The previous cursor y position.
bool UPDATE_CURSOR = true; // Used to determine whether a redraw is needed.
bool JOY_STATE = true; // Joystick moving availability state.
uint8_t PLAYER_TURN = 1; // Player 1 goes first.
uint8_t PLAYER1_SCORE = 0; // Player 1 score set to zero initially.
uint8_t PLAYER2_SCORE = 0; // Player 2 score set to zero initially.
int8_t COMPUTER_TURN = 0; // The computer's turn.
bool PLAY_AGAIN = false; // Determines whether a player plays again.
bool RESET = true; // A RESET state if there is a communication error.
uint16_t PLAYER_COLOUR = 0; // The player colour (BLUE = 1, RED = 2)

// A structure to house a pair of 8-bit coordinates.
struct XY8 {
    uint8_t x;
    uint8_t y;
    XY8(uint8_t p_x=0, uint8_t p_y=0) : x(p_x), y(p_y) {}
};

// Start point and end point states.
typedef enum {
    RS_WAIT_FOR_START = 0,
    RS_WAIT_FOR_END
} RequestState;

// Initially waiting for start point.
RequestState REQUEST_STATE = RS_WAIT_FOR_START;

// Start and end vertex coordinates for a requested edge.
XY8 start = XY8(0,0);
XY8 end = XY8(0,0);

// The screen coordinates for start and end vertices of a requested edge.
XY8 draw_start = XY8(0,0);
XY8 draw_end = XY8(0,0);

// Forward function declarations
void initialize_screen();
void initialize_joystick();
void render_map();
void status_msg(char *msg);
uint8_t process_joystick(int8_t *dx, int8_t *dy);
bool line_request_valid(uint8_t x_0, uint8_t y_0, uint8_t x_1, uint8_t y_1);
void invalid_request();
void game_over_screen();
void draw_box(uint16_t PLAYER_COLOUR, uint8_t num_closed_boxes);
void draw_line();
void send_request_to_server();
void game_setup();
void process_drawing();

/*
    Initial game setup.
    Runs in O(1)
*/
void setup() {
    Serial.begin(9600); // Begin serial port communication.
    Serial.flush(); // Flush leftover bits
    loop(); // Start the game loop
}

/*
    Client side game loop. Handles protocol for both human/human games and
    human/computer games.
    Game setup bounded by render_map runtime: O(n*m) where n is the number of
    columns+1 and m is the number of rows+1 (runs only at start of game and if
    there is an error).
    Game protocol bounded by draw_box runtime: O(n) wehre n is the number of
    closed boxes (max 2). Runs until game is over.
*/
void loop() {
    // If a RESET has been set, restart from the beginning and loop through the
    // setup until all values are valid.
    while (RESET) {
        RESET = false;
        game_setup();
    }

    // Protocol loop. Will break if there are any server/client communication
    // errors.
    while (true) {
        // Joystick displacement.
        int8_t dx = 0;
        int8_t dy = 0;
        // Process joystick input.
        uint8_t select_button_event = process_joystick(&dx, &dy);

        PLAY_AGAIN = false;

        // If it is the computer's turn:
        if (PLAYER_TURN == COMPUTER_TURN) {
            // Get the x-coordinate of the first edge to draw.
            int8_t start_x = srv_get_number('E');
            if (start_x == -1) {
                // If error, RESET.
                RESET = true;
                break;
            }
            // Get the y-coordinate of the first edge to draw.
            int8_t start_y = srv_get_number('E');
            if (start_y == -1) {
                // If error, RESET.
                RESET = true;
                break;
            }
            // Use the graph coordinates to make screen coordinates.
            uint8_t draw_x = (COL_WIDTH*start_x)+(DOT_SIZE*start_x)+(X_MARGIN);
            uint8_t draw_y = (ROW_HEIGHT*start_y)+(DOT_SIZE*start_y)+(Y_MARGIN);
            XY8 s(draw_x, draw_y);
            // Set the first vertex to draw.
            draw_start = s;

            // Get the x-coordinate of the second edge to draw.
            uint8_t end_x = srv_get_number('E');
            if (end_x == -1) {
                // If error, RESET.
                RESET = true;
                break;
            }
            // Get the y-coordinate of the second edge to draw.
            uint8_t end_y = srv_get_number('E');
            if (end_y == -1) {
                // If error, RESET.
                RESET = true;
                break;
            }
            // Use the graph coordinates to make screen coordinates.
            draw_x = (COL_WIDTH*end_x)+(DOT_SIZE*end_x)+(X_MARGIN);
            draw_y = (ROW_HEIGHT*end_y)+(DOT_SIZE*end_y)+(Y_MARGIN);
            XY8 e(draw_x, draw_y);
            // Set the second vertex to draw.
            draw_end = e;

            // Process the drawing of the line.
            process_drawing();
            // Go to the top of the loop, if the RESET bool was set, the game
            // will restart.
            break;

        // If it is a human turn:
        } else {
            // Set the current x position to the previous x position.
            int8_t cur_x = PREV_X;
            // Calculate the previous screen x position.
            uint8_t prev_screen_x = (COL_WIDTH*PREV_X)+(DOT_SIZE*PREV_X)+(X_MARGIN);
            uint8_t screen_x = prev_screen_x;
            // If the joystick registers a change in the x position:
            if (abs(dx) > 0) {
                // Add the dx (1 or -1) to the x-position
                cur_x += dx;

                // If the current x-position goes too far right, wrap around.
                if (cur_x > NUM_COLUMNS) {
                    cur_x = 0;
                // If the current x-position goes too far left, wrap around.
                } else if (cur_x < 0) {
                    cur_x = NUM_COLUMNS;
                }

                // Calculate screen x position.
                screen_x = (COL_WIDTH*cur_x)+(DOT_SIZE*cur_x)+(X_MARGIN);
                UPDATE_CURSOR = true; // The screen needs to be updated.
            }

            // Set the current y position to the previous y position.
            int8_t cur_y = PREV_Y;
            // Calculate the previous screen y position.
            uint8_t prev_screen_y = (ROW_HEIGHT*PREV_Y)+(DOT_SIZE*PREV_Y)+(Y_MARGIN);
            uint8_t screen_y = prev_screen_y;
            // If the joystick registers a change in the y position:
            if (abs(dy) > 0) {
                // Add the dy (1 or -1) to the x-position
                cur_y += dy;

                // If the current y-position goes too far down, wrap around.
                if (cur_y > NUM_ROWS) {
                    cur_y = 0;
                // If the current y-position goes too far up, wrap around.
                } else if (cur_y < 0) {
                    cur_y = NUM_ROWS;
                }

                // Calculate the screen y position.
                screen_y = (ROW_HEIGHT*cur_y)+(DOT_SIZE*cur_y)+(Y_MARGIN);
                UPDATE_CURSOR = true; // The screen needs to be updated.
            }

            // Move the cursor if needed.
            if (UPDATE_CURSOR) {
                // Draw a black dot over the old cursor position.
                TFT.fillRect(prev_screen_x, prev_screen_y, DOT_SIZE, DOT_SIZE, BLACK);
                // Draw a green dot on the new cursor position.
                TFT.fillRect(screen_x, screen_y, DOT_SIZE, DOT_SIZE, GREEN);
                // Now the previous positions are the current positions.
                PREV_X = cur_x;
                PREV_Y = cur_y;
                UPDATE_CURSOR = false; // The cursor was just updated.
            }

            // If the joystick was clicked:
            if (select_button_event) {
                // Create a XY8 structure initialized to current cursor position.
                XY8 p(cur_x, cur_y); // Graph coordinates of vertex.
                XY8 d(screen_x, screen_y); // Screen coordinates of vertex.

                // If this is the start vertex selection:
                if (REQUEST_STATE==RS_WAIT_FOR_START) {
                    start = p; // Graph coordinates of start vertex.
                    draw_start = d; // Screen coordinates of start vertex.

                    // Request state now waiting on end vertex.
                    REQUEST_STATE = RS_WAIT_FOR_END;

                    // Status message for end vertex selection.
                    if (PLAYER_TURN == 1) {
                        status_msg("PLAYER 1: TO?");
                    } else if (PLAYER_TURN == 2) {
                        status_msg("PLAYER 2: TO?");
                    }

                // If this is the end vertex selection:
                } else if (REQUEST_STATE==RS_WAIT_FOR_END) {
                    end = p; // Graph coordinates of end vertex.
                    draw_end = d; // Screen coordinates of end vertex.

                    // Request state now waiting on start vertex.
                    REQUEST_STATE = RS_WAIT_FOR_START;

                    // If the line is not valid:
                    if (!line_request_valid(start.x, start.y, end.x, end.y)) {
                        // Notify user and restart the player's turn.
                        invalid_request();
                        continue;
                    }

                    // If valid line, send to the server for graph processing.
                    send_request_to_server();

                    // Server checks if line has been made already.
                    int8_t line_valid = srv_get_number('L');
                    if (line_valid == -1) {
                        // If error, rest the game.
                        RESET = true;
                        break;

                    // If the line has been made already, redo the player turn.
                    } else if (line_valid == 1) {
                        // Notify user and restart the player's turn.
                        invalid_request();
                        continue;
                    }

                    // Process the drawing of the line.
                    process_drawing();
                    // Go to the top of the loop, if the RESET bool was set, the
                    // game will restart.
                    break;
                }
            }
        }
    }
}

/*
    Initialize the TFT screen.
    Runs in O(1)
*/
void initialize_screen() {
    TFT.initR(INITR_BLACKTAB); // Initialize screen type.
    TFT.setRotation(0); // No screen rotation.
    TFT.setCursor(0, 0); // Cursor at (0,0)
    TFT.setTextColor(BLACK); // Black font.
    TFT.setTextSize(1); // Size 1 font.
    TFT.fillScreen(WHITE); // White background.
}

// Centre point of the joystick.
int16_t JOY_CENTRE_X = 512;
int16_t JOY_CENTRE_Y = 512;

/*
    Initialize the joystick.
    Runs in O(1)
*/
void initialize_joystick() {
    // Initialize the button pin, turn on pullup resistor
    pinMode(JOY_PIN_BUTTON, INPUT);
    digitalWrite(JOY_PIN_BUTTON, HIGH);
    // Center Joystick
    JOY_CENTRE_X = analogRead(JOY_PIN_X);
    JOY_CENTRE_Y = analogRead(JOY_PIN_Y);
}

/*
    Gets the number of columns and rows from the server and draws the game board
    based on these specificiations. The game board is scaled to fill the screen
    regardless of the dimensions that are inputted (only limited by size of
    screen).
    Runs in O(n*m) where n is the number of columns+1 and m is the number of
    rows+1.
*/
void render_map() {
    // Get number of columns from the server
    NUM_COLUMNS = srv_get_number('C');
    // If there is an error, RESET the game.
    if (NUM_COLUMNS == -1) {
        RESET = true;
        return;
    }

    // Get the number of rows from the server.
    NUM_ROWS = srv_get_number('R');
    // If there is an error, RESET the game.
    if (NUM_ROWS == -1) {
        RESET = true;
        return;
    }

    // Any dot smaller than 3x3 is strenuous on the eyes.
    // Set a cap that is 3 greater than the maximum dimension so that the scaled
    // dot size will never go lower than 3.
    uint8_t max_dot_size = max(MAX_NUM_COLUMNS, MAX_NUM_ROWS) + 3;

    DOT_SIZE = max_dot_size - max(NUM_COLUMNS, NUM_ROWS);

    X_MARGIN = floor(SCREEN_WIDTH*0.025); // 2.5% margin on either side.
    Y_MARGIN = floor(SCREEN_HEIGHT*0.025); // 2.5% margin on either side.

    // Width of screen without considering dots or margins.
    uint8_t width_delta = SCREEN_WIDTH-(2*X_MARGIN)-(DOT_SIZE*(NUM_COLUMNS+1));
    // Height of screen without considering dots or margins.
    uint8_t height_delta = SCREEN_HEIGHT-(2*Y_MARGIN)-(DOT_SIZE*(NUM_ROWS+1));

    COL_WIDTH = floor(width_delta/NUM_COLUMNS); // The width of columns.
    ROW_HEIGHT = floor(height_delta/NUM_ROWS); // The height of rows.

    for (int i = 0; i < NUM_COLUMNS + 1; i++) {
        for (int j = 0; j < NUM_ROWS + 1; j++) {
            // Calculate the positions of dots on the screen.
            uint8_t x_0 = (COL_WIDTH*i)+(DOT_SIZE*i)+(X_MARGIN);
            uint8_t y_0 = (ROW_HEIGHT*j)+(DOT_SIZE*j)+(Y_MARGIN);

            // Draw the dot to the screen.
            TFT.fillRect(x_0, y_0, DOT_SIZE, DOT_SIZE, BLACK);
        }
    }
}

char* PREV_STATUS_MSG = 0; // Set to blank by default.

/*
    Prints a string msg to bottom of game screen.
    Runs in O(1)
*/
void status_msg(char *msg) {
    // Messages are strings, so we assume constant, and if they are the
    // same pointer then the contents are the same.  You can force by
    // setting PREV_STATUS_MSG = 0
    if (PREV_STATUS_MSG != msg) {
        PREV_STATUS_MSG = msg;
        TFT.fillRect(0, 148, 128, 12, BLACK);

        TFT.setTextColor(WHITE); // White font.
        TFT.setCursor(0, 150); // Cursor at bottom of screen.
        TFT.setTextSize(1); // Font size 1.

        TFT.println(msg); // Print the status message.
    }
}

// Button state: 0 not pressed, 1 pressed
uint8_t PREV_BUTTON_STATE = 0;
// Time of last sampling of button state
uint32_t BUTTON_PREV_TIME = millis();
// Only after this much time has passed is the state sampled.
uint32_t BUTTON_SAMPLE_DELAY = 200;

/*
    Read the joystick position, and return the x, y displacement from
    the zero position. Also, return 1 if the joystick button has been pushed,
    held for a minimum amount of time, and then released. That is, a 1 is
    returned if a button select action has occurred.
    Runs in O(1)
*/
uint8_t process_joystick(int8_t *dx, int8_t *dy) {
    int16_t joy_x; // Joystick x position
    int16_t joy_y; // Joystick y position
    uint8_t button_state; // State of joystick button

    // The joystick x position
    joy_x = (analogRead(JOY_PIN_X) - JOY_CENTRE_X);
    // The joystick y position.
    joy_y = (analogRead(JOY_PIN_Y) - JOY_CENTRE_Y);

    // If the joystick is available to be move the cursor:
    if (JOY_STATE) {

        if (abs(joy_x) > JOY_DEADZONE) {
            // If the x movement is significant, set dx as 1 or -1 based on the
            // direction of the movement.
            *dx = joy_x/abs(joy_x);
        }

        if (abs(joy_y) > JOY_DEADZONE) {
            // If the y movement is significant, set dy as 1 or -1 based on the
            // direction of the movement.
            *dy = joy_y/abs(joy_y);
        }
        // The joystick is now unable to move cursor until it is centred again.
        JOY_STATE = false;
    }

    if (abs(joy_x) <= JOY_DEADZONE && abs(joy_y) <= JOY_DEADZONE) {
        // If the joystick is centred, it can now move the cursor.
        JOY_STATE = true;
    }


    uint8_t button_press_event = 0; // No event by default

    // Check for suitable time delay since the last time we read the joystick
    uint32_t cur_time = millis();

    // Correct time inversion caused by wraparound.
    if (cur_time < BUTTON_PREV_TIME) {
        BUTTON_PREV_TIME = cur_time;
    }

    // If the joystick is avaiable to be clicked:
    if (cur_time > BUTTON_PREV_TIME + BUTTON_SAMPLE_DELAY) {
        BUTTON_PREV_TIME = cur_time;

        // True if button is pressed
        button_state = (LOW == digitalRead(JOY_PIN_BUTTON));

        // If a press is followed by a release, we will have an event:
        button_press_event = (PREV_BUTTON_STATE && !button_state);
        PREV_BUTTON_STATE = button_state;
    }

    return button_press_event; // True if clicked, false otherwise.
}

/*
    Checks if the line requested by human player is a valid move. Will return
    true if valid or false if invalid.
    Runs in O(1)
*/
bool line_request_valid(uint8_t x_0, uint8_t y_0, uint8_t x_1, uint8_t y_1) {
    if (abs(x_1 - x_0) > 1) {
        // If the width of the line is more than one column: false.
        return false;
    } else if (abs(y_1 - y_0) > 1) {
        // If the height of the line is more than one row: false.
        return false;
    } else if ((x_0 != x_1) && (y_0 != y_1)) {
        // If the request is somehow diagonal (hard to do, but possible): false.
        return false;
    } else {
        // Otherwise, the line must be valid.
        return true;
    }
}

/*
    Function to notify user that the last request was invalid and then restart
    the player's turn.
    Runs in O(1)
*/
void invalid_request() {
    // Notify the user that the request was invalid.
    status_msg("INVALID. TRY AGAIN.");
    delay(2000);

    // Set the state to wait for first vertex
    REQUEST_STATE = RS_WAIT_FOR_START;

    // Status message set to the start of the player's turn.
    if (PLAYER_TURN == 1) {
        status_msg("PLAYER 1: FROM?");
    } else if (PLAYER_TURN == 2) {
        status_msg("PLAYER 2: FROM?");
    }
}

/*
    Draws a game over screen.
    Runs in O(1).
*/
void game_over_screen() {
    uint16_t text_colour = WHITE; // Set the text colour to white by default.
    TFT.fillScreen(WHITE); // White background.
    TFT.setTextSize(2.5); // 2.5 font size.
    TFT.setCursor(15, 15);

    // If player 1 won:
    if (PLAYER1_SCORE > PLAYER2_SCORE) {
        // Print that player 1 wins.
        text_colour = BLUE;
        TFT.setTextColor(text_colour);
        TFT.print("PLAYER 1");
        TFT.setCursor(40,40);
        TFT.print("WINS");

    // If player 2 won:
    } else if (PLAYER2_SCORE > PLAYER1_SCORE) {
        // Print that player 2 wins.
        text_colour = RED;
        TFT.setTextColor(text_colour);
        TFT.print("PLAYER 2");
        TFT.setCursor(40,40);
        TFT.print("WINS");

    // If there was a tie:
    } else {
        // Print that it was a tie.
        text_colour = BLACK;
        TFT.setTextColor(text_colour);
        TFT.setTextSize(3.5);
        TFT.setCursor(40,35);
        TFT.print("TIE");
    }

    // Print both player scores and prompt the use to click to play again.
    TFT.setTextColor(BLACK);
    TFT.setTextSize(1);
    TFT.setCursor(45, 80);
    TFT.println("SCORE");
    TFT.setCursor(30,100);
    TFT.print("Player 1: "); TFT.print(PLAYER1_SCORE);
    TFT.setCursor(30,120);
    TFT.print("Player 2: "); TFT.print(PLAYER2_SCORE);
    TFT.setCursor(7, 145);
    TFT.setTextColor(text_colour);
    TFT.print("CLICK TO PLAY AGAIN");
}

/*
    Function to draw one or two boxes to the screen if the recently added edge
    has closed any of them.
    Runs in O(n) where n is the number of closed boxes.
*/
void draw_box(uint16_t PLAYER_COLOUR, uint8_t num_closed_boxes) {
    for (int i = 0; i < num_closed_boxes; i++) {
        // Get the x-positions of the closed box.
        int8_t box_col = srv_get_number('B');
        // If there is an error, RESET the game.
        if (box_col == -1) {
            RESET = true;
            return;
        }

        // Get the y-positions of the closed box.
        int8_t box_row = srv_get_number('B');
        // If there is an error, RESET the game.
        if (box_row == -1) {
            RESET = true;
            return;
        }

        // Calculate the screen x and screen y positions to draw the box.
        uint8_t box_x = (COL_WIDTH*box_col)+(DOT_SIZE*(box_col+1))+(X_MARGIN);
        uint8_t box_y = (ROW_HEIGHT*box_row)+(DOT_SIZE*(box_row+1))+(Y_MARGIN);

        // Draw the box.
        TFT.fillRect(box_x, box_y, COL_WIDTH, ROW_HEIGHT, PLAYER_COLOUR);
  }
}

/*
    Draws a line based on coordinates set in the main game loop.
    Runs in O(1)
*/
void draw_line() {
    uint8_t x_0; // The line's x-coordinate.
    uint8_t y_0; // The line's y-coordinate.

    // If the vertices are horizontally apart:
    if (draw_start.x != draw_end.x) {
        // Horizontal line draw.
        x_0 = (min(draw_start.x, draw_end.x) + DOT_SIZE);
        y_0 = draw_start.y;

        // Draw the black, horizontal line.
        TFT.fillRect(x_0, y_0, COL_WIDTH, DOT_SIZE, BLACK);

    // If the vertices are vertically apart:
    } else if (draw_start.y != draw_end.y) {
        // Vertical line draw.
        x_0 = draw_start.x;
        y_0 = (min(draw_start.y, draw_end.y) + DOT_SIZE);

        // Draw the black, vertical line.
        TFT.fillRect(x_0, y_0, DOT_SIZE, ROW_HEIGHT, BLACK);
    }
}

/*
    Sends a line request through the serial monitor to the python server.
    Runs in O(1)
*/
void send_request_to_server() {
    Serial.print("R ");
    Serial.print(start.x); Serial.print(" ");
    Serial.print(start.y); Serial.print(" ");
    Serial.print(end.x); Serial.print(" ");
    Serial.println(end.y);
}

/*
    A function that sets up the game board and game states based on the
    user-inputted values from the python server protocol function.
    Bounded by render_map runtime: O(n^2)
*/
void game_setup() {
    Serial.flush(); // Flush leftover bits.
    initialize_screen(); // Draw a white screen.
    initialize_joystick(); // Prepare joystick.

    // Get the type of game.
    GAME_TYPE = srv_get_number('G');
    // If the game type is invalid, retry to setup the game.
    if (GAME_TYPE == -1) {
        RESET = true;
        return;
    }

    render_map(); // Draw the game board.
    // If the game dimensions are invalid, retry to setup the game.
    if ((NUM_COLUMNS == -1) || (NUM_ROWS == -1)) {
        RESET = true;
        return;
    }

    // If it is a 1 versus computer game:
    if (GAME_TYPE == 0) {
        // Get the number of the computer's turn (1 or 2).
        COMPUTER_TURN = srv_get_number('F');
    } else {
        COMPUTER_TURN = 0;
    }
    // If the computer turn is invalid, retry to setup the game.
    if (COMPUTER_TURN == -1) {
        RESET = true;
        return;
    }

    PREV_X = 0; // Reset initial cursor x-position
    PREV_Y = 0; // Reset initial cursor y-position
    PLAYER1_SCORE = 0; // Reset score.
    PLAYER2_SCORE = 0; // Reset score.
    PLAYER_TURN = 1; // Reset to be the first turn.
    JOY_STATE = true; // Joystick moving availability state.
    PLAY_AGAIN = false; // Determines whether plays again or not.
    PREV_BUTTON_STATE = 0; // Reset click state.
    BUTTON_PREV_TIME = millis(); // Time of last sampling of button state.
    PREV_STATUS_MSG = 0; // Reset previous status message.
    JOY_CENTRE_X = 512; // Reset joystick centre x position
    JOY_CENTRE_Y = 512; // Reset joystick centre y position
    REQUEST_STATE = RS_WAIT_FOR_START; // Reset request state.
    status_msg("PLAYER 1: FROM?"); // Set the initial status message.
    UPDATE_CURSOR = true; // Draw the cursor at the top-left vertex.
}

/*
    Process the drawing of lines and boxes and sends information about the state
    of the game to the python server.
    Bounded by draw_box runtime: O(n) where n is the number of closed boxes.
*/
void process_drawing() {
    draw_line(); // Draw the requested line.

    // Get the number of boxes closed by the added line.
    int8_t num_closed_boxes = srv_get_number('N');
    // If there is an error, RESET the game.
    if (num_closed_boxes == -1) {
        RESET = true;
        return;
    // If boxes were closed, the player plays again.
    } else if (num_closed_boxes > 0) {
        PLAY_AGAIN = true;
    }

    // Set box colour based on which player made the request.
    // Each closed box adds a point to the player's score.
    if (PLAYER_TURN == 1) {
        PLAYER1_SCORE += num_closed_boxes;
        PLAYER_COLOUR = BLUE;
    } else if (PLAYER_TURN == 2) {
        PLAYER2_SCORE += num_closed_boxes;
        PLAYER_COLOUR = RED;
    }

    // Draw the box to the screen.
    draw_box(PLAYER_COLOUR, num_closed_boxes);

    // Server checks if the game is over.
    int8_t game_is_over = srv_get_number('O');
    // If there is an error, RESET the game.
    if (game_is_over == -1) {
        RESET = true;
        return;
    // If the game is over:
    } else if (game_is_over == 1) {
        delay(1000); // Delay for 1 second.
        game_over_screen(); // Draw a game over screen.
        // Wait for player to click joystick
        while (process_joystick(0, 0)==0){}
        Serial.println('A'); // Send acknowledgement.
        RESET = true;
        return;
    }

    // Determine the next player turn. If a player has scored, they play again.
    if (PLAYER_TURN == 1) {
        if (PLAY_AGAIN) {
            status_msg("PLAYER 1: FROM?");
        } else {
            PLAYER_TURN = 2;
            status_msg("PLAYER 2: FROM?");
        }
    } else if (PLAYER_TURN == 2) {
        if (PLAY_AGAIN) {
            status_msg("PLAYER 2: FROM?");
        } else {
            PLAYER_TURN = 1;
            status_msg("PLAYER 1: FROM?");
        }
    }
}
