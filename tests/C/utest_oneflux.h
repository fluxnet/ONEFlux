/* utest_oneflux.h */
#include "utest.h"

/*
  This macro provides an extension to the utest.h library to include 
  functionality similar to CK_ASSERT_MSG function from the Check library. It 
  currently only supports a single function parameter in the message.
*/
#define FAIL_UNLESS(x,...)                                  \
  UTEST_SURPRESS_WARNING_BEGIN do {                         \
    const int xEval = !!(x);                                \
    if (!(xEval)) {                                         \
      UTEST_PRINTF("%s:%i: Failure\n", __FILE__, __LINE__); \
	    UTEST_PRINTF(" Condition : (%s)\n", #x);              \
      UTEST_PRINTF("   Message : %s, parameter: %s\n", ## __VA_ARGS__);    \
      *utest_result = UTEST_TEST_FAILURE;                   \
      return;                                               \
    }                                                       \
  }                                                         \
  while (0)                                                 \
  UTEST_SURPRESS_WARNING_END


#define ASSERT_MSG FAIL_UNLESS