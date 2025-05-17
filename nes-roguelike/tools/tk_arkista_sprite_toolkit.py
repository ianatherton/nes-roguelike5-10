#!/usr/bin/env python3
"""
Arkista Sprite Toolkit: Enhanced Edition
----------------------------------
A comprehensive all-in-one application for managing NES sprite assets.
Features include:
- Sprite extraction, editing, and management
- Sprite categorization and tagging
- Animation sequence creation
- Metadata database integration
- Asset wizard for creating new game entities
- Export to game engine compatible formats
"""

import os
import sys
import json
import sqlite3
import uuid
import datetime
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
from tkinter.font import Font
from PIL import Image, ImageTk, ImageDraw
import shutil
from pathlib import Path

# NES palette (first 64 colors)
NES_PALETTE = [
    (124, 124, 124), (0, 0, 252), (0, 0, 188), (68, 40, 188), (148, 0, 132), (168, 0, 32),
    (168, 16, 0), (136, 20, 0), (80, 48, 0), (0, 120, 0), (0, 104, 0), (0, 88, 0),
    (0, 64, 88), (0, 0, 0), (0, 0, 0), (0, 0, 0), (188, 188, 188), (0, 120, 248),
    (0, 88, 248), (104, 68, 252), (216, 0, 204), (228, 0, 88), (248, 56, 0),
    (228, 92, 16), (172, 124, 0), (0, 184, 0), (0, 168, 0), (0, 168, 68), (0, 136, 136),
    (0, 0, 0), (0, 0, 0), (0, 0, 0), (248, 248, 248), (60, 188, 252), (104, 136, 252),
    (152, 120, 248), (248, 120, 248), (248, 88, 152), (248, 120, 88), (252, 160, 68),
    (248, 184, 0), (184, 248, 24), (88, 216, 84), (88, 248, 152), (0, 232, 216),
    (120, 120, 120), (0, 0, 0), (0, 0, 0), (252, 252, 252), (164, 228, 252),
    (184, 184, 248), (216, 184, 248), (248, 184, 248), (248, 164, 192), (240, 208, 176),
    (252, 224, 168), (248, 216, 120), (216, 248, 120), (184, 248, 184), (184, 248, 216),
    (0, 252, 252), (248, 216, 248), (0, 0, 0), (0, 0, 0)
]

# Asset Categories
ASSET_CATEGORIES = [
    "Player", "Enemy", "Item", "Environment", "UI", "Background", "Weapon", "Effect", "NPC", "Decoration"
]

# Animation Types
ANIMATION_TYPES = [
    "idle", "walk", "run", "attack", "death", "hurt", "jump", "fall", "cast", "special"
]

# Direction Types
DIRECTION_TYPES = ["down", "up", "left", "right", "none"]

# Database schema
DATABASE_SCHEMA = """
-- Assets table stores basic information about each sprite asset
CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    tags TEXT,
    chr_bank INTEGER,
    width INTEGER,
    height INTEGER,
    created_at TEXT,
    updated_at TEXT,
    file_path TEXT,
    preview_path TEXT
);

-- Sprites table stores individual sprite frames
CREATE TABLE IF NOT EXISTS sprites (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    name TEXT NOT NULL,
    animation_type TEXT,
    direction TEXT,
    frame_number INTEGER,
    base_tile INTEGER,
    tile_arrangement TEXT,
    file_path TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- Animations table stores animation sequences
CREATE TABLE IF NOT EXISTS animations (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT,
    direction TEXT,
    frames TEXT,
    frame_duration INTEGER,
    loop BOOLEAN,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- Configuration table for toolkit settings
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

class DatabaseManager:
    """SQLite database manager for sprite assets"""
    
    def __init__(self, db_path):
        """Initialize the database connection"""
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize the database if it doesn't exist"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create tables from schema
            cursor.executescript(DATABASE_SCHEMA)
            
            # Insert default configuration if not present
            cursor.execute("INSERT OR IGNORE INTO config VALUES (?, ?)", ("last_directory", ""))
            
            self.conn.commit()
            print(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
    
    def add_asset(self, asset):
        """Add or update an asset in the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO assets 
                (id, name, category, description, tags, chr_bank, width, height, created_at, updated_at, file_path, preview_path) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset.get("id", str(uuid.uuid4())),
                asset.get("name", ""),
                asset.get("category", "Unknown"),
                asset.get("description", ""),
                ",".join(asset.get("tags", [])),
                asset.get("chr_bank", 0),
                asset.get("width", 16),
                asset.get("height", 16),
                asset.get("created_at", datetime.datetime.now().isoformat()),
                datetime.datetime.now().isoformat(),
                asset.get("file_path", ""),
                asset.get("preview_path", "")
            ))
            self.conn.commit()
            return asset.get("id", str(uuid.uuid4()))
        except sqlite3.Error as e:
            print(f"Error adding asset: {e}")
            return None
    
    def add_sprite(self, sprite):
        """Add or update a sprite in the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sprites
                (id, asset_id, name, animation_type, direction, frame_number, base_tile, tile_arrangement, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sprite.get("id", str(uuid.uuid4())),
                sprite.get("asset_id", ""),
                sprite.get("name", ""),
                sprite.get("animation_type", ""),
                sprite.get("direction", ""),
                sprite.get("frame_number", 0),
                sprite.get("base_tile", 0),
                json.dumps(sprite.get("tile_arrangement", [0, 1, 2, 3])),
                sprite.get("file_path", "")
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding sprite: {e}")
            return False
    
    def add_animation(self, animation):
        """Add or update an animation in the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO animations
                (id, asset_id, name, type, direction, frames, frame_duration, loop)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                animation.get("id", str(uuid.uuid4())),
                animation.get("asset_id", ""),
                animation.get("name", ""),
                animation.get("type", ""),
                animation.get("direction", ""),
                json.dumps(animation.get("frames", [])),
                animation.get("frame_duration", 100),
                1 if animation.get("loop", True) else 0
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding animation: {e}")
            return False
    
    def get_all_assets(self, category=None):
        """Get all assets, optionally filtered by category"""
        try:
            cursor = self.conn.cursor()
            if category:
                cursor.execute("SELECT * FROM assets WHERE category = ?", (category,))
            else:
                cursor.execute("SELECT * FROM assets ORDER BY category, name")
            
            columns = [col[0] for col in cursor.description]
            result = []
            for row in cursor.fetchall():
                asset = dict(zip(columns, row))
                asset["tags"] = asset.get("tags", "").split(",") if asset.get("tags") else []
                result.append(asset)
            return result
        except sqlite3.Error as e:
            print(f"Error getting assets: {e}")
            return []
    
    def get_asset_by_id(self, asset_id):
        """Get a single asset by ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                asset = dict(zip(columns, row))
                asset["tags"] = asset.get("tags", "").split(",") if asset.get("tags") else []
                return asset
            return None
        except sqlite3.Error as e:
            print(f"Error getting asset: {e}")
            return None
    
    def get_sprites_for_asset(self, asset_id):
        """Get all sprites for a specific asset"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM sprites WHERE asset_id = ?", (asset_id,))
            
            columns = [col[0] for col in cursor.description]
            result = []
            for row in cursor.fetchall():
                sprite = dict(zip(columns, row))
                sprite["tile_arrangement"] = json.loads(sprite.get("tile_arrangement", "[0,1,2,3]"))
                result.append(sprite)
            return result
        except sqlite3.Error as e:
            print(f"Error getting sprites: {e}")
            return []
    
    def get_animations_for_asset(self, asset_id):
        """Get all animations for a specific asset"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM animations WHERE asset_id = ?", (asset_id,))
            
            columns = [col[0] for col in cursor.description]
            result = []
            for row in cursor.fetchall():
                animation = dict(zip(columns, row))
                animation["frames"] = json.loads(animation.get("frames", "[]"))
                animation["loop"] = bool(animation.get("loop", 1))
                result.append(animation)
            return result
        except sqlite3.Error as e:
            print(f"Error getting animations: {e}")
            return []
    
    def delete_asset(self, asset_id):
        """Delete an asset and all related sprites and animations"""
        try:
            cursor = self.conn.cursor()
            # Delete related sprites first
            cursor.execute("DELETE FROM sprites WHERE asset_id = ?", (asset_id,))
            # Delete related animations
            cursor.execute("DELETE FROM animations WHERE asset_id = ?", (asset_id,))
            # Delete the asset
            cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting asset: {e}")
            return False
    
    def search_assets(self, query):
        """Search assets by name, category, or tags"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM assets 
                WHERE name LIKE ? OR category LIKE ? OR tags LIKE ? 
                ORDER BY category, name
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            
            columns = [col[0] for col in cursor.description]
            result = []
            for row in cursor.fetchall():
                asset = dict(zip(columns, row))
                asset["tags"] = asset.get("tags", "").split(",") if asset.get("tags") else []
                result.append(asset)
            return result
        except sqlite3.Error as e:
            print(f"Error searching assets: {e}")
            return []

