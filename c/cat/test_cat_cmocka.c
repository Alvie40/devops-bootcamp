#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>

#include "capture.h"

extern void meow(int times);

static void test_meow_prints_three_times(void **state)
{
	(void)state;
	char buf[64];
	capture_stdout(meow, 3, buf, sizeof(buf));
	assert_string_equal(buf, "meow\nmeow\nmeow\n");
}

static void test_meow_zero_times_prints_nothing(void **state)
{
	(void)state;
	char buf[64];
	capture_stdout(meow, 0, buf, sizeof(buf));
	assert_string_equal(buf, "");
}

static void test_meow_five_times(void **state)
{
	(void)state;
	char buf[64];
	capture_stdout(meow, 5, buf, sizeof(buf));
	assert_string_equal(buf, "meow\nmeow\nmeow\nmeow\nmeow\n");
}

int main(void)
{
	const struct CMUnitTest tests[] = {
		cmocka_unit_test(test_meow_prints_three_times),
		cmocka_unit_test(test_meow_zero_times_prints_nothing),
		cmocka_unit_test(test_meow_five_times),
	};
	return cmocka_run_group_tests(tests, NULL, NULL);
}
