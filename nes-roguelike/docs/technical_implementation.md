# Craven Caverns - Technical Implementation Guide

This document provides technical details for implementing the Fatal Labyrinth-inspired gameplay systems in NES assembly.

## Memory Layout

### Zero Page Variables (High-Priority Variables)

```assembly
.segment "ZEROPAGE"
; Player Stats
player_x:        .res 1  ; Player X position on current map
player_y:        .res 1  ; Player Y position
player_hp:       .res 2  ; Current HP (16-bit)
player_max_hp:   .res 2  ; Maximum HP (16-bit)
player_str:      .res 1  ; Strength
player_def:      .res 1  ; Defense
player_level:    .res 1  ; Experience level
player_food:     .res 1  ; Food level
player_xp:       .res 3  ; Experience points (24-bit)
player_gold:     .res 3  ; Gold (24-bit)
player_dir:      .res 1  ; Direction (0=down, 1=up, 2=right, 3=left)
player_state:    .res 1  ; State bitfield (bit 0=poisoned, 1=confused, etc.)

; Game State
current_floor:   .res 1  ; Current dungeon floor
game_flags:      .res 1  ; Game state flags
turn_counter:    .res 2  ; Count of turns passed (16-bit)
rng_seed:        .res 2  ; Random number generator seed

; Temporary variables for calculations
temp1:           .res 1
temp2:           .res 1
pointer_lo:      .res 1  ; Low byte of memory pointer
pointer_hi:      .res 1  ; High byte of memory pointer
```

### RAM Variables

```assembly
.segment "RAM"
; Map data
map_data:        .res 240  ; 16x15 map (screen size)
map_flags:       .res 240  ; Tile flags (bit 0=explored, 1=visible, etc.)
map_objects:     .res 240  ; Objects on map (items, traps, etc.)

; Monster data (8 monsters max)
monster_type:    .res 8    ; Monster type
monster_x:       .res 8    ; X position
monster_y:       .res 8    ; Y position
monster_hp:      .res 8    ; Current HP
monster_state:   .res 8    ; State (active, sleeping, etc.)

; Inventory (12 slots)
inv_type:        .res 12   ; Item type
inv_subtype:     .res 12   ; Item subtype
inv_quantity:    .res 12   ; Quantity
inv_flags:       .res 12   ; Flags (identified, cursed, etc.)

; Equipment slots
equip_weapon:    .res 1    ; Equipped weapon slot
equip_armor:     .res 1    ; Equipped armor slot
equip_ring1:     .res 1    ; Equipped ring 1
equip_ring2:     .res 1    ; Equipped ring 2
equip_amulet:    .res 1    ; Equipped amulet

; Game UI variables
ui_selection:    .res 1    ; Current menu selection
ui_state:        .res 1    ; UI state
ui_message:      .res 32   ; Message buffer
```

## Data Tables

### Experience Level Requirements Table

```assembly
.segment "RODATA"
; Experience points needed for each level (24-bit values)
; Format: Low byte, middle byte, high byte
xp_level_table:
    .byte $0A, $00, $00   ; Level 2 - 10 XP
    .byte $19, $00, $00   ; Level 3 - 25 XP
    .byte $32, $00, $00   ; Level 4 - 50 XP
    .byte $64, $00, $00   ; Level 5 - 100 XP
    .byte $96, $00, $00   ; Level 6 - 150 XP
    .byte $FA, $00, $00   ; Level 7 - 250 XP
    .byte $90, $01, $00   ; Level 8 - 400 XP
    .byte $8A, $02, $00   ; Level 9 - 650 XP
    .byte $E8, $03, $00   ; Level 10 - 1,000 XP
    ; Additional levels follow
```

### Stat Growth Tables

```assembly
; HP gain per level (min, max)
hp_gain_table:
    .byte 5, 8    ; Levels 1-10
    .byte 8, 12   ; Levels 11-20
    .byte 10, 15  ; Levels 21-30
    .byte 12, 18  ; Levels 31-40
    .byte 15, 20  ; Levels 41-50

; Strength gain per level (min, max)
str_gain_table:
    .byte 1, 1    ; Levels 1-10
    .byte 1, 2    ; Levels 11-20
    .byte 2, 2    ; Levels 21-30
    .byte 2, 3    ; Levels 31-40
    .byte 3, 3    ; Levels 41-50

; Defense gain per level (min, max)
def_gain_table:
    .byte 0, 1    ; Levels 1-10 (50% chance)
    .byte 0, 1    ; Levels 11-20 (50% chance)
    .byte 1, 1    ; Levels 21-30
    .byte 1, 2    ; Levels 31-40
    .byte 2, 2    ; Levels 41-50
```

