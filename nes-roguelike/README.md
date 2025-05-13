# Craven Caverns: NES Roguelike

A classic-style roguelike game for the NES inspired by Arkista's Ring (visuals/audio) and Fatal Labyrinth (gameplay mechanics). This project aims to create an authentic NES experience while staying within the hardware limitations of the original console.

## Project Structure

```
nes-roguelike/
├── docs/             # Design documents, notes, references
├── assets/           # Extracted assets from Arkista's Ring
│   ├── sprites/
│   ├── backgrounds/
│   ├── music/
│   ├── sfx/
│   └── reference/    # Place your legal ROM copy here
├── src/              # Source code for the game
│   ├── engine/       # Core game engine code
│   ├── gameplay/     # Gameplay mechanics
│   ├── ui/           # UI elements and code
│   └── data/         # Game data (items, enemies, etc.)
├── tools/            # Tools for development and asset extraction
└── build/            # Compiled ROMs and build artifacts
```

## Getting Started

1. Read the `docs/development_environment_setup.md` guide to set up your Linux Mint environment
2. Place your legal copy of Arkista's Ring ROM in `assets/reference/`
3. Use the extraction tools in the `tools/` directory to extract game assets
4. Follow the project roadmap in `docs/project_roadmap.md`

## Documentation

- `docs/game_design_document.md` - Overall game design and concepts
- `docs/technical_specification.md` - Technical details and implementation plans
- `docs/asset_extraction_guide.md` - Guide for extracting assets from Arkista's Ring
- `docs/development_environment_setup.md` - Setup guide for Linux Mint
- `docs/project_roadmap.md` - Development timeline and milestones

## Development

This project uses:
- CC65 compiler suite for C code
- Assembly for performance-critical sections
- Custom tools for asset extraction and conversion
- FCEUX/Mesen for emulation and testing

## Legal Notes

This project is for educational purposes only. You must own a legal copy of Arkista's Ring to extract and use its assets. The final game should be substantially different from the original games it's inspired by.

## Current Status

Project is in the initial planning and setup phase. See the roadmap for next steps.
