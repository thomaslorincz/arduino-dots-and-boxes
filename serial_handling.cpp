#include "serial_handling.h"

#include <Arduino.h>
#include <errno.h>
#include <assert13.h>
#include <stdio.h>

int srv_get_number(char expected_identifier) {
    size_t buf_size = 32; // max size for a read buffer
    size_t buf_len = 0; // length of read buffer
    char buf[buf_size]; // where to store read bytes

    char received_identifier;
    int desired_quantity;

    unsigned long timeout = 3000; // 3 second timeout for all communications.
    unsigned long prev_time = millis(); // Set a start time.

    while (received_identifier != expected_identifier) {
        if ((millis() - prev_time) > timeout) {
            Serial.println('T'); // 'T' denotes a timeout
            return -1;
        }

        buf_len = serial_readline(buf, buf_size);
        if (buf_len > 0) {
            sscanf(buf, "%c %d", &received_identifier, &desired_quantity);
        } else {
            Serial.println('T'); // 'T' denotes a timeout
            return -1;
        }
    }

    Serial.println('A');
    return desired_quantity;
}

/*
    Function to read a single line from the serial buffer up to a
    specified length (length includes the null termination character
    that must be appended onto the string). This function is blocking.
    The newline character sequence is given by CRLF, or "\r\n".

    Arguments:

    buffer - Pointer to a buffer of characters where the string will
        be stored.

    length - The maximum length of the string to be read.

    Preconditions:  None.

    Postconditions: Function will block until a full newline has been
        read, or the maximum length has been reached. Afterwards the new
        string will be stored in the buffer passed to the function.

    Returns: the number of bytes read

*/
int16_t serial_readline(char *line, uint16_t line_size) {
    int bytes_read = 0; // Number of bytes read from the serial port.
    unsigned long timeout = 3000; // 3 second timeout for all communications.
    unsigned long prev_time = millis(); // Set a start time.

    // Read until we hit the maximum length, or a newline.
    // One less than the maximum length because we want to add a null terminator.
    while (bytes_read < line_size - 1) {
        // If the current time - start time is greater than timeout, return -1.
        if ((millis() - prev_time) > timeout) {
            return -1;
        }

        // Wait until data is available.
        while (Serial.available() == 0 ) {}

        line[bytes_read] = (char) Serial.read();

        // A newline is given by \r or \n, or some combination of both
        // or the read may have failed and returned 0
        if ( line[bytes_read] == '\r' || line[bytes_read] == '\n' ||
             line[bytes_read] == 0 ) {
                // We ran into a newline character!  Overwrite it with \0
                break;    // Break out of this - we are done reading a line.
        } else {
            bytes_read++;
        }
    }

    // Add null termination to the end of our string.
    line[bytes_read] = '\0';
    return bytes_read;
}