### Weapon Data Table

```assembly
; Weapon data table
; Format: Base Min Damage, Base Max Damage, Weight, Special Properties
weapon_data:
    .byte 1, 2, 1, 0      ; Wooden Dagger
    .byte 2, 5, 2, 0      ; Short Sword
    .byte 5, 9, 3, 0      ; Iron Sword
    .byte 7, 12, 4, 0     ; Broad Sword
    .byte 10, 15, 5, 1    ; Fighter's Sword (Special: Crit x1.5)
    .byte 12, 18, 6, 1    ; Knight's Sword (Special: Crit x1.5)
    .byte 15, 25, 7, 2    ; Dragon Slayer (Special: +10 vs dragon)
    .byte 12, 20, 6, 3    ; Flame Sword (Special: Fire damage)
    .byte 12, 20, 6, 4    ; Ice Blade (Special: Ice damage)
    .byte 18, 30, 7, 5    ; Holy Sword (Special: +15 vs undead)
```

### Armor Data Table

```assembly
; Armor data table
; Format: Min Defense, Max Defense, Weight, Special Properties
armor_data:
    .byte 1, 1, 1, 0      ; Cloth Robe
    .byte 2, 3, 2, 0      ; Leather Armor
    .byte 4, 5, 3, 1      ; Chain Mail (Special: -1 Dex)
    .byte 6, 7, 4, 1      ; Scale Mail (Special: -1 Dex)
    .byte 8, 10, 5, 2     ; Breast Plate (Special: -2 Dex)
    .byte 12, 15, 6, 3    ; Full Plate (Special: -3 Dex)
    .byte 8, 12, 2, 4     ; Magic Robe (Special: +5 Magic Def)
    .byte 15, 20, 5, 5    ; Dragon Mail (Special: Fire Resist)
    .byte 18, 25, 4, 6    ; Crystal Armor (Special: +10 Magic Def)
    .byte 20, 25, 6, 7    ; Holy Armor (Special: Undead Resist)
```

### Monster Data Table

```assembly
; Monster data table
; Format: Min HP, Max HP, Min Attack, Max Attack, Defense, Special Abilities, XP Value
monster_data:
    .byte 5, 10, 2, 4, 0, 1, 5     ; Slime (Special: Splits)
    .byte 3, 8, 3, 5, 1, 0, 8      ; Rat
    .byte 5, 12, 4, 7, 1, 2, 12    ; Bat (Special: Fast movement)
    .byte 12, 18, 6, 10, 3, 3, 20  ; Skeleton (Special: Undead)
    .byte 15, 25, 8, 12, 4, 4, 35  ; Zombie (Special: Undead, poison)
    .byte 20, 30, 10, 15, 5, 0, 45 ; Orc
    .byte 15, 22, 8, 12, 3, 5, 30  ; Goblin (Special: Steals gold)
    .byte 35, 50, 15, 25, 8, 0, 100 ; Ogre
    .byte 50, 75, 20, 30, 12, 6, 200 ; Troll (Special: Regenerates)
    .byte 100, 200, 30, 50, 20, 7, 500 ; Dragon (Special: Fire breath)
```

### Item and Scroll Data

```assembly
; Potion data table
; Format: Effect Value, Secondary Effect, Value
potion_data:
    .byte 25, 0, 50       ; Healing Potion (Restores 25 HP)
    .byte 100, 0, 150     ; Greater Healing (Restores 100 HP)
    .byte 255, 0, 300     ; Full Healing (Restores all HP)
    .byte 1, 0, 200       ; Strength Potion (+1 STR)
    .byte 1, 1, 200       ; Defense Potion (+1 DEF)
    .byte 10, 2, 0        ; Poison (Lose 10 HP, poisoned)
    .byte 10, 3, 0        ; Slowness (Movement halved)
    .byte 15, 4, 0        ; Blindness (Vision reduced)
    .byte 20, 5, 300      ; Invisibility (Monsters can't see)
    .byte 30, 6, 200      ; Fire Resistance (50% fire reduction)
    .byte 1, 7, 100       ; Identify (Identifies one item)

; Scroll data table
; Format: Effect Type, Effect Value, Value
scroll_data:
    .byte 0, 0, 80        ; Teleport
    .byte 1, 2, 200       ; Enchant Weapon (+2 damage)
    .byte 2, 2, 200       ; Enchant Armor (+2 defense)
    .byte 3, 0, 150       ; Remove Curse
    .byte 4, 0, 120       ; Magic Mapping
    .byte 5, 0, 300       ; Identify All
    .byte 6, 3, 0         ; Create Monster (1-3 monsters)
    .byte 7, 50, 250      ; Fireball (50 fire damage)
    .byte 8, 40, 250      ; Ice Blast (40 ice damage)
    .byte 9, 0, 500       ; Divine Blessing
```

