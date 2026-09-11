#include <cs50.h>
#include <stdio.h>

void meow(int times);

int main(void)
{
	meow(3);
}

void meow (int times)
{
	for (int i = 0; i < times; i++)
	{
		printf("meow\n");
	}
}
