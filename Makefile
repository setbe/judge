# Linux compiler settings
CXX = g++
CXXFLAGS = -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wsign-conversion \
           -Wmissing-declarations -Winline \
           -Wundef -Wcast-align -Wcast-qual -Wpointer-arith -Wwrite-strings \
           -Wredundant-decls -Wformat=2 -Wswitch-default -Wswitch-enum \
           -Wunreachable-code -Wstack-usage=1024 -Winit-self -Wlogical-op \
           -Wfloat-equal -Wstrict-overflow=5 -Wduplicated-cond -Wduplicated-branches \
           -Wnull-dereference -Wdouble-promotion -Walloc-zero -Walloca \
					 -Wformat-truncation=2 -Wformat-overflow=2 -Wstringop-overflow=2 \
           -std=c++11 -O2 -g2 -fanalyzer -I/usr/include/boost

LDFLAGS = -lboost_system -pthread 

# Directories
SRC_DIR = src
BUILD_DIR = build
OBJ_DIR = $(BUILD_DIR)/obj
BIN_DIR = $(BUILD_DIR)/bin

# Source files
SRC_FILES = $(shell find $(SRC_DIR) -type f -name "*.cpp" ! -path "*/windows/*")
OBJ_FILES = $(patsubst $(SRC_DIR)/%.cpp, $(OBJ_DIR)/%.o, $(SRC_FILES))

# Output binary
TARGET = $(BIN_DIR)/judge

# Default rule (Linux build)
all: $(TARGET)

# Create directories if they don't exist
$(OBJ_DIR) $(BIN_DIR):
	mkdir -p $@

# Compile object files for Linux (with automatic directory creation)
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp | $(OBJ_DIR)
	mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Link the final executable for Linux
$(TARGET): $(OBJ_FILES) | $(BIN_DIR)
	$(CXX) $(OBJ_FILES) $(LDFLAGS) -o $(TARGET)

# Clean build
clean:
	rm -rf $(BUILD_DIR)

# Run on Linux
run: all
	./$(TARGET)
