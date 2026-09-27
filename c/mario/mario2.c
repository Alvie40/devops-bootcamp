#include <cs50.h>
#include <stdio.h>

int main(void)
{
    int height;
    do
    {
        height = get_int("Height: ");
    }
    while (height < 1);

    for (int n = 1; n <= height; n++)
    {
        for (int i = 0; i < n; i++)
            printf("#");
        printf("\n");
    }
}
