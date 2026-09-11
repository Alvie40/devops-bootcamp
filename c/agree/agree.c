#include <cs50.h>
#include <ctype.h>
#include <stdio.h>

int main(void)
{
	char c;
	do
	{
		c = tolower(get_char("Do you agree? "));
	}
	while (c != 'y' && c != 'n');

	printf(c == 'y' ? "Agreed.\n" : "Not agreed.\n");
}
