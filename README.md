# Arduino Dots and Boxes
## Recommended hardware
* 1x Arduino Mega Board (AMG)  
* 1x Adafruit 1.8" 18-bit color TFT LCD    
* 1x Sparkfun COM-09032 Joystick and Breakout Board  
## Wiring Instructions
* Note: LCD pins below are listed from left to right (LCD is portrait with pins facing user).
* LCD GND <--> Arduino GND bus
* LCD VCC <--> Arduino positive bus
* LCD RESET <--> Arduino Pin 8
* LCD D/C (Data/Command) <--> Arduino Pin 7
* LCD CARD_CS (Card Chip Select) <--> Arduino Pin 5
* LCD TFT_CS (TFT/screen Chip Select) <--> Arduino Pin 6
* LCD MOSI (Master Out Slave In) <--> Arduino Pin 51
* LCD SCK (Clock) <--> Arduino Pin 52
* LCD MISO (Master In Slave Out) <--> Arduino 50
* LCD LITE (Backlite) <--> Arduino positive bus
*
* Note: Joystick pins below are listed from right to left (Joystick is portrait with pins facing away from user).
* Joystick VCC <--> Arduino positive bus
* Joystick VERT <--> Arduino Pin A0
* Joystick HOR <--> Arduino Pin A1
* Joystick SEL <--> Arduino Pin 4
* Joystick GND <--> Arduino GND bus
*
* Arduino positive bus <--> Arduino 5V pin
* Arduino GND bus <--> Arduino GND pin
## How to run
* This project is designed to run through the command line with the help of a Makefile that was provided for the class.
* Typing "make upload client.cpp" and pressing enter in the command line while in the project directory will run the client code.
* Next, typing "python3 server.py" and pressing enter in the command line while in the project directory will run the server code.
* Additional arguments can be added to the "python3 server.py" command. These include -s for specifying serial port and -d to turn debug printing on.
* Note: It is best to give a few seconds before responding to a the game setup prompts.
* The serial monitor needs a small amount of time to load before it is ready to begin serial port communication.
* If the game setup prompts become erroneous and without correction, use CTRL-C to break out and then re-enter "python3 server.py" to try again.
* Note: Using VMware on a Mac seems to produce communication errors in the game setup (inconsistent).
* The above bugs do not occur using Oracle VirtualBox or VMWare with a Windows host OS.
* Note: To minimize the risk of soft-locking the joystick, move and click definitively and try to avoid moving during a computer turn.
## Description
* Dots and boxes is a two-player combinatorial game.
* The game board is a rectangular array of dots.
* A move consists of drawing a line of length 1 between horizontally or vertically adjacent dots.
* If a player closes a 1x1 box on the game board with their line, they score a point and get to play again.
* The player with the most points at the end of the game wins.
* Our project implements a game of dots and boxes using a python server for user input and request processing and an Arduino client for interfacing the game.
* Our project supports a "human versus human" game type and a "human versus computer" game type. They are described below.
* With every turn in our game, timeouts and error handling is inplemented such that the game will completely reset if an error is encountered.
* This error handling scheme was chosen because errors were a sign of communication interruption or disconnection (safest to completely reset the server/client states).
* Our project supports a debug printing mode where the sends/receives between the server and client can are printed to the screen.
* As well, if the computer is playing, debug printing will show a representation of the chains and components of the game board graph.
* These representations are printed to the screen as lists and sets. In our proposal we said that this would be visualized as lines on the screen, but this proved to be
* too time-expensive (and also they were long functions).
* Useful terms for reading our code:
* Game graph - The game board is stored as an undirected graph with vertices and edges. This graph can be visualized as the dots and lines on the TFT display.
* Strategy graph - An undirected graph representation of the connected chains that can be made with boxes that are reachable from one another. Not the same as the game graph.
* Open chain - An open chain is a group of multiple boxes that can be taken simultaneously, using the extra turns scored from successive closed boxes.
* Long chain - A chain of boxes of length 3 or more.
* Short chain - A chain of two boxes.
* "Edge of graph" and "line of game board" are two ways of describing the same thing.
* "Vertex of graph" and "dot of game board" are two ways of describing the same thing.
## Human versus Human Gameplay
* The python server will prompt the user for game specifications including the game type and game board dimensions. From these the game board will be built.
* Once the game has been built, the player's will take turns adding lines to the board.
* To do so, users will move around the board with the joystick (visualized by a green cursor) and can click on the dots that they want to build a line with.
* If the dots are adjacent and the line has not already been drawn, the line will be drawn.
* If a request is invalid, the player will be prompted by the Arduino screen and gets to retry their turn.
* If a user closes a 1x1 box on the board, they will score a point and will be allowed to play again.
* When there are no more moves left, the game will end and the users will be prompted to play again by clicking on the game over screen.
## Human versus Computer Gameplay
Human versus Computer gameplay:
* The same as the "human versus human gameplay" section above except one of the players is the computer.
* The computer will print a description of the move that it just took.
* The computer uses a strategy known as the "long chain rule"
* More on this strategy can be found online or in Elwyn Berlekamp's novel "The Dots and Boxes Game: Sophisticated Child's Play"
* The long chain rule dictates:
* The first player wants the number of starting dots + the number of long chains in the game to be EVEN