## Key Algorithms

### Random Number Generation

```assembly
; Generate a random number
; Inputs: None
; Outputs: A = random number 0-255
; Modifies: A, X
.proc generate_random
    ; Simple LFSR (Linear Feedback Shift Register) for pseudo-random numbers
    LDA rng_seed
    LSR A
    BCC skip_eor
    EOR #$D4        ; Apply feedback polynomial
skip_eor:
    STA rng_seed
    RTS
.endproc

; Generate a random number in a range
; Inputs: X = min value, Y = max value
; Outputs: A = random number X to Y inclusive
; Modifies: A, temp1
.proc random_range
    STX temp1       ; Store min value
    TYA
    SEC
    SBC temp1       ; A = max - min
    TAX             ; X = range
    INX             ; X = range + 1
    JSR generate_random  ; Get random number in A
    ; Divide by 256/range to get 0 to range-1
    CPX #$00        ; Special case: if range = 256, just return A
    BEQ full_range
    ; Integer division by repeated subtraction (for small ranges)
    TXA
    STA temp1
    LDA #$00
divide_loop:
    CLC
    ADC temp1
    BCS divide_done  ; If we carried, we're done
    CMP #$FF
    BCC divide_loop  ; Keep going if we haven't reached 255
divide_done:
    LDA generate_random
    CMP temp1
    BCS divide_loop  ; If A >= divisor, try again
    ; Add the minimum value
    ADC temp1       ; A = random in range 0 to range-1
full_range:
    RTS
.endproc
```

### Damage Calculation

```assembly
; Calculate physical damage
; Inputs: 
;   X = attacker strength
;   Y = weapon damage
;   temp1 = defender defense
; Outputs: A = final damage
; Modifies: A, X, Y, temp2
.proc calculate_damage
    ; Base damage = Strength + Weapon
    TXA            ; A = strength
    CLC
    ADC weapon_damage  ; A = strength + weapon
    
    ; Generate random variance (±10%)
    STA temp2       ; Save base damage
    LSR A           ; A = base damage / 2
    LSR A           ; A = base damage / 4
    LSR A           ; A = base damage / 8 (about 12%)
    TAY             ; Y = variance range
    BNE has_variance
    LDY #$01        ; Minimum variance of 1
has_variance:
    STY temp2
    LDA #$00
    SEC
    SBC temp2       ; A = -variance
    TAX             ; X = -variance
    LDY temp2       ; Y = +variance  
    JSR random_range  ; Get random number between -variance and +variance
    
    ; Apply variance to base damage
    CLC
    ADC temp2       ; A = base damage + random variance
    
    ; Subtract defense (but ensure minimum 1 damage)
    SEC 
    SBC temp1       ; A = damage - defense
    BCS damage_positive
    LDA #$01        ; Minimum 1 damage
damage_positive:
    RTS
.endproc
```

### Level Up Processing