class ArkistaSpriteToolkit:
    """Main application for the Arkista Sprite Toolkit: Enhanced Edition"""
    
    def __init__(self, root):
        # Basic setup
        self.root = root
        self.root.title("Arkista Sprite Toolkit: Enhanced Edition")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Set application icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
            if os.path.exists(icon_path):
                icon = ImageTk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Create necessary directories
        self.app_dir = os.path.join(os.path.expanduser("~"), ".arkista_toolkit")
        os.makedirs(self.app_dir, exist_ok=True)
        
        # Database initialization
        self.db_path = os.path.join(self.app_dir, "sprite_database.db")
        self.db = DatabaseManager(self.db_path)
        
        # Common data that will be shared between tabs
        self.sprite_data = {}
        self.assets_dir = os.path.join(self.app_dir, "assets")
        os.makedirs(self.assets_dir, exist_ok=True)
        self.sprites_dir = os.path.join(self.assets_dir, "sprites")
        os.makedirs(self.sprites_dir, exist_ok=True)
        self.exports_dir = os.path.join(self.assets_dir, "exports")
        os.makedirs(self.exports_dir, exist_ok=True)
        
        self.base_directory = None
        self.current_asset = None
        self.current_sprite = None
        
        # Define standard sprite configurations
        self.sprite_configs = {
            "single": (1, 1),     # 1x1 (8x8) single sprite
            "double_h": (2, 1),   # 2x1 (16x8) horizontal double sprite
            "double_v": (1, 2),   # 1x2 (8x16) vertical double sprite
            "quad": (2, 2)        # 2x2 (16x16) quad sprite (standard character)
        }
        self.current_config = "quad"  # Default to quad sprites (16x16)
        self.tile_size = 8  # Standard NES tile size (8x8 pixels)
        
        # Styling options
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Use a modern theme
        
        # Configure custom styles
        self.style.configure("TButton", padding=6, relief="flat", foreground="#333333")
        self.style.configure("Primary.TButton", background="#4CAF50", foreground="white")
        self.style.map("Primary.TButton",
            foreground=[('pressed', 'white'), ('active', 'white')],
            background=[('pressed', '#3e8e41'), ('active', '#45a049')])
        
        self.style.configure("Secondary.TButton", background="#2196F3", foreground="white")
        self.style.map("Secondary.TButton",
            foreground=[('pressed', 'white'), ('active', 'white')],
            background=[('pressed', '#0b7dda'), ('active', '#0d8af0')])
        
        # Set up custom fonts
        self.header_font = Font(family="Helvetica", size=12, weight="bold")
        self.title_font = Font(family="Helvetica", size=14, weight="bold")
        self.label_font = Font(family="Helvetica", size=10)
        
        # App state variables
        self.wizard_active = False
        self.current_wizard_stage = 0
        self.wizard_data = {}
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main UI with tabs and wizard"""
        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create top bar with logo and controls
        self.create_top_bar()
        
        # Create notebook (tabs container)
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create main menu
        self.create_menu()
        
        # Create central tabs
        self.create_dashboard_tab()
        self.create_asset_manager_tab()
        self.create_sprite_editor_tab()
        self.create_animation_editor_tab()
        self.create_export_tab()
        
        # Create wizard container (initially hidden)
        self.wizard_container = ttk.Frame(self.main_container)
        
        # Create status bar
        self.create_status_bar()
        
    def create_top_bar(self):
        """Create the top application bar"""
        top_frame = ttk.Frame(self.main_container, padding="10 5 10 5")
        top_frame.pack(fill=tk.X)
        
        # App title
        title_label = ttk.Label(top_frame, text="Arkista Sprite Toolkit", font=self.title_font)
        title_label.pack(side=tk.LEFT, padx=10)
        
        # New Asset button
        new_asset_btn = ttk.Button(top_frame, text="New Asset", style="Primary.TButton", 
                               command=self.start_new_asset_wizard)
        new_asset_btn.pack(side=tk.RIGHT, padx=5)
        
        # Import button
        import_btn = ttk.Button(top_frame, text="Import Assets", style="Secondary.TButton",
                             command=self.import_assets)
        import_btn.pack(side=tk.RIGHT, padx=5)
        
        # Quick search
        ttk.Label(top_frame, text="Search:").pack(side=tk.RIGHT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.quick_search)
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.RIGHT, padx=5)
    
    def create_status_bar(self):
        """Create a status bar at the bottom of the application"""
        status_frame = ttk.Frame(self.main_container, relief=tk.SUNKEN, padding="2 2 2 2")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Asset counter
        self.asset_count_var = tk.StringVar(value="Assets: 0")
        asset_count_label = ttk.Label(status_frame, textvariable=self.asset_count_var)
        asset_count_label.pack(side=tk.RIGHT, padx=5)
        
        # Update the asset count
        self.update_asset_count()
    
    def update_asset_count(self):
        """Update the asset counter in the status bar"""
        assets = self.db.get_all_assets()
        self.asset_count_var.set(f"Assets: {len(assets)}")
        
    def update_status(self, message):
        """Update the status message"""
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def create_asset_manager_tab(self):
        """Create the asset manager tab for managing sprite assets"""
        # Create tab
        self.asset_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.asset_frame, text="Asset Manager")
        
        # Split into left panel (asset list) and right panel (asset details)
        pane = ttk.PanedWindow(self.asset_frame, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - asset list and filtering
        left_panel = ttk.Frame(pane)
        pane.add(left_panel, weight=1)
        
        # Filter controls
        filter_frame = ttk.Frame(left_panel)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT, padx=5)
        
        self.category_filter = tk.StringVar(value="All")
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_filter,
                                  values=["All"] + ASSET_CATEGORIES)
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.bind("<<ComboboxSelected>>", self.filter_assets)
        
        # Search box
        search_frame = ttk.Frame(left_panel)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.asset_search_var = tk.StringVar()
        self.asset_search_var.trace_add("write", self.filter_assets)
        ttk.Entry(search_frame, textvariable=self.asset_search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Asset listbox with scrollbar
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.asset_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.asset_listbox.yview)
        self.asset_listbox.configure(yscrollcommand=scrollbar.set)
        self.asset_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.asset_listbox.bind('<<ListboxSelect>>', self.on_asset_select)
        
        # Buttons for asset management
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="New Asset", command=self.start_new_asset_wizard).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Asset", command=self.delete_selected_asset).pack(side=tk.LEFT, padx=5)
        
        # Right panel - asset details
        right_panel = ttk.Frame(pane)
        pane.add(right_panel, weight=2)
        
        # Asset details notebook
        self.asset_notebook = ttk.Notebook(right_panel)
        self.asset_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Overview tab
        self.asset_overview_frame = ttk.Frame(self.asset_notebook, padding=10)
        self.asset_notebook.add(self.asset_overview_frame, text="Overview")
        
        # Preview frame
        preview_frame = ttk.LabelFrame(self.asset_overview_frame, text="Asset Preview")
        preview_frame.pack(fill=tk.X, pady=10)
        
        self.asset_preview_label = ttk.Label(preview_frame)
        self.asset_preview_label.pack(padx=20, pady=20)
        
        # Details grid
        details_frame = ttk.LabelFrame(self.asset_overview_frame, text="Asset Details")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Two-column layout for details
        details_grid = ttk.Frame(details_frame, padding=10)
        details_grid.pack(fill=tk.BOTH, expand=True)
        
        # Row 1: Name
        ttk.Label(details_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.asset_name_var = tk.StringVar()
        name_entry = ttk.Entry(details_grid, textvariable=self.asset_name_var, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=3)
        
        # Row 2: Category
        ttk.Label(details_grid, text="Category:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.asset_category_var = tk.StringVar()
        category_combo = ttk.Combobox(details_grid, textvariable=self.asset_category_var, values=ASSET_CATEGORIES)
        category_combo.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=3)
        
        # Row 3: Tags
        ttk.Label(details_grid, text="Tags:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.asset_tags_var = tk.StringVar()
        tags_entry = ttk.Entry(details_grid, textvariable=self.asset_tags_var)
        tags_entry.grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=3)
        
        # Row 4: Description
        ttk.Label(details_grid, text="Description:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.asset_desc_text = tk.Text(details_grid, height=5, width=30)
        self.asset_desc_text.grid(row=3, column=1, sticky=tk.W+tk.E, padx=5, pady=3)
        
        # Row 5: CHR Bank
        ttk.Label(details_grid, text="CHR Bank:").grid(row=4, column=0, sticky=tk.W, pady=3)
        self.asset_bank_var = tk.IntVar(value=0)
        bank_spinbox = ttk.Spinbox(details_grid, from_=0, to=31, textvariable=self.asset_bank_var, width=5)
        bank_spinbox.grid(row=4, column=1, sticky=tk.W, padx=5, pady=3)
        
        # Buttons for saving changes
        btn_frame2 = ttk.Frame(details_grid)
        btn_frame2.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame2, text="Save Changes", command=self.save_asset_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Edit Sprites", command=self.edit_asset_sprites).pack(side=tk.LEFT, padx=5)
        
        # Sprites tab
        self.asset_sprites_frame = ttk.Frame(self.asset_notebook, padding=10)
        self.asset_notebook.add(self.asset_sprites_frame, text="Sprites")
        
        # Animations tab
        self.asset_animations_frame = ttk.Frame(self.asset_notebook, padding=10)
        self.asset_notebook.add(self.asset_animations_frame, text="Animations")
        
        # Export tab
        self.asset_export_frame = ttk.Frame(self.asset_notebook, padding=10)
        self.asset_notebook.add(self.asset_export_frame, text="Export")
        
        # Populate the asset list
        self.refresh_asset_list()
        
    def create_sprite_editor_tab(self):
        """Create the sprite editor tab"""
        # Create tab
        self.sprite_editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sprite_editor_frame, text="Sprite Editor")
        
        # We'll implement this tab's content later
        ttk.Label(self.sprite_editor_frame, text="Sprite Editor Tab - Coming Soon").pack(pady=50)
    
    def create_animation_editor_tab(self):
        """Create the animation editor tab"""
        # Create tab
        self.animation_editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.animation_editor_frame, text="Animation Editor")
        
        # We'll implement this tab's content later
        ttk.Label(self.animation_editor_frame, text="Animation Editor Tab - Coming Soon").pack(pady=50)
    
    def create_export_tab(self):
        """Create the export tab"""
        # Create tab
        self.export_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.export_frame, text="Export")
        
        # We'll implement this tab's content later
        ttk.Label(self.export_frame, text="Export Tab - Coming Soon").pack(pady=50)
    
    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Asset", command=self.start_new_asset_wizard)
        file_menu.add_command(label="Open ROM...", command=self.load_rom)
        file_menu.add_command(label="Import Assets...", command=self.import_assets)
        file_menu.add_separator()
        file_menu.add_command(label="Export All Assets", command=self.export_all_assets)
        file_menu.add_command(label="Export Selected Asset", command=self.export_selected_asset)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Preferences", command=self.show_preferences)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Extract Sprites from ROM", command=self.extract_sprites_from_rom)
        tools_menu.add_command(label="Bulk Tag Similar Sprites", command=self.bulk_tag_similar)
        tools_menu.add_command(label="Auto-Detect Animations", command=self.detect_all_animations)
        tools_menu.add_command(label="Generate Assembly Code", command=self.generate_assembly)
        tools_menu.add_separator()
        tools_menu.add_command(label="Database Management", command=self.show_database_management)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Preferences", command=self.show_preferences)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Extract Sprites from ROM", command=self.extract_sprites_from_rom)
        tools_menu.add_command(label="Bulk Tag Similar Sprites", command=self.bulk_tag_similar)
        tools_menu.add_command(label="Auto-Detect Animations", command=self.detect_all_animations)
        tools_menu.add_command(label="Generate Assembly Code", command=self.generate_assembly)
        tools_menu.add_separator()
        tools_menu.add_command(label="Database Management", command=self.show_database_management)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_dashboard_tab(self):
        """Create the dashboard tab with overview information"""
        # Create tab
        self.dashboard_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        
        # Welcome header
        header_frame = ttk.Frame(self.dashboard_frame)
        header_frame.pack(fill=tk.X, pady=10)
        
        welcome_label = ttk.Label(header_frame, 
                             text="Welcome to Arkista Sprite Toolkit: Enhanced Edition",
                             font=self.title_font)
        welcome_label.pack()
        
        description = "A comprehensive toolkit for managing NES sprite assets for your game projects."
        desc_label = ttk.Label(header_frame, text=description)
        desc_label.pack(pady=5)
        
        # Main dashboard content in three columns
        content_frame = ttk.Frame(self.dashboard_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left column - Recent assets
        left_frame = ttk.LabelFrame(content_frame, text="Recent Assets", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.recent_listbox = tk.Listbox(left_frame, height=10)
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.recent_listbox.yview)
        self.recent_listbox.configure(yscrollcommand=scrollbar.set)
        self.recent_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recent_listbox.bind("<<ListboxSelect>>", self.select_recent_asset)
        
        # Middle column - Quick actions
        middle_frame = ttk.LabelFrame(content_frame, text="Quick Actions", padding=10)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        action_buttons = [
            ("Create New Asset", self.start_new_asset_wizard),
            ("Import Sprites", self.import_assets),
            ("Extract From ROM", self.extract_sprites_from_rom),
            ("Create Animation", self.create_new_animation),
            ("Export Assets", self.export_all_assets)
        ]
        
        for text, command in action_buttons:
            btn = ttk.Button(middle_frame, text=text, command=command)
            btn.pack(fill=tk.X, pady=5)
        
        # Right column - Statistics
        right_frame = ttk.LabelFrame(content_frame, text="Statistics", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Stats grid
        stats_frame = ttk.Frame(right_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        self.stats_labels = {}
        stats = [
            ("Total Assets", "0"),
            ("Player Sprites", "0"),
            ("Enemy Sprites", "0"),
            ("Items", "0"),
            ("Animations", "0")
        ]
        
        for i, (label, value) in enumerate(stats):
            ttk.Label(stats_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=3)
            value_var = tk.StringVar(value=value)
            value_label = ttk.Label(stats_frame, textvariable=value_var)
            value_label.grid(row=i, column=1, sticky=tk.W, padx=10, pady=3)
            self.stats_labels[label] = value_var
        
        # Progress bar for disk usage
        ttk.Label(stats_frame, text="Disk Usage:").grid(row=len(stats), column=0, sticky=tk.W, pady=3)
        self.disk_progress = ttk.Progressbar(stats_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.disk_progress.grid(row=len(stats), column=1, sticky=tk.W+tk.E, padx=10, pady=3)
        
        # Update dashboard data
        self.update_dashboard()
    
    def update_dashboard(self):
        """Update the dashboard with current data"""
        # Update recent assets listbox
        self.recent_listbox.delete(0, tk.END)
        
        # Get all assets ordered by updated_at
        assets = self.db.get_all_assets()
        # Sort by updated_at if available
        try:
            assets.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        except:
            pass
        
        # Take just the first 10
        recent_assets = assets[:10]
        for asset in recent_assets:
            self.recent_listbox.insert(tk.END, f"{asset['name']} ({asset['category']})")
        
        # Update statistics
        self.stats_labels["Total Assets"].set(str(len(assets)))
        
        # Count by category
        player_count = len([a for a in assets if a['category'] == 'Player'])
        enemy_count = len([a for a in assets if a['category'] == 'Enemy'])
        item_count = len([a for a in assets if a['category'] == 'Item'])
        
        self.stats_labels["Player Sprites"].set(str(player_count))
        self.stats_labels["Enemy Sprites"].set(str(enemy_count))
        self.stats_labels["Items"].set(str(item_count))
        
        # Count animations
        animation_count = 0
        for asset in assets:
            animations = self.db.get_animations_for_asset(asset['id'])
            animation_count += len(animations)
        
        self.stats_labels["Animations"].set(str(animation_count))
        
        # Update disk usage
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.assets_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            
            # Set progress to percentage of 1GB
            disk_pct = min(100, (total_size / (1024 * 1024 * 1024)) * 100)
            self.disk_progress['value'] = disk_pct
        except Exception as e:
            print(f"Error calculating disk usage: {e}")
        
        # Update status bar
        self.update_asset_count()
    
    def select_recent_asset(self, event):
        """Handle selecting an asset from the recent list"""
        if not self.recent_listbox.curselection():
            return
        
        index = self.recent_listbox.curselection()[0]
        # Get all assets ordered by updated_at
        assets = self.db.get_all_assets()
        try:
            assets.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        except:
            pass
        
        if index < len(assets):
            asset = assets[index]
            self.current_asset = asset
            # Switch to asset manager tab
            self.notebook.select(1)  # Asset Manager tab index
            self.load_asset_details(asset)
    
    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Sprite Directory", command=self.load_directory)
        file_menu.add_command(label="Export All Metadata", command=self.export_all_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Bulk Tag Similar Sprites", command=self.bulk_tag_similar)
        tools_menu.add_command(label="Auto-Detect All Animations", command=self.detect_all_animations)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_sprite_manager_tab(self):
        """Create the sprite manager tab"""
        # Create tab
        self.sprite_manager_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sprite_manager_frame, text="Sprite Manager")
        
        # Main frame with two panes
        main_panes = ttk.PanedWindow(self.sprite_manager_frame, orient=tk.HORIZONTAL)
        main_panes.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - sprite list and navigation
        left_frame = ttk.Frame(main_panes, padding=5)
        main_panes.add(left_frame, weight=1)
        
        # File controls
        file_frame = ttk.LabelFrame(left_frame, text="File Operations", padding=5)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(file_frame, text="Load Sprite Directory", command=self.load_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Export All Metadata", command=self.export_all_data).pack(side=tk.LEFT, padx=5)
        
        # Sprite list frame
        list_frame = ttk.LabelFrame(left_frame, text="Sprite List", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add search field
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_sprite_list)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Sprite listbox with scrollbar
        self.sprite_listbox = tk.Listbox(list_frame, width=30, height=30)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.sprite_listbox.yview)
        self.sprite_listbox.configure(yscrollcommand=scrollbar.set)
        self.sprite_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sprite_listbox.bind('<<ListboxSelect>>', self.select_sprite)
        
        # Right panel - sprite details and tagging
        right_frame = ttk.Frame(main_panes, padding=5)
        main_panes.add(right_frame, weight=2)
        
        # Sprite preview frame
        preview_frame = ttk.LabelFrame(right_frame, text="Sprite Preview", padding=5)
        preview_frame.pack(fill=tk.X, pady=5)
        
        # Configuration frame
        config_frame = ttk.Frame(preview_frame)
        config_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(config_frame, text="Sprite Configuration:").pack(side=tk.LEFT, padx=5)
        self.config_var = tk.StringVar(value=self.current_config)
        config_combo = ttk.Combobox(config_frame, textvariable=self.config_var, 
                                    values=["single", "double_h", "double_v", "quad"])
        config_combo.pack(side=tk.LEFT, padx=5)
        config_combo.bind("<<ComboboxSelected>>", self.change_sprite_config)
        
        ttk.Button(config_frame, text="Refresh Preview", command=self.refresh_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_frame, text="Split Tiles", command=self.split_current_sprite).pack(side=tk.LEFT, padx=5)
        
        # Sprite preview
        self.preview_frame = ttk.Frame(preview_frame)
        self.preview_frame.pack(pady=10)
        
        self.sprite_preview = ttk.Label(self.preview_frame)
        self.sprite_preview.pack()
        
        # Sprite data entry
        data_frame = ttk.LabelFrame(right_frame, text="Sprite Data", padding=5)
        data_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Two-column layout for data fields
        data_cols = ttk.Frame(data_frame)
        data_cols.pack(fill=tk.BOTH, expand=True)
        
        # Left column
        left_data = ttk.Frame(data_cols)
        left_data.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Name field
        name_frame = ttk.Frame(left_data)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(name_frame, width=30)
        self.name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Type dropdown
        type_frame = ttk.Frame(left_data)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="Type:").pack(side=tk.LEFT)
        self.type_combo = ttk.Combobox(type_frame, 
                                        values=["Player", "Enemy", "Item", "Environment", 
                                                "UI", "Text", "Weapon", "Decoration", "Unknown"])
        self.type_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Original bank field
        bank_frame = ttk.Frame(left_data)
        bank_frame.pack(fill=tk.X, pady=5)
        ttk.Label(bank_frame, text="Original Bank:").pack(side=tk.LEFT)
        self.bank_entry = ttk.Entry(bank_frame, width=10)
        self.bank_entry.pack(side=tk.LEFT, padx=5)
        
        # Right column
        right_data = ttk.Frame(data_cols)
        right_data.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Animation frames
        anim_frame = ttk.Frame(right_data)
        anim_frame.pack(fill=tk.X, pady=5)
        ttk.Label(anim_frame, text="Animation Frames:").pack(side=tk.LEFT)
        self.anim_entry = ttk.Entry(anim_frame, width=30)
        self.anim_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Sprite size
        size_frame = ttk.Frame(right_data)
        size_frame.pack(fill=tk.X, pady=5)
        ttk.Label(size_frame, text="Size (tiles):").pack(side=tk.LEFT)
        self.size_entry = ttk.Entry(size_frame, width=10)
        self.size_entry.pack(side=tk.LEFT, padx=5)
        
        # Palette
        palette_frame = ttk.Frame(right_data)
        palette_frame.pack(fill=tk.X, pady=5)
        ttk.Label(palette_frame, text="Palette:").pack(side=tk.LEFT)
        self.palette_entry = ttk.Entry(palette_frame, width=30)
        self.palette_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Notes field 
        notes_frame = ttk.LabelFrame(data_frame, text="Notes", padding=5)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.notes_text = tk.Text(notes_frame, height=5, width=40)
        notes_scroll = ttk.Scrollbar(notes_frame, orient=tk.VERTICAL, command=self.notes_text.yview)
        self.notes_text.configure(yscrollcommand=notes_scroll.set)
        self.notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        notes_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Save Sprite Data", command=self.save_sprite_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Tag Similar Sprites", command=self.tag_similar).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Auto-Detect Animations", command=self.detect_animations).pack(side=tk.LEFT, padx=5)
    
    def create_tile_splitter_tab(self):
        """Create the tile splitter tab"""
        # Create tab
        self.tile_splitter_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tile_splitter_frame, text="Tile Splitter")
        
        # Main layout with paned window
        main_pane = ttk.PanedWindow(self.tile_splitter_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left side - controls
        control_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(control_frame, weight=1)
        
        # Load buttons
        load_frame = ttk.Frame(control_frame)
        load_frame.pack(fill=tk.X, pady=5)
        ttk.Button(load_frame, text="Load Sprite File", command=self.load_sprite_for_split).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(load_frame, text="Load Selected Sprite", command=self.load_selected_sprite).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Configuration options
        config_frame = ttk.LabelFrame(control_frame, text="Configuration", padding=5)
        config_frame.pack(fill=tk.X, pady=5)
        
        # Sprite configuration
        ttk.Label(config_frame, text="Sprite Configuration:").pack(anchor=tk.W)
        self.split_config_var = tk.StringVar(value=self.current_config)
        config_options = ttk.Combobox(config_frame, textvariable=self.split_config_var,
                                      values=["single", "double_h", "double_v", "quad"])
        config_options.pack(fill=tk.X, pady=2)
        config_options.bind("<<ComboboxSelected>>", self.update_split_preview)
        
        # Palette editor
        palette_frame = ttk.LabelFrame(control_frame, text="Palette", padding=5)
        palette_frame.pack(fill=tk.X, pady=5)
        
        # Four color selectors for the palette
        self.palette_buttons = []
        self.current_palette = [0, 1, 2, 3]  # Default palette indices
        for i in range(4):
            frame = ttk.Frame(palette_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"Color {i}:").pack(side=tk.LEFT)
            color_var = tk.IntVar(value=self.current_palette[i])
            color_spin = ttk.Spinbox(frame, from_=0, to=63, width=5, textvariable=color_var)
            color_spin.pack(side=tk.LEFT, padx=5)
            
            # Color preview button
            color_button = tk.Button(frame, width=3, height=1, bg="black")
            color_button.pack(side=tk.LEFT, padx=5)
            
            self.palette_buttons.append((color_var, color_button))
            color_var.trace_add("write", lambda *args, i=i: self.update_palette_preview(i))
        
        ttk.Button(palette_frame, text="Apply Palette", command=self.apply_palette_to_preview).pack(fill=tk.X, pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Split Into Tiles", command=self.split_into_tiles).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Save Individual Tiles", command=self.save_tiles).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Export Metadata", command=self.export_tile_metadata).pack(fill=tk.X, pady=2)
        
        # Right side - preview area
        preview_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(preview_frame, weight=3)
        
        # Original sprite preview
        original_frame = ttk.LabelFrame(preview_frame, text="Original Sprite")
        original_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.original_preview = ttk.Label(original_frame)
        self.original_preview.pack(padx=10, pady=10)
        
        # Split tiles preview
        split_frame = ttk.LabelFrame(preview_frame, text="Split Tiles")
        split_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Canvas for displaying split tiles
        self.canvas_frame = ttk.Frame(split_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.split_canvas = tk.Canvas(self.canvas_frame, bg="lightgray")
        self.split_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initialize palette preview
        for i in range(4):
            self.update_palette_preview(i)
    
    # --- Shared Methods ---
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Arkista Sprite Toolkit

A unified tool for managing NES sprites from Arkista's Ring.
Combines sprite management and tile splitting functionality.

Created for Craven Caverns NES roguelike project."""
        messagebox.showinfo("About", about_text)
    
    def load_directory(self):
        """Load all sprite images from a directory"""
        directory = filedialog.askdirectory(title="Select Sprite Directory")
        if not directory:
            return
            
        self.base_directory = directory  # Store the base directory for resolving paths
        self.sprite_listbox.delete(0, tk.END)
        self.sprite_data = {}
        
        # Load all PNG files from directory
        loaded_count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.png'):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, directory)
                    self.sprite_listbox.insert(tk.END, relative_path)
                    loaded_count += 1
                    
                    # Check for metadata file
                    metadata_path = os.path.splitext(full_path)[0] + '.json'
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            self.sprite_data[relative_path] = json.load(f)
                    else:
                        # Create default metadata
                        sprite_name = os.path.splitext(os.path.basename(file))[0]
                        self.sprite_data[relative_path] = {
                            "name": sprite_name,
                            "type": "Unknown",
                            "bank": "",
                            "animation_frames": "",
                            "size": "8x8" if "single" in self.current_config else "16x16",
                            "palette": "",
                            "notes": ""
                        }
        
        messagebox.showinfo("Sprites Loaded", f"Loaded {loaded_count} sprites from {directory}")
        
        # Automatically select first sprite
        if loaded_count > 0:
            self.sprite_listbox.selection_set(0)
            self.sprite_listbox.event_generate("<<ListboxSelect>>")

    def filter_sprite_list(self, *args):
        """Filter sprite list based on search text"""
        search_text = self.search_var.get().lower()
        
        self.sprite_listbox.delete(0, tk.END)
        for sprite_path in sorted(self.sprite_data.keys()):
            if search_text in sprite_path.lower() or search_text in self.sprite_data[sprite_path].get("name", "").lower():
                self.sprite_listbox.insert(tk.END, sprite_path)
    
    def export_all_data(self):
        """Export all sprite metadata to a JSON file"""
        if not self.sprite_data:
            messagebox.showinfo("No Data", "No sprite data to export")
            return
            
        output_file = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export All Sprite Data"
        )
        
        if not output_file:
            return
        
        with open(output_file, 'w') as f:
            json.dump(self.sprite_data, f, indent=2)
        
        # Also generate a report
        report_file = os.path.splitext(output_file)[0] + "_report.txt"
        self.generate_sprite_report(report_file)
        
        messagebox.showinfo("Export Complete", f"Exported metadata to {output_file}\nand report to {report_file}")
    
    def generate_sprite_report(self, report_file):
        """Generate a detailed report of all sprites"""
        with open(report_file, 'w') as f:
            f.write("Arkista's Ring Sprite Report\n")
            f.write("==========================\n\n")
            
            # Count by type
            types = {}
            for sprite, data in self.sprite_data.items():
                sprite_type = data.get("type", "Unknown")
                types[sprite_type] = types.get(sprite_type, 0) + 1
            
            f.write("Sprite Types Summary:\n")
            for sprite_type, count in sorted(types.items()):
                f.write(f"  {sprite_type}: {count} sprites\n")
            
            f.write("\nDetailed Sprite List:\n")
            for sprite, data in sorted(self.sprite_data.items()):
                f.write(f"\n{sprite}\n")
                f.write(f"  Name: {data.get('name', '')}\n")
                f.write(f"  Type: {data.get('type', 'Unknown')}\n")
                if data.get('bank'):
                    f.write(f"  Bank: {data['bank']}\n")
                if data.get('animation_frames'):
                    f.write(f"  Animation Frames: {data['animation_frames']}\n")
                if data.get('notes'):
                    notes = data['notes'].replace('\n', '\n  ')
                    f.write(f"  Notes: {notes}\n")
    
    def bulk_tag_similar(self):
        """Bulk tag similar sprites across the entire set"""
        if not self.sprite_data:
            messagebox.showinfo("No Data", "No sprite data to process")
            return
            
        # This is a simplified implementation
        # A real implementation would use image similarity algorithms
        messagebox.showinfo("Bulk Tagging", "Bulk tagging not yet implemented")
    
    def detect_all_animations(self):
        """Auto-detect animation sequences across the entire set"""
        if not self.sprite_data:
            messagebox.showinfo("No Data", "No sprite data to process")
            return
            
        # This is a simplified implementation
        # A real implementation would detect sequences based on filename patterns
        messagebox.showinfo("Animation Detection", "Animation detection not yet implemented")
    
    # --- Sprite Manager Tab Methods ---
    
    def change_sprite_config(self, event=None):
        """Change the sprite configuration (single, double, quad)"""
        self.current_config = self.config_var.get()
        if self.current_sprite:
            self.refresh_preview()
    
    def refresh_preview(self):
        """Refresh the sprite preview with current configuration"""
        if not self.current_sprite:
            return
            
        self.update_sprite_preview()
    
    def update_sprite_preview(self):
        """Update the sprite preview based on current configuration"""
        if not self.current_sprite or not hasattr(self, 'base_directory'):
            return
            
        # Use the stored base directory for resolving paths
        image_path = os.path.join(self.base_directory, self.current_sprite)
        
        try:
            # Load the image
            image = Image.open(image_path)
            
            # Get configuration dimensions
            width, height = self.sprite_configs[self.current_config]
            
            # Scale based on configuration (each NES tile is 8x8)
            scale = 6  # Scale factor for display
            new_width = width * 8 * scale
            new_height = height * 8 * scale
            
            # Resize with nearest neighbor for pixel art
            image = image.resize((new_width, new_height), Image.NEAREST)
            photo = ImageTk.PhotoImage(image)
            
            self.sprite_preview.configure(image=photo)
            self.sprite_preview.image = photo  # Keep reference
            
            # Update size in the form
            size_text = f"{width*8}x{height*8}"
            self.size_entry.delete(0, tk.END)
            self.size_entry.insert(0, size_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")
    
    def select_sprite(self, event):
        """Handle sprite selection from the list"""
        selected_indices = self.sprite_listbox.curselection()
        if not selected_indices:
            return
            
        self.current_sprite = self.sprite_listbox.get(selected_indices[0])
        data = self.sprite_data[self.current_sprite]
        
        # Update preview
        self.update_sprite_preview()
        
        # Populate form fields
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, data.get("name", ""))
        
        self.type_combo.set(data.get("type", "Unknown"))
        
        self.bank_entry.delete(0, tk.END)
        self.bank_entry.insert(0, data.get("bank", ""))
        
        self.anim_entry.delete(0, tk.END)
        self.anim_entry.insert(0, data.get("animation_frames", ""))
        
        self.size_entry.delete(0, tk.END)
        self.size_entry.insert(0, data.get("size", ""))
        
        self.palette_entry.delete(0, tk.END)
        self.palette_entry.insert(0, data.get("palette", ""))
        
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", data.get("notes", ""))
    
    def save_sprite_data(self):
        """Save metadata for the current sprite"""
        if not self.current_sprite:
            return
            
        self.sprite_data[self.current_sprite] = {
            "name": self.name_entry.get(),
            "type": self.type_combo.get(),
            "bank": self.bank_entry.get(),
            "animation_frames": self.anim_entry.get(),
            "size": self.size_entry.get(),
            "palette": self.palette_entry.get(),
            "notes": self.notes_text.get("1.0", tk.END).strip()
        }
        
        # Save to JSON file
        if hasattr(self, 'base_directory'):
            image_path = os.path.join(self.base_directory, self.current_sprite)
            metadata_path = os.path.splitext(image_path)[0] + '.json'
            
            with open(metadata_path, 'w') as f:
                json.dump(self.sprite_data[self.current_sprite], f, indent=2)
            
            messagebox.showinfo("Saved", f"Saved metadata for {self.current_sprite}")
    
    def tag_similar(self):
        """Apply current sprite's tags to visually similar sprites"""
        if not self.current_sprite or not self.sprite_data:
            return
            
        # This is a simplified implementation
        # A real implementation would use image similarity algorithms
        messagebox.showinfo("Tag Similar", "Tag similar feature not yet implemented")
    
    def detect_animations(self):
        """Auto-detect animation sequences in the current selection"""
        if not self.current_sprite:
            return
            
        # Simple animation detection based on filename patterns
        current_name = self.name_entry.get()
        similar_sprites = []
        
        for sprite_path in self.sprite_data.keys():
            sprite_name = self.sprite_data[sprite_path].get("name", "")
            if current_name and sprite_name.startswith(current_name) and sprite_path != self.current_sprite:
                similar_sprites.append(sprite_path)
        
        if similar_sprites:
            animation_text = ", ".join(similar_sprites)
            self.anim_entry.delete(0, tk.END)
            self.anim_entry.insert(0, animation_text)
            messagebox.showinfo("Animations", f"Found {len(similar_sprites)} potential animation frames")
        else:
            messagebox.showinfo("Animations", "No animation frames detected")
    
    def split_current_sprite(self):
        """Split the current sprite into tiles (connects to tile splitter tab)"""
        if not self.current_sprite or not hasattr(self, 'base_directory'):
            messagebox.showinfo("No Sprite", "Please select a sprite first")
            return
        
        # Load the current sprite into the tile splitter tab
        image_path = os.path.join(self.base_directory, self.current_sprite)
        self.load_sprite_for_split(image_path)
        
        # Switch to the tile splitter tab
        self.notebook.select(self.tile_splitter_frame)
    
    # --- Tile Splitter Tab Methods ---
    
    def load_selected_sprite(self):
        """Load the sprite currently selected in the sprite manager tab"""
        if not hasattr(self, 'current_sprite') or self.current_sprite is None or not hasattr(self, 'base_directory'):
            messagebox.showinfo("No Selection", "Please select a sprite in the Sprite Manager tab first")
            return
            
        # Load the current sprite into the tile splitter
        image_path = os.path.join(self.base_directory, self.current_sprite)
        self.load_sprite_for_split(image_path)
    
    def update_palette_preview(self, index):
        """Update the palette preview button color"""
        if not hasattr(self, 'palette_buttons') or index >= len(self.palette_buttons):
            return
            
        color_var, button = self.palette_buttons[index]
        color_index = color_var.get()
        if 0 <= color_index < len(NES_PALETTE):
            rgb = NES_PALETTE[color_index]
            hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            button.config(bg=hex_color)
            
        # Auto-update the preview with new palette colors
        if hasattr(self, 'current_split_image') and self.current_split_image is not None:
            self.apply_palette_to_preview()
    
    def load_sprite_for_split(self, filepath=None):
        """Load a sprite image to split"""
        if not filepath:
            filepath = filedialog.askopenfilename(
                title="Select Sprite Image",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
            )
        
        if not filepath:
            return
        
        try:
            self.current_split_image = Image.open(filepath)
            self.current_split_filepath = filepath
            self.update_split_preview()
            self.split_tiles = []  # Clear any existing split tiles
            messagebox.showinfo("Image Loaded", f"Loaded image: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")
    
    def apply_palette_to_preview(self):
        """Apply the current palette to the sprite preview"""
        if not hasattr(self, 'current_split_image') or self.current_split_image is None:
            return
            
        # Get current palette colors
        palette_colors = [NES_PALETTE[var.get()] for var, _ in self.palette_buttons]
        
        # Apply palette and update preview
        self.update_split_preview(apply_palette=True)
        
        # Also update the sprite data if we're working with a sprite from the manager
        if hasattr(self, 'current_sprite') and self.current_sprite in self.sprite_data:
            palette_indexes = [var.get() for var, _ in self.palette_buttons]
            palette_str = ",".join(map(str, palette_indexes))
            
            # Update palette field in sprite manager
            if hasattr(self, 'palette_entry'):
                self.palette_entry.delete(0, tk.END)
                self.palette_entry.insert(0, palette_str)
            
            # Update sprite data
            self.sprite_data[self.current_sprite]["palette"] = palette_str
    
    def update_split_preview(self, event=None, apply_palette=False):
        """Update the original sprite preview with current settings"""
        if not hasattr(self, 'current_split_image') or self.current_split_image is None:
            return
        
        # Create a copy of the image to work with
        img = self.current_split_image.copy()
        
        # Apply current palette if requested
        if apply_palette:
            # Get palette colors
            palette_colors = [NES_PALETTE[var.get()] for var, _ in self.palette_buttons]
            
            # Create a new image with the same size
            width, height = img.size
            data = list(img.getdata())
            new_data = []
            
            # Improved palette mapping - handle both indexed and non-indexed images
            for pixel in data:
                # Handle both RGB and RGBA images
                if len(pixel) == 4:  # RGBA
                    r, g, b, a = pixel
                    if a == 0:  # Transparent
                        new_data.append((0, 0, 0, 0))
                        continue
                else:  # RGB
                    r, g, b = pixel
                    a = 255
                
                # Calculate grayscale value to determine palette index
                # Use luminance formula for better color mapping
                luminance = int(0.299 * r + 0.587 * g + 0.114 * b)
                
                # Map luminance to palette index
                if luminance < 64:  # Very dark
                    new_data.append(palette_colors[0] + (a,))
                elif luminance < 128:  # Dark/medium
                    new_data.append(palette_colors[1] + (a,))
                elif luminance < 192:  # Medium/light
                    new_data.append(palette_colors[2] + (a,))
                else:  # Very light/white
                    new_data.append(palette_colors[3] + (a,))
            
            # Create a new image with the palette applied
            new_img = Image.new("RGBA", (width, height))
            new_img.putdata(new_data)
            img = new_img
        
        # Display with zoom factor
        zoom = 6  # 6x zoom for better visibility
        preview_img = img.resize(
            (img.width * zoom, img.height * zoom),
            Image.NEAREST
        )
        
        photo = ImageTk.PhotoImage(preview_img)
        self.original_preview.configure(image=photo)
        self.original_preview.image = photo
    
    def split_into_tiles(self):
        """Split the loaded sprite into individual 8x8 tiles"""
        if not hasattr(self, 'current_split_image') or self.current_split_image is None:
            messagebox.showinfo("No Image", "Please load a sprite image first")
            return
        
        # Determine the tile configuration
        config = self.split_config_var.get()
        if config == "single":
            width, height = 1, 1
        elif config == "double_h":
            width, height = 2, 1
        elif config == "double_v":
            width, height = 1, 2
        else:  # quad
            width, height = 2, 2
        
        # Split the image into 8x8 tiles
        self.split_tiles = []
        for y in range(height):
            for x in range(width):
                box = (x * self.tile_size, y * self.tile_size, 
                      (x + 1) * self.tile_size, (y + 1) * self.tile_size)
                tile = self.current_split_image.crop(box)
                pos_name = ""
                if config == "quad":
                    if x == 0 and y == 0:
                        pos_name = "top_left"
                    elif x == 1 and y == 0:
                        pos_name = "top_right"
                    elif x == 0 and y == 1:
                        pos_name = "bottom_left"
                    else:
                        pos_name = "bottom_right"
                elif config == "double_h":
                    pos_name = "left" if x == 0 else "right"
                elif config == "double_v":
                    pos_name = "top" if y == 0 else "bottom"
                
                self.split_tiles.append({
                    "tile": tile,
                    "position": (x, y),
                    "position_name": pos_name,
                    "index": y * width + x
                })
        
        # Display the split tiles
        self.display_split_tiles()
    
    def display_split_tiles(self):
        """Display the split tiles in the canvas"""
        if not self.split_tiles:
            return
        
        # Clear canvas
        self.split_canvas.delete("all")
        
        # Calculate display size
        zoom = 8  # 8x zoom for better visibility of small tiles
        display_size = self.tile_size * zoom
        spacing = 10
        
        # Draw each tile
        for i, tile_info in enumerate(self.split_tiles):
            tile = tile_info["tile"]
            x = i * (display_size + spacing) + spacing
            y = spacing
            
            # Convert to PhotoImage and display
            large_tile = tile.resize((display_size, display_size), Image.NEAREST)
            photo = ImageTk.PhotoImage(large_tile)
            self.split_canvas.create_image(x, y, anchor=tk.NW, image=photo)
            self.split_canvas.image_refs = getattr(self.split_canvas, "image_refs", []) + [photo]
            
            # Add position label
            pos_name = tile_info["position_name"]
            self.split_canvas.create_text(
                x + display_size // 2, 
                y + display_size + 15,
                text=f"{pos_name} ({tile_info['index']})",
                fill="black"
            )
    
    def save_tiles(self):
        """Save individual tiles as separate files"""
        if not self.split_tiles:
            messagebox.showinfo("No Tiles", "Please split the sprite into tiles first")
            return
        
        # Get directory to save tiles
        save_dir = filedialog.askdirectory(title="Select Directory to Save Tiles")
        if not save_dir:
            return
        
        # Get base filename
        base_name = os.path.splitext(os.path.basename(self.current_split_filepath))[0]
        config = self.split_config_var.get()
        
        # Save each tile
        for tile_info in self.split_tiles:
            pos_name = tile_info["position_name"]
            filename = f"{base_name}_{pos_name}.png"
            filepath = os.path.join(save_dir, filename)
            
            tile_info["tile"].save(filepath)
            tile_info["filename"] = filename
            tile_info["filepath"] = filepath
        
        messagebox.showinfo("Tiles Saved", f"Saved {len(self.split_tiles)} tiles to {save_dir}")
    
    def export_tile_metadata(self):
        """Export metadata for the split tiles"""
        if not self.split_tiles:
            messagebox.showinfo("No Tiles", "Please split the sprite into tiles first")
            return
        
        # Create metadata
        metadata = {
            "original_sprite": os.path.basename(self.current_split_filepath),
            "configuration": self.split_config_var.get(),
            "palette": [var.get() for var, _ in self.palette_buttons],
            "tiles": []
        }
        
        for tile_info in self.split_tiles:
            tile_meta = {
                "index": tile_info["index"],
                "position": list(tile_info["position"]),
                "position_name": tile_info["position_name"],
            }
            
            # Add filename if tiles were saved
            if "filename" in tile_info:
                tile_meta["filename"] = tile_info["filename"]
            
            metadata["tiles"].append(tile_meta)
        
        # Save metadata
        filepath = filedialog.asksaveasfilename(
            title="Save Metadata",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        with open(filepath, "w") as f:
            json.dump(metadata, f, indent=2)
        
        messagebox.showinfo("Metadata Saved", f"Saved metadata to {filepath}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ArkistaSpriteToolkit(root)
    root.mainloop()
