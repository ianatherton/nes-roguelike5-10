# Craven Caverns - Gameplay Systems Documentation

This document outlines the core gameplay systems for Craven Caverns, inspired by Fatal Labyrinth while using artwork from Arkista's Ring.

## Table of Contents
- [Character Stats](#character-stats)
- [Level Progression](#level-progression)
- [Weapons](#weapons)
- [Armor](#armor)
- [Items and Scrolls](#items-and-scrolls)
- [Food and Hunger System](#food-and-hunger-system)
- [Monsters](#monsters)
- [Magic and Spells](#magic-and-spells)
- [Dungeon Generation](#dungeon-generation)

## Character Stats

### Base Player Stats
| Stat | Starting Value | Max Value | Description |
|------|---------------|-----------|-------------|
| HP   | 15            | 999       | Hit Points - your life force |
| Strength | 5         | 99        | Physical attack power |
| Defense  | 1         | 99        | Damage reduction |
| Food Level | 100     | 100       | Hunger meter, decreases over time |
| Level | 1           | 50         | Character experience level |


### Stat Growth per Level
| Level | HP Gain | Strength Gain | Defense Gain |
|-------|---------|---------------|-------------|
| 1-10  | +5-8    | +1            | +1 every 2 levels |
| 11-20 | +8-12   | +1-2          | +1 every 2 levels |
| 21-30 | +10-15  | +2            | +1 |
| 31-40 | +12-18  | +2-3          | +1-2 |
| 41-50 | +15-20  | +3            | +2 |

### Experience Requirements
| Level | Exp Required | Cumulative Exp |
|-------|--------------|----------------|
| 2     | 10           | 10             |
| 3     | 25           | 35             |
| 4     | 50           | 85             |
| 5     | 100          | 185            |
| 6     | 150          | 335            |
| 7     | 250          | 585            |
| 8     | 400          | 985            |
| 9     | 650          | 1,635          |
| 10    | 1,000        | 2,635          |
| 15    | 5,000        | 17,635         |
| 20    | 10,000       | 67,635         |
| 30    | 40,000       | 467,635        |
| 40    | 100,000      | 1,467,635      |
| 50    | 250,000      | 3,967,635      |

## Weapons

### Weapon Types and Base Damage
| Weapon Type    | Base Damage | Weight | Special Properties |
|----------------|-------------|--------|-------------------|
| Wooden Dagger  | 1-2         | 1      | None |
| Short Sword    | 2-5         | 2      | None |
| Iron Sword     | 5-9         | 3      | None |
| Broad Sword    | 7-12        | 4      | None |
| Fighter's Sword| 10-15       | 5      | Critical x1.5 |
| Knight's Sword | 12-18       | 6      | Critical x1.5 |
| Dragon Slayer  | 15-25       | 7      | +10 damage vs. dragons |
| Flame Sword    | 12-20       | 6      | Fire damage, melts ice |
| Ice Blade      | 12-20       | 6      | Ice damage, freezes enemies |
| Holy Sword     | 18-30       | 7      | +15 damage vs. undead |

### Weapon Special Attributes
| Attribute      | Effect                          | Rarity |
|----------------|--------------------------------|--------|
| Cursed         | -5 damage, cannot be unequipped | Common |
| Blessed        | +5 damage                       | Uncommon |
| Accurate       | +10% hit chance                 | Uncommon |
| Vampiric       | Drains 10% of damage as health  | Rare |
| Sharpened      | +3 damage                       | Common |
| Rusted         | -3 damage                       | Common |

## Armor

### Armor Types and Defense Values
| Armor Type     | Defense Value | Weight | Special Properties |
|----------------|---------------|--------|-------------------|
| Cloth Robe     | 1             | 1      | None |
| Leather Armor  | 2-3           | 2      | None |
| Chain Mail     | 4-5           | 3      | -1 Dexterity |
| Scale Mail     | 6-7           | 4      | -1 Dexterity |
| Breast Plate   | 8-10          | 5      | -2 Dexterity |
| Full Plate     | 12-15         | 6      | -3 Dexterity |
| Magic Robe     | 8-12          | 2      | +5 Magic Defense |
| Dragon Mail    | 15-20         | 5      | Fire Resistance |
| Crystal Armor  | 18-25         | 4      | +10 Magic Defense |
| Holy Armor     | 20-25         | 6      | Undead Resistance |

### Armor Special Attributes
| Attribute      | Effect                           | Rarity |
|----------------|----------------------------------|--------|
| Cursed         | -5 defense, cannot be unequipped | Common |
| Blessed        | +5 defense                       | Uncommon |
| Fireproof      | 50% fire damage reduction        | Uncommon |
| Lightweight    | -2 Weight                        | Uncommon |
| Sturdy         | +3 defense                       | Common |
| Corroded       | -3 defense                       | Common |

## Items and Scrolls

### Potions
| Potion Type      | Effect                           | Rarity |
|------------------|----------------------------------|-------|
| Healing Potion   | Restores 25 HP                   | Common |
| Greater Healing  | Restores 100 HP                  | Uncommon |
| Full Healing     | Restores all HP                  | Rare |
| Strength Potion  | +1 Strength, permanent           | Rare |
| Defense Potion   | +1 Defense, permanent            | Rare |
| Poison           | Lose 10 HP, poisoned for 5 turns | -     |
| Slowness         | Movement speed halved for 10 turns | -   |
| Blindness        | Vision range reduced for 15 turns | -   |
| Invisibility     | Monsters can't see you for 20 turns | Very Rare |
| Fire Resistance  | 50% fire damage reduction for 30 turns | Rare |
| Identify         | Identifies one unidentified item | Uncommon |

### Scrolls
| Scroll Type     | Effect                           | Rarity |
|-----------------|----------------------------------|-------|
| Teleport        | Random teleport on current floor | Uncommon |
| Enchant Weapon  | +2 to equipped weapon's damage   | Rare |
| Enchant Armor   | +2 to equipped armor's defense   | Rare |
| Remove Curse    | Removes curse from equipped items | Uncommon |
| Magic Mapping   | Reveals entire floor map         | Uncommon |
| Identify All    | Identifies all carried items     | Rare |
| Create Monster  | Spawns 1-3 random monsters       | -     |
| Fireball        | Deals 50 fire damage to all visible enemies | Rare |
| Ice Blast       | Deals 40 ice damage and slows all visible enemies | Rare |
| Divine Blessing | All equipped items become blessed | Very Rare |

### Rings and Amulets
| Item Type         | Effect                           | Rarity |
|-------------------|----------------------------------|-------|
| Ring of Strength  | +3 Strength while equipped       | Rare |
| Ring of Defense   | +3 Defense while equipped        | Rare |
| Ring of Health    | +20 Max HP while equipped        | Rare |
| Ring of Sustenance| Food depletes 50% slower         | Very Rare |
| Ring of Searching | Automatically reveals traps      | Uncommon |
| Amulet of Life    | Resurrect once with 50% HP       | Extremely Rare |
| Amulet of Speed   | Movement speed +50%              | Very Rare |
| Amulet of Mana    | Magic recovery rate +100%        | Very Rare |

## Food and Hunger System

### Hunger Levels
| Hunger Level | Food Value | Effect |
|--------------|------------|--------|
| Stuffed      | 80-100     | HP regenerates +1 per 5 turns |
| Satiated     | 60-79      | Normal state |
| Hungry       | 30-59      | No HP regeneration |
| Very Hungry  | 10-29      | Lose 1 HP every 20 turns |
| Starving     | 1-9        | Lose 1 HP every 5 turns |
| Dead         | 0          | Die from starvation |

### Food Items
| Food Type      | Food Value | Other Effects | Rarity |
|----------------|------------|---------------|-------|
| Bread          | +15        | None          | Common |
| Meat           | +25        | +5 HP         | Common |
| Ration         | +40        | None          | Common |
| Apple          | +10        | +2 HP         | Common |
| Magic Fruit    | +20        | +10 HP, cures poison | Uncommon |
| Royal Feast    | +100       | +25 HP, +1 strength | Rare |
| Rotten Food    | +5         | 50% chance of poison | -     |
| Moldy Bread    | +3         | 75% chance of poison | -     |

### Actions that Deplete Food
| Action                  | Food Cost |
|-------------------------|-----------|
| Each turn (time passing)| -0.1      |
| Walking one tile        | -0.2      |
| Running one tile        | -0.4      |
| Attacking               | -0.5      |
| Casting a spell         | -1 to -5  |
| Going down stairs       | -2        |
| Healing naturally       | -0.3 per HP|

## Monsters

### Monster Strength by Dungeon Level
| Dungeon Level | Monster Level Range | Number of Monsters |
|---------------|---------------------|-------------------|
| 1-3           | 1-4                 | 3-7               |
| 4-6           | 3-8                 | 4-9               |
| 7-10          | 6-12                | 5-11              |
| 11-15         | 10-18               | 6-12              |
| 16-20         | 15-25               | 7-14              |
| 21-25         | 20-30               | 8-15              |
| 26-30         | 25-35               | 9-17              |

### Monster Types
| Monster Type   | HP    | Attack | Defense | Special Abilities | Experience |
|----------------|-------|--------|---------|-------------------|---------|
| Slime          | 5-10  | 2-4    | 0       | Splits when hit   | 5 XP    |
| Rat            | 3-8   | 3-5    | 1       | None              | 5 XP    |
| Bat            | 5-12  | 4-7    | 1       | Fast movement     | 12 XP   |
| Skeleton       | 12-18 | 6-10   | 3       | Undead            | 20 XP   |
| Zombie         | 15-25 | 8-12   | 4       | Undead, poisonous | 35 XP   |
| Orc            | 20-30 | 10-15  | 5       | None              | 45 XP   |
| Goblin         | 15-22 | 8-12   | 3       | Steals items      | 30 XP   |
| Ogre           | 35-50 | 15-25  | 8       | None              | 100 XP  |
| Troll          | 50-75 | 20-30  | 12      | Regenerates HP    | 200 XP  |
| Dragon         | 100-200| 30-50  | 20      | Breathes fire     | 500 XP  |
| Evil Knight    | 80-120| 25-40  | 15      | Blocks attacks    | 350 XP  |
| Necromancer    | 60-90 | 15-25  | 10      | Summons undead    | 300 XP  |
| Mimic          | 40-60 | 20-30  | 10      | Disguised as chest| 150 XP  |
| Ghost          | 30-45 | 15-25  | 5       | Phasing movement  | 120 XP  |
| Demon          | 120-180| 30-45 | 18      | Fire attacks      | 450 XP  |

### Monster Behavior Types
| Behavior Type | Description |
|---------------|-------------|
| Passive       | Only attacks if attacked first |
| Aggressive    | Attacks player on sight |
| Territorial   | Only attacks if player enters its territory |
| Cowardly      | Runs away when health is low |
| Erratic       | Random movement patterns |
| Hunter        | Actively pursues player through the dungeon |
| Ambusher      | Waits in hidden spots to surprise attack |
| Swarm         | Coordinates attacks with similar monsters |

## Magic and Spells

### Spell Types and Effects
| Spell Name      | MP Cost | Effect                         | Level Required |
|-----------------|---------|--------------------------------|----------------|
| Magic Arrow     | 3       | 5-10 damage, never misses      | 1              |
| Heal            | 5       | Restore 20 HP                  | 2              |
| Light           | 4       | Reveals surrounding area       | 3              |
| Shield          | 6       | +5 Defense for 20 turns        | 4              |
| Fireball        | 8       | 15-25 damage in area           | 5              |
| Ice Bolt        | 7       | 12-20 damage, chance to freeze | 6              |
| Levitation      | 10      | Avoid floor traps for 40 turns | 7              |
| Lightning       | 12      | 20-40 damage, chains to targets| 8              |
| Teleport        | 15      | Teleport to random location    | 9              |
| Earthquake      | 20      | 15-30 damage to all enemies    | 10             |
| Identify        | 8       | Identify one item              | 5              |
| Fear            | 10      | Enemies flee for 10 turns      | 7              |
| Summon Ally     | 18      | Summons a friendly creature    | 12             |
| Stone to Flesh  | 12      | Cures petrification            | 8              |

### Magic Staves and Wands
| Item            | Charges | Effect                          | Rarity |
|-----------------|---------|--------------------------------|--------|
| Wand of Fire    | 5-10    | Fireball spell                  | Rare   |
| Wand of Ice     | 5-10    | Ice Bolt spell                  | Rare   |
| Wand of Healing | 3-8     | Heal spell                      | Rare   |
| Staff of Light  | 10-20   | Light spell                     | Uncommon |
| Staff of Power  | 3-6     | Lightning spell                 | Very Rare |


## Dungeon Generation

### Floor Types and Features
| Floor Level | Room Count | Special Features | Treasure | Shop Chance |
|-------------|------------|------------------|---------|-------------|
| 1-5         | 5-10       | None             | 1-3 items | 20%       |
| 6-10        | 8-15       | Water pools      | 2-4 items | 15%       |
| 11-15       | 10-18      | Lava, chasms     | 3-6 items | 10%       |
| 16-20       | 12-20      | Teleport traps   | 4-7 items | 5%        |
| 21-25       | 15-25      | All traps        | 5-8 items | 3%        |
| 26-30       | 15-25      | Dark areas       | 6-10 items | 1%       |

### Room Types and Probabilities
| Room Type     | Probability | Special Properties |
|---------------|-------------|-------------------|
| Standard      | 60%         | None |
| Circular      | 10%         | Better for combat maneuvering |
| Large Hall    | 5%          | More monsters, more treasure |
| Storage Room  | 10%         | Higher item chance |
| Flooded Room  | 5%          | Slows movement |
| Trapped Room  | 5%          | Contains multiple traps |
| Library       | 2%          | Scroll chance increased |
| Armory        | 2%          | Weapon/armor chance increased |
| Treasure Room | 1%          | Guaranteed treasure, often guarded |

### Trap Types and Effects
| Trap Type     | Effect                          | Detection Difficulty |
|---------------|--------------------------------|----------------------|
| Pit           | 1-10 damage, fall to next floor| Easy                 |
| Dart          | 2-8 damage, poison chance      | Medium               |
| Alarm         | Summons nearby monsters        | Easy                 |
| Gas           | Poison, blindness, or confusion| Medium               |
| Teleport      | Random teleport on current level| Hard                |
| Blade         | 5-15 damage                    | Medium               |
| Bear Trap     | 3-6 damage, immobilized 5 turns| Easy                 |
| Lightning     | 10-25 damage                   | Hard                 |
| Polymorph     | Transforms random item or monster| Very Hard           |
| Disintegration| Destroys random equipped item  | Very Hard            |

### Special Floor Elements
| Element        | Effect                         | Rarity |
|----------------|--------------------------------|--------|
| Healing Fountain| Restores full HP when used    | Very Rare |
| Mysterious Altar| Can bless or curse equipment  | Rare |
| Magic Portal   | Teleports to special area      | Very Rare |
| Enchanted Forge| Can upgrade weapons/armor      | Extremely Rare |
| Training Dummy | Gain experience by practicing  | Rare |
| Forbidden Library| Learn new spells             | Extremely Rare |
| Treasure Vault | Rare and powerful items | Very Rare |

## Controls

Craven Caverns uses a simple and intuitive control scheme similar to Fatal Labyrinth, adapted for the NES controller:

### Movement Controls
| Control | Action |
|---------|--------|
| D-Pad   | Move player in four directions. attack adjacent enemy if in that direction. |
| B button | pass a turn |
| A button | pick up item on ground same tile as player |


### Menu Controls
| Control | Action |
|---------|--------|
| START button | Open inventory menu |
| SELECT button | Toggle information display |
| D-Pad | Navigate menus |
| A button | Confirm selection |
| B button | Cancel/Go back |

### Inventory Actions
| Control | Action |
|---------|--------|
| A button while on item | Show item options (Use, Drop, Throw, Equip) |
| B button while in inventory | Exit inventory |

The game follows a turn-based system where each action (movement, attack, using items) counts as one turn, after which enemies can move and act.

## Screen Layout and Grid Design

Craven Caverns follows a visual structure similar to Arkista's Ring on the NES:

### Display Grid
| Dimension | Size | Description |
|-----------|------|-------------|
| Width     | 16 tiles | Game world horizontal view |
| Height    | 11 tiles total | 7-8 tiles for gameplay area, 3-4 tiles for UI |

### UI Layout (Bottom Area)
| Element | Position | Description |
|---------|----------|-------------|
| Item Slots | Left side | Currently equipped/active items |
| Hearts | Right side | Player health represented as heart icons |
| Score/Stats | Bottom right | Numerical display of relevant stats |

### Gameplay Area
- **Visible Area**: The player can see approximately 16×7 tiles around their position
- **Scroll Behavior**: Screen centers on player when possible, scrolls when approaching map edges
- **Tile Size**: 16×16 pixels for consistent NES-style appearance

This documentation covers the core gameplay systems for Craven Caverns, providing a solid foundation for implementing a roguelike inspired by Fatal Labyrinth with the visual style of Arkista's Ring.