```assembly
; Process level up
; Inputs: None (uses player_level)
; Outputs: None (updates player stats)
; Modifies: A, X, Y, temp1, temp2
.proc process_level_up
    ; Get index into stat growth tables
    LDA player_level
    SEC
    SBC #$01        ; Level - 1
    LSR A           ; (Level - 1) / 2
    LSR A           ; (Level - 1) / 4
    LSR A           ; (Level - 1) / 8
    TAX             ; X = table index
    
    ; HP Gain
    LDA hp_gain_table, X     ; Min HP gain
    TAY                      ; Y = min HP
    LDA hp_gain_table+1, X   ; Max HP gain 
    TAX                      ; X = max HP
    JSR random_range         ; A = random HP gain
    
    ; Add to max HP (16-bit addition)
    CLC
    ADC player_max_hp
    STA player_max_hp
    LDA player_max_hp+1
    ADC #$00                 ; Add carry
    STA player_max_hp+1
    
    ; Strength gain
    LDX player_level
    DEX
    TXA
    LSR A
    LSR A
    LSR A
    TAX                      ; X = table index
    
    LDA str_gain_table, X    ; Min STR gain
    TAY                      ; Y = min STR
    LDA str_gain_table+1, X  ; Max STR gain
    TAX                      ; X = max STR
    JSR random_range         ; A = random STR gain
    
    ; Add to strength
    CLC
    ADC player_str
    STA player_str
    
    ; Defense gain (similar to above)
    ; ...
    
    ; Set HP to full
    LDA player_max_hp
    STA player_hp
    LDA player_max_hp+1
    STA player_hp+1
    
    RTS
.endproc
```

### Food Consumption

```assembly
; Process food consumption for a turn
; Inputs: None
; Outputs: None (updates player_food)
; Modifies: A, X, flags
.proc process_food
    ; Standard turn consumption
    LDA player_food
    SEC
    SBC #$01        ; Subtract 1 food point (out of 100)
    BCS not_zero
    LDA #$00        ; Prevent underflow
not_zero:
    STA player_food
    
    ; Check hunger status and apply effects
    CMP #$0A        ; Check if starving (< 10)
    BCS not_starving
    
    ; Handle starving effects
    LDA turn_counter
    AND #$04        ; Every 5th turn when starving
    BNE no_hp_loss
    
    ; Lose 1 HP from starvation
    LDA player_hp
    SEC
    SBC #$01
    STA player_hp
    LDA player_hp+1
    SBC #$00        ; Subtract carry
    STA player_hp+1
    
    ; Check if dead
    ORA player_hp
    BNE no_hp_loss
    ; Handle death
    JMP player_died
    
no_hp_loss:
not_starving:
    RTS
.endproc
```

### Monster AI Routine

```assembly
; Process monster turn
; Inputs: X = monster index
; Outputs: None
; Modifies: A, X, Y, various temp variables
.proc process_monster_turn
    ; Check if monster is active
    LDA monster_state, X
    AND #$01
    BEQ done        ; Skip inactive monsters
    
    ; Get monster position
    LDA monster_x, X
    STA temp1
    LDA monster_y, X
    STA temp2
    
    ; Check distance to player
    SEC
    LDA temp1
    SBC player_x
    BCS no_abs1
    EOR #$FF
    ADC #$01        ; 2's complement for absolute value
no_abs1:
    STA temp1       ; |monster_x - player_x|
    
    SEC
    LDA temp2
    SBC player_y
    BCS no_abs2
    EOR #$FF
    ADC #$01        ; 2's complement for absolute value
no_abs2:
    STA temp2       ; |monster_y - player_y|
    
    ; Manhattan distance = |x1-x2| + |y1-y2|
    LDA temp1
    CLC
    ADC temp2
    STA temp1       ; temp1 = distance to player
    
    ; Check if player is visible
    CMP #$08        ; Within 8 tiles?
    BCS too_far
    
    ; Behavior based on monster type
    LDY monster_type, X
    LDA monster_behavior, Y
    AND #$0F        ; Get behavior type
    
    ; Different movement patterns based on behavior
    CMP #$00        ; Passive
    BEQ passive_move
    CMP #$01        ; Aggressive
    BEQ aggressive_move
    ; Other behaviors...
    
aggressive_move:
    ; Try to move toward player
    LDA monster_x, X
    CMP player_x
    BEQ same_x
    BCS move_left
    ; Move right
    INC monster_x, X
    JMP check_y
move_left:
    DEC monster_x, X
    
check_y:
same_x:
    LDA monster_y, X
    CMP player_y
    BEQ done
    BCS move_up
    ; Move down
    INC monster_y, X
    JMP done
move_up:
    DEC monster_y, X
    JMP done
    
passive_move:
    ; Random movement or stay still
    JSR generate_random
    AND #$07        ; 0-7
    CMP #$05        ; 5/8 chance to stay still
    BCS done
    
    ; Random direction 0-3
    JSR generate_random
    AND #$03
    ; Move based on direction
    ; ...
    
too_far:
    ; Random wandering for monsters out of view
    JSR generate_random
    AND #$0F        ; 0-15
    CMP #$03        ; 3/16 chance to move
    BCS done
    
    ; Random direction 0-3
    JSR generate_random
    AND #$03
    ; Move based on direction
    ; ...
    
done:
    RTS
.endproc
```

