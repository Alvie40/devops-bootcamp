#include <cs50.h>
#include <stdio.h>

int main(void)
{
    int numbers[] = {20, 500, 10, 5, 100, 1, 50};
    int count = sizeof(numbers) / sizeof(numbers[0]);
    int n = get_int("Number: ");

    for (int pos = 0; pos < count; pos++)
    {
        if (numbers[pos] == n)
        {
            printf("Number %i found in position %i\n", n, pos);
            return 0;
        }
    }

    printf("Not Found\n");
    return 0;
}
