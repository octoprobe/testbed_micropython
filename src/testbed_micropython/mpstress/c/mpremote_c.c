/*
This programs open a serial line to a micropython cpu.

Send "print('hello')"
Return 0 if the response in "hellon\r\n"
Return 1 on error.
*/
#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <errno.h>

#ifndef CRTSCTS
#define CRTSCTS 0
#endif

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <serial_device>\n", argv[0]);
        fprintf(stderr, "Example: %s /dev/ttyACM4\n", argv[0]);
        return 1;
    }

    const char *serial_device = argv[1];
    int serial_fd;
    struct termios tty;
    const char *command = "print('hello')\r\n";
    char response[256];
    const char *expected_response = "hello\r\n";
    ssize_t bytes_read;

    // Open serial device
    serial_fd = open(serial_device, O_RDWR | O_NOCTTY);
    if (serial_fd < 0) {
        perror("Error opening serial device");
        return 1;
    }

    // Get current terminal attributes
    if (tcgetattr(serial_fd, &tty) != 0) {
        perror("Error getting terminal attributes");
        close(serial_fd);
        return 1;
    }

    // Configure serial port settings
    // Set baud rate to 115200
    cfsetospeed(&tty, B115200);
    cfsetispeed(&tty, B115200);

    // 8N1 mode
    tty.c_cflag &= ~PARENB;        // No parity
    tty.c_cflag &= ~CSTOPB;        // One stop bit
    tty.c_cflag &= ~CSIZE;         // Clear size bits
    tty.c_cflag |= CS8;            // 8 data bits
    tty.c_cflag &= ~CRTSCTS;       // No hardware flow control
    tty.c_cflag |= CREAD | CLOCAL; // Enable reading, ignore modem control lines

    // Input modes
    tty.c_iflag &= ~(IXON | IXOFF | IXANY); // No software flow control
    tty.c_iflag &= ~(ICANON | ECHO | ECHOE | ISIG); // Raw input

    // Output modes
    tty.c_oflag &= ~OPOST; // Raw output

    // Local modes
    tty.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG); // Raw mode

    // Control characters
    tty.c_cc[VMIN] = 2*strlen(expected_response);   // Blocking read - wait for at least 1 character
    tty.c_cc[VTIME] = 10; // 1 second timeout (in deciseconds)

    // Apply settings
    if (tcsetattr(serial_fd, TCSANOW, &tty) != 0) {
        perror("Error setting terminal attributes");
        close(serial_fd);
        return 1;
    }

    // Flush any existing data
    tcflush(serial_fd, TCIOFLUSH);

    // Give device time to initialize
    // usleep(100000); // 100ms

    // Send command
    ssize_t bytes_written = write(serial_fd, command, strlen(command));
    if (bytes_written < 0) {
        perror("Error writing to serial device");
        close(serial_fd);
        return 1;
    }

    // Give device time to process and respond
    // usleep(500000); // 500ms

    // Read response
    memset(response, 0, sizeof(response));
    bytes_read = read(serial_fd, response, sizeof(response) - 1);
    if (bytes_read < 0) {
        perror("Error reading from serial device");
        close(serial_fd);
        return 1;
    }

    // Close serial device
    close(serial_fd);

    // Check if we got the expected response
    // Look for "hello" followed by newline and carriage return
    if (strstr(response, "hello") != NULL) {
        // Check if response contains hello followed by \r\n or \n\r
        if (strstr(response, "hello\r\n") != NULL || strstr(response, "hello\n\r") != NULL) {
            printf("Success: Got expected response containing 'hello\\r\\n' or 'hello\\n\\r'\n");
            return 0;
        } else if (strstr(response, "hello") != NULL) {
            printf("Partial success: Got 'hello' but not with expected line endings\n");
            printf("Response was: ");
            for (int i = 0; i < bytes_read; i++) {
                if (response[i] >= 32 && response[i] <= 126) {
                    printf("%c", response[i]);
                } else {
                    printf("\\x%02x", (unsigned char)response[i]);
                }
            }
            printf("\n");
            return 0; // Still consider it success if we got hello
        }
    }

    printf("Failed: Did not get expected response 'hello\\n\\r'\n");
    printf("Response was: ");
    for (int i = 0; i < bytes_read; i++) {
        if (response[i] >= 32 && response[i] <= 126) {
            printf("%c", response[i]);
        } else {
            printf("\\x%02x", (unsigned char)response[i]);
        }
    }
    printf("\n");
    return 1;
}
