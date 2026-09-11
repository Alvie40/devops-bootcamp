// Shared helper: capture what a function prints to stdout.
#ifndef CAPTURE_H
#define CAPTURE_H

#include <stdio.h>
#include <string.h>
#include <unistd.h>

static inline void capture_stdout(void (*fn)(int), int arg, char *buf, size_t bufsize)
{
	memset(buf, 0, bufsize);

	fflush(stdout);
	int saved_fd = dup(fileno(stdout));
	FILE *tmp = tmpfile();
	dup2(fileno(tmp), fileno(stdout));

	fn(arg);

	fflush(stdout);
	dup2(saved_fd, fileno(stdout));
	close(saved_fd);

	rewind(tmp);
	fread(buf, 1, bufsize - 1, tmp);
	fclose(tmp);
}

#endif