### Dungeon Generation

```assembly
; Generate a new dungeon floor
; Inputs: A = floor number
; Outputs: None (fills map_data)
; Modifies: Many variables
.proc generate_dungeon
    STA current_floor
    
    ; Clear the map
    LDX #$00
    LDA #$00        ; Empty space
clear_loop:
    STA map_data, X
    STA map_flags, X
    STA map_objects, X
    INX
    CPX #$F0        ; 240 tiles
    BNE clear_loop
    
    ; Determine number of rooms based on floor
    LDA current_floor
    CMP #$06        ; Floor 6+
    BCC early_floors
    CMP #$10        ; Floor 16+
    BCC mid_floors
    LDX #$0F        ; Min 15 rooms
    LDY #$19        ; Max 25 rooms
    JMP got_room_range
    
mid_floors:
    LDX #$0A        ; Min 10 rooms
    LDY #$12        ; Max 18 rooms
    JMP got_room_range
    
early_floors:
    LDX #$05        ; Min 5 rooms
    LDY #$0A        ; Max 10 rooms
    
got_room_range:
    JSR random_range
    STA temp1       ; Number of rooms to generate
    
    ; Create rooms
    LDX #$00        ; Room counter
create_rooms_loop:
    CPX temp1
    BEQ rooms_done
    
    ; Random room position and size
    ; ...
    
    ; Connect rooms with corridors
    ; ...
    
    INX
    JMP create_rooms_loop
    
rooms_done:
    ; Place stairs down
    ; ...
    
    ; Place monsters
    JSR place_monsters
    
    ; Place items
    JSR place_items
    
    ; Place player at stairs up position
    ; ...
    
    RTS
.endproc
```

## File Organization

The code should be organized into several logical files:

### Main Engine Files
- `main.s` - Main game loop, initialization
- `player.s` - Player movement, inventory, stats
- `monsters.s` - Monster AI, combat
- `items.s` - Item handling, effects
- `dungeon.s` - Dungeon generation, floors
- `ui.s` - User interface, menus
- `render.s` - Graphics rendering

### Data Files
- `constants.inc` - Game constants
- `tables.s` - Data tables for game mechanics
- `text.s` - Text strings and messages
- `graphics.s` - Graphic tile references

### Assembly Structure for Object-Oriented Approach

Even though 6502 assembly doesn't have object-oriented features, we can structure the code to mimic object-oriented design:

```assembly
; Entity system - each object has a type and related data
; Entity types:
; 0 = Empty
; 1 = Player
; 2-15 = Monster types
; 16-31 = Item types
; 32-47 = Environment objects

; Process turn for all entities
.proc process_turn
    ; Process player
    JSR process_player_turn
    
    ; Process monsters
    LDX #$00
monster_loop:
    CPX #$08        ; Up to 8 monsters
    BEQ monsters_done
    LDA monster_state, X
    BEQ next_monster
    JSR process_monster_turn
next_monster:
    INX
    JMP monster_loop
monsters_done:
    
    ; Process environment (traps, etc.)
    JSR process_environment
    
    ; Increment turn counter
    INC turn_counter
    BNE :+
    INC turn_counter+1
:
    RTS
.endproc
```

## Performance Considerations

- **Optimize map checks**: Use lookup tables for map access rather than multiplication
- **Limit active monsters**: Only process monsters within a certain distance of player
- **Split processing across frames**: Don't try to do everything in one frame
- **Precalculate values**: Use tables for values that would require complex calculation
- **Minimize division**: Use bit shifting and subtraction where possible
- **Store values efficiently**: Pack flags into bitfields to save memory

## Memory Management

- Use the zero page for frequently accessed variables
- Split the dungeon map into chunks if needed for larger maps
- Use RLE (Run-Length Encoding) for compressed map storage
- Reuse memory between different game states
- Store static data in ROM (RODATA segment)

This technical guide should help you implement the Fatal Labyrinth-inspired gameplay systems in your NES assembly code, while leveraging the visual style of Arkista's Ring.
