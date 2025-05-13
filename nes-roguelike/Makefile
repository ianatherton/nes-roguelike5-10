# Makefile for Craven Caverns NES Roguelike
# Based on cc65 compiler suite

# Directories
SRC_DIR = src
BUILD_DIR = build
TOOLS_DIR = tools
ASM_DIR = $(SRC_DIR)/assembly

# Compiler and tools
CC = cc65
CA = ca65
LD = ld65

# ROM details
ROM_NAME = craven_caverns
ROM_MAPPER = 4  # MMC3 mapper (same as Castlevania III)

# Files
C_SOURCES = $(wildcard $(SRC_DIR)/*.c)
ASM_SOURCES = $(wildcard $(ASM_DIR)/*.s)
C_OBJECTS = $(patsubst $(SRC_DIR)/%.c, $(BUILD_DIR)/%.o, $(C_SOURCES))
ASM_OBJECTS = $(patsubst $(ASM_DIR)/%.s, $(BUILD_DIR)/%.o, $(ASM_SOURCES))
OBJECTS = $(C_OBJECTS) $(ASM_OBJECTS)

# Flags
CFLAGS = -Oi -t nes --add-source
CAFLAGS = -t nes
LDFLAGS = -t nes -C nes.cfg

# Main target
.PHONY: all clean run

all: $(BUILD_DIR)/$(ROM_NAME).nes

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Compile C source files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $(patsubst %.o, %.s, $@) $<
	$(CA) $(CAFLAGS) -o $@ $(patsubst %.o, %.s, $@)

# Assemble ASM source files
$(BUILD_DIR)/%.o: $(ASM_DIR)/%.s | $(BUILD_DIR)
	$(CA) $(CAFLAGS) -o $@ $<

# Link object files
$(BUILD_DIR)/$(ROM_NAME).nes: $(OBJECTS)
	$(LD) $(LDFLAGS) -o $@ $^

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)/*

# Run in emulator (FCEUX)
run: $(BUILD_DIR)/$(ROM_NAME).nes
	fceux $<

# Debug in emulator
debug: $(BUILD_DIR)/$(ROM_NAME).nes
	fceux --debug 1 $<
