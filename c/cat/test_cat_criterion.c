#include <criterion/criterion.h>

#include "capture.h"

extern void meow(int times);

Test(meow, prints_three_times)
{
	char buf[64];
	capture_stdout(meow, 3, buf, sizeof(buf));
	cr_assert_str_eq(buf, "meow\nmeow\nmeow\n");
}

Test(meow, zero_times_prints_nothing)
{
	char buf[64];
	capture_stdout(meow, 0, buf, sizeof(buf));
	cr_assert_str_eq(buf, "");
}

Test(meow, five_times)
{
	char buf[64];
	capture_stdout(meow, 5, buf, sizeof(buf));
	cr_assert_str_eq(buf, "meow\nmeow\nmeow\nmeow\nmeow\n");
}
