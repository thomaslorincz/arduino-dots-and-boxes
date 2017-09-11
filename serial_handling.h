#ifndef SERIAL_HANDLING_H
#define SERIAL_HANDLING_H

#include <stdint.h>

int srv_get_number(char expected_identifier);

int16_t serial_readline(char *line, uint16_t line_size);

#endif
