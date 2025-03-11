#ifdef __linux__
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wanalyzer-use-of-uninitialized-value"
#include <boost/asio.hpp>
#pragma GCC diagnostic pop
#else
#include <boost/asio.hpp>
#endif // __linux__

#include <iostream>

int main() {
    std::cout << "Hello World!" << std::endl;
    return 0;
}
