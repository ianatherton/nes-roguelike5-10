# Development Environment Setup for Linux Mint

This guide will help you set up all the necessary tools and dependencies for developing Craven Caverns, our NES roguelike game.

## Required Tools

### 1. Emulators
```bash
# Install FCEUX (NES emulator with debugging tools)
sudo apt update
sudo apt install fceux

# Install Mesen (another excellent NES emulator, may require building from source)
# Instructions at: https://github.com/SourMesen/Mesen
```

### 2. Development Tools
```bash
# Install cc65 (C compiler for 6502 processors)
sudo apt install cc65

# Install git for version control
sudo apt install git

# Install make for build automation
sudo apt install make

# Install Python (for custom tools)
sudo apt install python3 python3-pip

# Install image manipulation libraries for Python
pip3 install pillow numpy
```

### 3. Additional Helpful Tools
```bash
# Install HxD alternative (hexedit) for Linux
sudo apt install hexedit

# Install tile editors
sudo apt install tiled

# Install GIMP for graphics editing
sudo apt install gimp
```

## Setup Project Environment

### Clone the Repository (if using version control)
```bash
git init
```

### Download and Install NES Development Tools
```bash
# Create a directory for tools
mkdir -p ~/nes-dev-tools
cd ~/nes-dev-tools

# Download and extract NESASM (if not using cc65)
wget https://github.com/camsaul/nesasm/archive/refs/heads/master.zip
unzip master.zip
cd nesasm-master
make
```

### Install Tile Editing Tools
```bash
# YY-CHR can be run with Wine
sudo apt install wine
# Then download YY-CHR from http://www.geocities.jp/yy_6502/yychr/
```

### Install FamiTracker for Music
FamiTracker is Windows software but can be run on Linux using Wine:
```bash
sudo apt install wine
# Download FamiTracker from http://famitracker.com/
```

## ROM Placement

Create a designated spot for your legally owned Arkista's Ring ROM:

```bash
mkdir -p /home/sparkydev/projects/general_research/nes-roguelike5-10/nes-roguelike/assets/reference/
```

Place your ROM file at:
```
/home/sparkydev/projects/general_research/nes-roguelike5-10/nes-roguelike/assets/reference/arkistas_ring.nes
```

This location is gitignored (if using git) and only used locally for asset extraction.

## Building and Running

### Basic Build Process
```bash
# Navigate to project directory
cd /home/sparkydev/projects/general_research/nes-roguelike5-10/nes-roguelike

# Run make (once Makefile is created)
make

# Test in emulator
fceux build/craven_caverns.nes
```

## Setting Up Visual Studio Code (Optional)
```bash
# Install Visual Studio Code
sudo apt install code

# Recommended extensions:
# - C/C++ extension
# - 6502 Assembly extension
# - Hex Editor extension
# - NES debug extension
```

## Next Steps

1. Place your Arkista's Ring ROM in the designated folder
2. Run the asset extraction tools (to be developed)
3. Begin implementing the game systems according to the technical specification
