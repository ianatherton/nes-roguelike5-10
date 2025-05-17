#!/usr/bin/env python3
"""
NES Asset Wizard - UI Module
----------------------------
Provides the user interface for the asset wizard system.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
import json
import uuid
import datetime
import shutil

# Import sprite sheet editor
try:
    from sprite_sheet_editor import SpriteSheetEditor
except ImportError:
    # Handle the case where the module might not be available
    print("Warning: Could not import SpriteSheetEditor module")
    SpriteSheetEditor = None

# Import core functionality
from asset_wizard_core import (
    ASSET_TYPES,
    ANIMATION_TYPES,
    DIRECTION_TYPES,
    create_default_metadata,
    get_asset_list,
    load_asset_metadata,
    get_asset_dir,
    save_asset,
    export_asset_for_game,
    create_animation_definition,
    create_sprite_definition,
    ensure_asset_directory,
    save_asset_metadata,
    get_asset_list,
    generate_sprite_filename
)

class AssetWizardApp:
    """Main asset wizard application window"""
    
    def __init__(self, root, base_dir=None):
        self.root = root
        self.root.title("NES Asset Wizard")
        self.root.geometry("900x700")
        
        # Set base directory for assets
        if base_dir:
            self.base_dir = base_dir
        else:
            # Default to a directory in user's home
            self.base_dir = os.path.join(os.path.expanduser("~"), ".nes_asset_wizard")
        
        # Ensure directories exist
        ensure_asset_directory(self.base_dir)
        
        # Current asset being edited
        self.current_asset = None
        
        # Setup the UI
        self.setup_ui()
        
        # Load asset list
        self.load_asset_list()
    
    def setup_ui(self):
        """Setup the main UI components"""
        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the various tabs
        self.create_dashboard_tab()
        self.create_wizard_tab()
        self.create_editor_tab()
        self.create_export_tab()
        
        # Start on the Asset Wizard tab by default
        self.notebook.select(1)  # Index 1 is the Asset Wizard tab
        
        # Create status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_dashboard_tab(self):
        """Create the dashboard tab with asset overview"""
        dashboard_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Header
        header_frame = ttk.Frame(dashboard_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="NES Asset Wizard", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text="New Asset", 
                  command=self.new_asset_wizard).pack(side=tk.RIGHT)
        
        # Main content - split view
        content_frame = ttk.Frame(dashboard_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - asset list
        left_panel = ttk.LabelFrame(content_frame, text="Asset Library")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Search and filter
        filter_frame = ttk.Frame(left_panel)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                  values=["All"] + list(ASSET_TYPES.keys()))
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.filter_assets)
        
        # Asset listbox with scrollbar
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.asset_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.asset_listbox.yview)
        self.asset_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.asset_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.asset_listbox.bind("<<ListboxSelect>>", self.on_asset_select)
        
        # Button frame
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Edit", command=self.edit_selected_asset).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Duplicate", command=self.duplicate_selected_asset).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_selected_asset).pack(side=tk.LEFT, padx=2)
        
        # Right panel - asset details
        right_panel = ttk.LabelFrame(content_frame, text="Asset Details")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Asset preview frame
        preview_frame = ttk.Frame(right_panel)
        preview_frame.pack(fill=tk.X, pady=10)
        
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(pady=10)
        
        # Asset details
        details_frame = ttk.Frame(right_panel)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Use a grid layout for details
        ttk.Label(details_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        ttk.Label(details_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.type_var = tk.StringVar()
        ttk.Label(details_frame, textvariable=self.type_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.desc_var = tk.StringVar()
        ttk.Label(details_frame, textvariable=self.desc_var).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_frame, text="Created:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.created_var = tk.StringVar()
        ttk.Label(details_frame, textvariable=self.created_var).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_frame, text="Modified:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.modified_var = tk.StringVar()
        ttk.Label(details_frame, textvariable=self.modified_var).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_frame, text="Sprites:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.sprites_var = tk.StringVar()
        ttk.Label(details_frame, textvariable=self.sprites_var).grid(row=5, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(details_frame, text="Animations:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.animations_var = tk.StringVar()
        ttk.Label(details_frame, textvariable=self.animations_var).grid(row=6, column=1, sticky=tk.W, pady=2)
        
        # Action buttons
        action_frame = ttk.Frame(right_panel)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Edit Asset", 
                  command=self.edit_selected_asset).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Export Asset", 
                  command=self.export_selected_asset).pack(side=tk.LEFT, padx=5)
    
    def create_wizard_tab(self):
        """Create the New Asset Wizard tab"""
        wizard_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(wizard_frame, text="New Asset Wizard")
        
        # Wizard header
        ttk.Label(wizard_frame, text="Create New Asset", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Wizard form frame
        form_frame = ttk.LabelFrame(wizard_frame, text="Asset Information")
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Asset type selection
        type_frame = ttk.Frame(form_frame, padding=10)
        type_frame.pack(fill=tk.X)
        
        ttk.Label(type_frame, text="Asset Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.wizard_type_var = tk.StringVar(value="PLAYER")
        type_combo = ttk.Combobox(type_frame, textvariable=self.wizard_type_var,
                                values=list(ASSET_TYPES.keys()))
        type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        type_combo.bind("<<ComboboxSelected>>", self.on_wizard_type_change)
        
        # Asset description label
        self.type_desc_var = tk.StringVar(value=ASSET_TYPES["Player"])
        ttk.Label(type_frame, textvariable=self.type_desc_var).grid(row=0, column=2, padx=5, pady=5)
        
        # Asset name
        ttk.Label(type_frame, text="Asset Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.wizard_name_var = tk.StringVar(value="New Player")
        ttk.Entry(type_frame, textvariable=self.wizard_name_var, width=30).grid(
            row=1, column=1, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Asset description
        ttk.Label(type_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.wizard_desc_var = tk.StringVar(value="A new player character")
        ttk.Entry(type_frame, textvariable=self.wizard_desc_var, width=30).grid(
            row=2, column=1, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Size selection
        ttk.Label(type_frame, text="Size:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        size_frame = ttk.Frame(type_frame)
        size_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        self.wizard_width_var = tk.IntVar(value=16)
        self.wizard_height_var = tk.IntVar(value=16)
        
        ttk.Spinbox(size_frame, from_=8, to=64, increment=8, width=5,
                   textvariable=self.wizard_width_var).pack(side=tk.LEFT)
        ttk.Label(size_frame, text="x").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(size_frame, from_=8, to=64, increment=8, width=5,
                   textvariable=self.wizard_height_var).pack(side=tk.LEFT)
        ttk.Label(size_frame, text="pixels").pack(side=tk.LEFT, padx=5)
        
        # Animation setup
        anim_frame = ttk.LabelFrame(form_frame, text="Animation Setup")
        anim_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        # Animation types to include
        ttk.Label(anim_frame, text="Include Animation Types:").pack(anchor=tk.W, pady=5)
        
        self.wizard_anim_vars = {}
        anim_check_frame = ttk.Frame(anim_frame)
        anim_check_frame.pack(fill=tk.X, pady=5)
        
        # Create checkbuttons for animations in a grid layout
        for i, anim in enumerate(ANIMATION_TYPES):
            var = tk.BooleanVar(value=True)
            self.wizard_anim_vars[anim] = var
            
            row, col = divmod(i, 3)
            ttk.Checkbutton(anim_check_frame, text=anim.capitalize(), 
                           variable=var).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
        
        # Direction setup
        dir_frame = ttk.LabelFrame(form_frame, text="Direction Setup")
        dir_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        ttk.Label(dir_frame, text="Include Directions:").pack(anchor=tk.W, pady=5)
        
        self.wizard_dir_vars = {}
        dir_check_frame = ttk.Frame(dir_frame)
        dir_check_frame.pack(fill=tk.X, pady=5)
        
        # Create checkbuttons for directions
        for i, direction in enumerate(DIRECTION_TYPES):
            if not direction:  # Skip empty direction
                continue
                
            var = tk.BooleanVar(value=True)
            self.wizard_dir_vars[direction] = var
            
            ttk.Checkbutton(dir_check_frame, text=direction.capitalize(), 
                           variable=var).pack(side=tk.LEFT, padx=10)
        
        # Action buttons
        btn_frame = ttk.Frame(wizard_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=lambda: self.notebook.select(0)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Create Asset", command=self.create_new_asset).pack(side=tk.RIGHT, padx=5)
    
    def create_editor_tab(self):
        """Create the Asset Editor tab with sprite sheet integration"""
        editor_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(editor_frame, text="Asset Editor")
        
        # Header
        ttk.Label(editor_frame, text="Asset Sprite Editor",
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Asset selection panel
        selection_frame = ttk.LabelFrame(editor_frame, text="Asset Selection")
        selection_frame.pack(fill=tk.X, pady=5)
        
        # Asset selector
        select_frame = ttk.Frame(selection_frame, padding=5)
        select_frame.pack(fill=tk.X)
        
        ttk.Label(select_frame, text="Select Asset:").pack(side=tk.LEFT, padx=5)
        
        self.editor_asset_var = tk.StringVar()
        self.editor_asset_combo = ttk.Combobox(select_frame, textvariable=self.editor_asset_var, width=40)
        self.editor_asset_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.editor_asset_combo.bind("<<ComboboxSelected>>", self.on_editor_asset_selected)
        
        ttk.Button(select_frame, text="Load", command=self.load_editor_asset).pack(side=tk.LEFT, padx=5)
        
        # Asset type filter
        filter_frame = ttk.Frame(selection_frame, padding=5)
        filter_frame.pack(fill=tk.X)
        
        ttk.Label(filter_frame, text="Type Filter:").pack(side=tk.LEFT, padx=5)
        
        self.editor_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.editor_filter_var,
                                 values=["All"] + list(ASSET_TYPES.keys()))
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.update_editor_asset_list)
        
        # Split view for sprites and animations
        content_paned = ttk.PanedWindow(editor_frame, orient=tk.HORIZONTAL)
        content_paned.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left side - Sprites
        sprites_frame = ttk.LabelFrame(content_paned, text="Sprites")
        content_paned.add(sprites_frame, weight=1)
        
        # Sprite list
        sprite_list_frame = ttk.Frame(sprites_frame, padding=5)
        sprite_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.sprite_listbox = tk.Listbox(sprite_list_frame, height=10)
        s_scrollbar = ttk.Scrollbar(sprite_list_frame, orient=tk.VERTICAL, command=self.sprite_listbox.yview)
        self.sprite_listbox.configure(yscrollcommand=s_scrollbar.set)
        self.sprite_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        s_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sprite_listbox.bind("<<ListboxSelect>>", self.on_sprite_selected)
        
        # Initialize the current sprite index
        self.current_sprite_index = None
        
        # Sprite buttons
        sprite_btn_frame = ttk.Frame(sprites_frame, padding=5)
        sprite_btn_frame.pack(fill=tk.X)
        
        ttk.Button(sprite_btn_frame, text="Add From Sheet", 
                  command=self.add_sprite_from_sheet).pack(side=tk.LEFT, padx=2)
        ttk.Button(sprite_btn_frame, text="Add From File", 
                  command=self.add_sprite_from_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(sprite_btn_frame, text="Remove", 
                  command=self.remove_selected_sprite).pack(side=tk.LEFT, padx=2)
        
        # Right side - Preview and details
        details_frame = ttk.LabelFrame(content_paned, text="Sprite Details")
        content_paned.add(details_frame, weight=1)
        
        # Preview
        preview_frame = ttk.Frame(details_frame, padding=5)
        preview_frame.pack(fill=tk.X)
        
        self.sprite_preview = ttk.Label(preview_frame)
        self.sprite_preview.pack(pady=10)
        
        # Sprite properties
        props_frame = ttk.Frame(details_frame, padding=5)
        props_frame.pack(fill=tk.X)
        
        # Meta fields in a grid
        ttk.Label(props_frame, text="Animation Type:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.sprite_anim_var = tk.StringVar()
        anim_combo = ttk.Combobox(props_frame, textvariable=self.sprite_anim_var, 
                                values=ANIMATION_TYPES)
        anim_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(props_frame, text="Direction:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.sprite_dir_var = tk.StringVar()
        dir_combo = ttk.Combobox(props_frame, textvariable=self.sprite_dir_var, 
                              values=DIRECTION_TYPES)
        dir_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(props_frame, text="Frame Number:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.sprite_frame_var = tk.IntVar(value=0)
        ttk.Spinbox(props_frame, from_=0, to=99, textvariable=self.sprite_frame_var, 
                  width=5).grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
        
        # Save button
        ttk.Button(props_frame, text="Apply Changes", 
                  command=self.save_sprite_changes).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Animation section
        anim_frame = ttk.LabelFrame(editor_frame, text="Animation Sequences")
        anim_frame.pack(fill=tk.X, pady=5)
        
        # Animation buttons
        anim_btn_frame = ttk.Frame(anim_frame, padding=5)
        anim_btn_frame.pack(fill=tk.X)
        
        ttk.Button(anim_btn_frame, text="Create Animation", 
                  command=self.create_animation).pack(side=tk.LEFT, padx=2)
        ttk.Button(anim_btn_frame, text="Auto-Generate Animations", 
                  command=self.auto_generate_animations).pack(side=tk.LEFT, padx=2)
        
        # Populate editor asset list initially
        self.update_editor_asset_list()
    
    def create_export_tab(self):
        """Create the Export tab with JSON export options"""
        export_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(export_frame, text="Export")
        
        # Header
        ttk.Label(export_frame, text="Export Assets for Game Integration",
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Info text
        info_text = """This tab allows you to export your assets in a format that's ready for use with your game engine.
        
Exports include:
- JSON metadata in a structured format
- Organized sprite images
- Categorized by type (player, enemy, UI, etc.)

The exported files can be imported directly into your C/assembly code."""
        
        info_label = ttk.Label(export_frame, text=info_text, justify=tk.LEFT, wraplength=600)
        info_label.pack(pady=10, anchor=tk.W)
        
        # Export options frame
        options_frame = ttk.LabelFrame(export_frame, text="Export Options")
        options_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Export selection
        selection_frame = ttk.Frame(options_frame, padding=10)
        selection_frame.pack(fill=tk.X)
        
        ttk.Label(selection_frame, text="Export:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.export_selection = tk.StringVar(value="selected")
        ttk.Radiobutton(selection_frame, text="Selected Asset", 
                       variable=self.export_selection, value="selected").grid(
            row=0, column=1, sticky=tk.W, padx=10)
        ttk.Radiobutton(selection_frame, text="All Assets", 
                       variable=self.export_selection, value="all").grid(
            row=0, column=2, sticky=tk.W, padx=10)
        
        # Export location
        location_frame = ttk.Frame(options_frame, padding=10)
        location_frame.pack(fill=tk.X)
        
        ttk.Label(location_frame, text="Export to:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.export_path = tk.StringVar(value=os.path.join(self.base_dir, "exports"))
        path_entry = ttk.Entry(location_frame, textvariable=self.export_path, width=50)
        path_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5)
        
        ttk.Button(location_frame, text="Browse...", 
                  command=self.browse_export_path).grid(row=0, column=2, padx=5)
        
        # Export format options
        format_frame = ttk.Frame(options_frame, padding=10)
        format_frame.pack(fill=tk.X)
        
        ttk.Label(format_frame, text="Options:").grid(row=0, column=0, sticky=tk.W)
        
        self.include_sprites = tk.BooleanVar(value=True)
        ttk.Checkbutton(format_frame, text="Include sprite files", 
                       variable=self.include_sprites).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        self.organize_by_type = tk.BooleanVar(value=True)
        ttk.Checkbutton(format_frame, text="Organize by type", 
                       variable=self.organize_by_type).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Export buttons
        btn_frame = ttk.Frame(export_frame)
        btn_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(btn_frame, text="Export Now", 
                  command=self.perform_export).pack(side=tk.RIGHT)
        
        # Export log
        log_frame = ttk.LabelFrame(export_frame, text="Export Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.export_log = tk.Text(log_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.export_log.yview)
        self.export_log.configure(yscrollcommand=scrollbar.set)
        
        self.export_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_asset_list(self):
        """Load the list of assets into the UI"""
        # Clear current list
        self.asset_listbox.delete(0, tk.END)
        
        # Get assets
        assets = get_asset_list(self.base_dir)
        
        # Filter if needed
        filter_type = self.filter_var.get()
        if filter_type != "All":
            assets = [a for a in assets if a.get("type") == filter_type]
        
        # Add to listbox
        for asset in assets:
            self.asset_listbox.insert(tk.END, f"{asset['name']} ({asset['type']})")
        
        # Update status
        self.status_var.set(f"Loaded {len(assets)} assets")
    
    def filter_assets(self, event=None):
        """Filter assets based on selected type"""
        self.load_asset_list()
    
    def on_asset_select(self, event=None):
        """Handle asset selection from the list"""
        # Get selected index
        if not self.asset_listbox.curselection():
            return
        
        index = self.asset_listbox.curselection()[0]
        
        # Get the asset at that index
        assets = get_asset_list(self.base_dir)
        filter_type = self.filter_var.get()
        if filter_type != "All":
            assets = [a for a in assets if a.get("type") == filter_type]
        
        if index < len(assets):
            self.display_asset_details(assets[index])
    
    def display_asset_details(self, asset):
        """Display details of the selected asset"""
        # Store current asset
        self.current_asset = asset
        
        # Update detail fields
        self.name_var.set(asset.get("name", ""))
        self.type_var.set(asset.get("type", ""))
        self.desc_var.set(asset.get("description", ""))
        
        # Format dates
        created = asset.get("created_at", "")
        modified = asset.get("updated_at", "")
        
        if created:
            # Simple formatting - just take the date part
            try:
                self.created_var.set(created.split("T")[0])
            except:
                self.created_var.set(created)
        
        if modified:
            try:
                self.modified_var.set(modified.split("T")[0])
            except:
                self.modified_var.set(modified)
        
        # Count sprites and animations
        self.sprites_var.set(str(len(asset.get("sprites", []))))
        self.animations_var.set(str(len(asset.get("animations", []))))
    
    def new_asset_wizard(self):
        """Start the new asset wizard"""
        # Switch to the wizard tab
        self.notebook.select(1)
        
        # Reset form to defaults
        self.wizard_type_var.set("PLAYER")
        self.wizard_name_var.set("New Player")
        self.wizard_desc_var.set("A new player character")
        self.wizard_width_var.set(16)
        self.wizard_height_var.set(16)
        
        # Reset animation and direction checkboxes
        self.on_wizard_type_change()
    
    def on_wizard_type_change(self, event=None):
        """Handle changing the asset type in the wizard"""
        asset_type = self.wizard_type_var.get()
        
        # Update description
        self.type_desc_var.set(ASSET_TYPES.get(asset_type, ""))
        
        # Set default size based on type
        if asset_type in ["Player", "Enemy", "Effect"]:
            # Default to 16x16 for characters and effects
            width, height = 16, 16
        else:
            # Default to 8x8 for items, UI, backgrounds, props
            width, height = 8, 8
            
        self.wizard_width_var.set(width)
        self.wizard_height_var.set(height)
        
        # Update name hint
        if self.wizard_name_var.get() == "" or self.wizard_name_var.get().startswith("New "):
            self.wizard_name_var.set(f"New {asset_type}")
    
    def create_new_asset(self):
        """Create a new asset from wizard data"""
        asset_type = self.wizard_type_var.get()
        asset_name = self.wizard_name_var.get()
        
        if not asset_name.strip():
            messagebox.showwarning("Warning", "Please enter an asset name")
            return
        
        # Create the base metadata
        asset_data = create_default_metadata(asset_type, asset_name)
        
        # Update with form data
        asset_data["description"] = self.wizard_desc_var.get()
        asset_data["size"] = (self.wizard_width_var.get(), self.wizard_height_var.get())
        
        # Create animations based on selected checkboxes
        for anim_type, var in self.wizard_anim_vars.items():
            if var.get():
                # For each selected direction
                for direction, dir_var in self.wizard_dir_vars.items():
                    if dir_var.get():
                        anim_name = f"{anim_type.capitalize()} {direction.capitalize()}"
                        anim = create_animation_definition(
                            asset_data["id"], anim_name, anim_type, direction
                        )
                        asset_data["animations"].append(anim)
        
        # Save the asset
        save_asset(self.base_dir, asset_data)
        
        # Create asset directory with placeholder files if needed
        asset_dir = ensure_asset_directory(self.base_dir, asset_data["id"])
        
        # Refresh asset list
        self.load_asset_list()
        
        # Show success message
        messagebox.showinfo("Success", f"Created new asset: {asset_name}")
        
        # Switch back to dashboard
        self.notebook.select(0)
        
        # Update status
        self.status_var.set(f"Created new asset: {asset_name}")
    
    def edit_selected_asset(self):
        """Edit the currently selected asset"""
        if not self.current_asset:
            messagebox.showinfo("Info", "No asset selected")
            return
        
        # Switch to the editor tab
        self.notebook.select(2)
        
        # TODO: Implement asset editor functionality
        messagebox.showinfo("Coming Soon", "Asset editing will be implemented in a future version")
    
    def duplicate_selected_asset(self):
        """Duplicate the currently selected asset"""
        if not self.current_asset:
            messagebox.showinfo("Info", "No asset selected")
            return
        
        # Create a copy of the asset data
        asset_copy = self.current_asset.copy()
        
        # Generate a new ID
        asset_copy["id"] = str(uuid.uuid4())
        
        # Update name
        asset_copy["name"] = f"{asset_copy['name']} (Copy)"
        
        # Update timestamps
        import datetime
        now = datetime.datetime.now().isoformat()
        asset_copy["created_at"] = now
        asset_copy["updated_at"] = now
        
        # Save the new asset
        save_asset_metadata(self.base_dir, asset_copy)
        
        # Create asset directory
        ensure_asset_directory(self.base_dir, asset_copy["id"])
        
        # TODO: Copy sprite files if any
        
        # Refresh asset list
        self.load_asset_list()
        
        # Show success message
        messagebox.showinfo("Success", f"Duplicated asset: {asset_copy['name']}")
    
    def delete_selected_asset(self):
        """Delete the currently selected asset"""
        if not self.current_asset:
            messagebox.showinfo("Info", "No asset selected")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", 
                                 f"Are you sure you want to delete the asset:\n{self.current_asset['name']}?"):
            return
        
        # Get asset directory
        asset_dir = os.path.join(self.base_dir, "assets", self.current_asset["id"])
        
        # Delete directory if it exists
        if os.path.exists(asset_dir):
            import shutil
            shutil.rmtree(asset_dir)
        
        # Refresh asset list
        self.load_asset_list()
        
        # Clear current asset
        self.current_asset = None
        
        # Clear detail fields
        self.name_var.set("")
        self.type_var.set("")
        self.desc_var.set("")
        self.created_var.set("")
        self.modified_var.set("")
        self.sprites_var.set("")
        self.animations_var.set("")
        
        # Update status
        self.status_var.set("Asset deleted")
    
    #---------------------------
    # Asset Editor Methods
    #---------------------------
    def update_editor_asset_list(self, event=None):
        """Update the asset list in the editor tab"""
        assets = get_asset_list(self.base_dir)
        
        # Apply filter if needed
        filter_type = self.editor_filter_var.get()
        if filter_type != "All":
            assets = [a for a in assets if a.get("type") == filter_type]
        
        # Clear and update the combobox
        self.editor_asset_combo["values"] = [f"{a['name']} ({a['type']})" for a in assets]
        
        # Update the asset ID mapping
        self.editor_asset_map = {f"{a['name']} ({a['type']})": a for a in assets}
    
    def on_editor_asset_selected(self, event=None):
        """Handle selection of an asset in the editor"""
        selected = self.editor_asset_var.get()
        if not selected or selected not in self.editor_asset_map:
            return
        
        # Load the asset
        self.load_editor_asset()
    
    def load_editor_asset(self):
        """Load the selected asset for editing"""
        selected = self.editor_asset_var.get()
        if not selected or selected not in self.editor_asset_map:
            messagebox.showinfo("Info", "Please select an asset to edit")
            return
        
        # Get the asset data
        self.current_editing_asset = self.editor_asset_map[selected]
        
        # Update status
        self.status_var.set(f"Editing asset: {self.current_editing_asset['name']}")
        
        # Clear the sprite listbox
        self.sprite_listbox.delete(0, tk.END)
        
        # Load sprites
        sprites = self.current_editing_asset.get("sprites", [])
        for sprite in sprites:
            sprite_name = self.get_sprite_display_name(sprite)
            self.sprite_listbox.insert(tk.END, sprite_name)
    
    def get_sprite_display_name(self, sprite):
        """Generate a display name for a sprite"""
        anim_type = sprite.get("animation_type", "idle")
        direction = sprite.get("direction", "")
        frame = sprite.get("frame", 0)
        
        # Create a descriptive name
        if direction:
            return f"{anim_type} {direction} - Frame {frame}"
        else:
            return f"{anim_type} - Frame {frame}"
    
    def on_sprite_selected(self, event=None):
        """Handle selection of a sprite in the listbox"""
        selection = self.sprite_listbox.curselection()
        if not selection:
            return
        
        # Get the selected sprite index
        index = selection[0]
        
        # Get the sprite data
        sprites = self.current_editing_asset.get("sprites", [])
        if index >= len(sprites):
            return
        
        sprite = sprites[index]
        
        # Update the sprite details
        self.sprite_anim_var.set(sprite.get("animation_type", ""))
        self.sprite_dir_var.set(sprite.get("direction", ""))
        self.sprite_frame_var.set(sprite.get("frame", 0))
        
        # Display the sprite preview
        self.display_sprite_preview(sprite)
    
    def display_sprite_preview(self, sprite):
        """Display a preview of the sprite"""
        # Get the sprite path
        sprite_path = sprite.get("file_path", "")
        if not sprite_path or not os.path.exists(sprite_path):
            # Clear preview
            self.sprite_preview.configure(image=None)
            self.sprite_preview.image = None
            return
        
        try:
            # Load the image and scale it up for better visibility
            image = Image.open(sprite_path)
            scale_factor = 3  # NES sprites are tiny, scale up for visibility
            width, height = image.size
            image = image.resize((width * scale_factor, height * scale_factor), Image.NEAREST)
            
            # Convert to Tkinter-compatible format
            photo = ImageTk.PhotoImage(image)
            
            # Update the preview label
            self.sprite_preview.configure(image=photo)
            self.sprite_preview.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error displaying sprite: {e}")
            # Clear preview
            self.sprite_preview.configure(image=None)
            self.sprite_preview.image = None
    
    def add_sprite_from_sheet(self):
        """Add sprites from a sprite sheet using the sheet editor"""
        if not self.current_editing_asset:
            messagebox.showinfo("Info", "Please select an asset first")
            return
        
        # Check if SpriteSheetEditor is available
        if SpriteSheetEditor is None:
            messagebox.showerror("Error", "Sprite Sheet Editor module not available")
            return
        
        # Callback function for when frames are selected
        def on_frames_selected(frames, metadata):
            if not frames:
                return
            
            # Get asset directory for sprites
            asset_dir = get_asset_dir(self.base_dir, self.current_editing_asset)
            sprite_dir = os.path.join(asset_dir, "sprites")
            os.makedirs(sprite_dir, exist_ok=True)
            
            # Process each frame
            for i, frame in enumerate(frames):
                # Determine frame metadata
                frame_num = len(self.current_editing_asset.get("sprites", []))
                anim_type = "idle"  # Default animation type
                direction = ""      # Default direction (none)
                
                # Save the frame image
                filename = f"sprite_{frame_num}.png"
                file_path = os.path.join(sprite_dir, filename)
                frame.save(file_path)
                
                # Create sprite data
                sprite_data = {
                    "id": str(uuid.uuid4()),
                    "file_path": file_path,
                    "animation_type": anim_type,
                    "direction": direction,
                    "frame": frame_num,
                    "source_sheet": metadata.get("source_sheet", ""),
                    "rect": frame.rect,
                    "created": datetime.datetime.now().isoformat()
                }
                
                # Add to asset
                if "sprites" not in self.current_editing_asset:
                    self.current_editing_asset["sprites"] = []
                
                self.current_editing_asset["sprites"].append(sprite_data)
                
                # Add to listbox
                sprite_name = self.get_sprite_display_name(sprite_data)
                self.sprite_listbox.insert(tk.END, sprite_name)
            
            # Save the asset
            save_asset(self.base_dir, self.current_editing_asset)
            
            # Update status
            self.status_var.set(f"Added {len(frames)} sprites from sheet")
        
        # Open the sprite sheet editor
        SpriteSheetEditor(self.root, on_frames_selected)
    
    def add_sprite_from_file(self):
        """Add a sprite from an individual image file"""
        if not self.current_editing_asset:
            messagebox.showinfo("Info", "Please select an asset first")
            return
        
        # Open file dialog
        file_paths = filedialog.askopenfilenames(
            title="Select Sprite Image(s)",
            filetypes=[(
                "Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if not file_paths:
            return
        
        # Get asset directory for sprites
        asset_dir = get_asset_dir(self.base_dir, self.current_editing_asset)
        sprite_dir = os.path.join(asset_dir, "sprites")
        os.makedirs(sprite_dir, exist_ok=True)
        
        # Get current sprite count
        start_frame = len(self.current_editing_asset.get("sprites", []))
        
        # Process each file
        for i, src_path in enumerate(file_paths):
            try:
                # Load the image
                img = Image.open(src_path)
                
                # Determine frame metadata
                frame_num = start_frame + i
                anim_type = "idle"  # Default animation type
                direction = ""      # Default direction (none)
                
                # Save the image to the sprite directory
                filename = f"sprite_{frame_num}.png"
                dst_path = os.path.join(sprite_dir, filename)
                img.save(dst_path)
                
                # Create sprite data
                sprite_data = {
                    "id": str(uuid.uuid4()),
                    "file_path": dst_path,
                    "animation_type": anim_type,
                    "direction": direction,
                    "frame": frame_num,
                    "source_file": src_path,
                    "created": datetime.datetime.now().isoformat()
                }
                
                # Add to asset
                if "sprites" not in self.current_editing_asset:
                    self.current_editing_asset["sprites"] = []
                
                self.current_editing_asset["sprites"].append(sprite_data)
                
                # Add to listbox
                sprite_name = self.get_sprite_display_name(sprite_data)
                self.sprite_listbox.insert(tk.END, sprite_name)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add sprite {os.path.basename(src_path)}: {e}")
        
        # Save the asset
        save_asset(self.base_dir, self.current_editing_asset)
        
        # Update status
        self.status_var.set(f"Added {len(file_paths)} sprites from files")
    
    def remove_selected_sprite(self):
        """Remove the selected sprite"""
        if not self.current_editing_asset:
            return
        
        selection = self.sprite_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a sprite to remove")
            return
        
        # Get the selected sprite index
        index = selection[0]
        
        # Get the sprites list
        sprites = self.current_editing_asset.get("sprites", [])
        if index >= len(sprites):
            return
        
        # Confirm removal
        sprite = sprites[index]
        sprite_name = self.get_sprite_display_name(sprite)
        if not messagebox.askyesno("Confirm", f"Remove sprite '{sprite_name}'?"):
            return
        
        # Remove the sprite file if it exists
        file_path = sprite.get("file_path", "")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not remove sprite file: {e}")
        
        # Remove from the list
        del sprites[index]
        
        # Update the asset
        self.current_editing_asset["sprites"] = sprites
        save_asset(self.base_dir, self.current_editing_asset)
        
        # Update the listbox
        self.sprite_listbox.delete(index)
        
        # Clear preview
        self.sprite_preview.configure(image=None)
        self.sprite_preview.image = None
        
        # Update status
        self.status_var.set(f"Removed sprite: {sprite_name}")
    
    def on_sprite_selected(self, event=None):
        """Handle selection of a sprite in the listbox"""
        selection = self.sprite_listbox.curselection()
        if not selection:
            return
        
        # Get the selected sprite index
        index = selection[0]
        
        # Get the sprite data
        sprites = self.current_editing_asset.get("sprites", [])
        if index >= len(sprites):
            return
        
        sprite = sprites[index]
        
        # Store the current sprite index for Apply Changes
        self.current_sprite_index = index
        
        # Update the sprite details
        self.sprite_anim_var.set(sprite.get("animation_type", ""))
        self.sprite_dir_var.set(sprite.get("direction", ""))
        self.sprite_frame_var.set(sprite.get("frame", 0))
        
        # Display the sprite preview
        self.display_sprite_preview(sprite)
    
    def save_sprite_changes(self):
        """Save changes to the selected sprite's metadata"""
        if not self.current_editing_asset:
            return
        
        # Use the stored sprite index instead of requiring reselection
        if not hasattr(self, 'current_sprite_index') or self.current_sprite_index is None:
            messagebox.showinfo("Info", "Please select a sprite first")
            return
        
        index = self.current_sprite_index
        
        # Get the sprites list
        sprites = self.current_editing_asset.get("sprites", [])
        if index >= len(sprites):
            return
        
        # Update the sprite data
        sprite = sprites[index]
        
        # Get updated values
        sprite["animation_type"] = self.sprite_anim_var.get()
        sprite["direction"] = self.sprite_dir_var.get()
        sprite["frame"] = self.sprite_frame_var.get()
        sprite["updated"] = datetime.datetime.now().isoformat()
        
        # Update the list
        sprites[index] = sprite
        
        # Save the asset
        save_asset(self.base_dir, self.current_editing_asset)
        
        # Update the listbox
        self.sprite_listbox.delete(index)
        sprite_name = self.get_sprite_display_name(sprite)
        self.sprite_listbox.insert(index, sprite_name)
        
        # Reselect the item
        self.sprite_listbox.selection_set(index)
        
        # Update status
        self.status_var.set(f"Updated sprite: {sprite_name}")
    
    def create_animation(self):
        """Create a new animation sequence from selected sprites"""
        if not self.current_editing_asset:
            messagebox.showinfo("Info", "Please select an asset first")
            return
        
        # Get selected sprites
        selected_indices = self.sprite_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "Please select sprites to include in the animation")
            return
        
        # Get animation name
        name = simpledialog.askstring("Animation Name", "Enter a name for this animation:")
        if not name:
            return
        
        # Get animation type
        anim_type = simpledialog.askstring("Animation Type", 
                                        "Enter animation type (idle, walk, attack, etc):")
        if not anim_type:
            anim_type = "idle"
        
        # Get sprites list
        sprites = self.current_editing_asset.get("sprites", [])
        
        # Create sprite references for the animation
        sprite_refs = []
        for idx in selected_indices:
            if idx < len(sprites):
                sprite = sprites[idx]
                sprite_refs.append({
                    "sprite_id": sprite["id"],
                    "frame_index": sprite.get("frame", 0)
                })
        
        # Create animation data
        animation = {
            "id": str(uuid.uuid4()),
            "name": name,
            "animation_type": anim_type,
            "direction": self.sprite_dir_var.get(),  # Use current direction selection
            "fps": 6,  # Default FPS for NES-style animations
            "frames": sprite_refs,
            "loop": True,
            "created": datetime.datetime.now().isoformat()
        }
        
        # Add to asset
        if "animations" not in self.current_editing_asset:
            self.current_editing_asset["animations"] = []
        
        self.current_editing_asset["animations"].append(animation)
        
        # Save the asset
        save_asset(self.base_dir, self.current_editing_asset)
        
        # Update status
        self.status_var.set(f"Created animation: {name} with {len(sprite_refs)} frames")
        
        messagebox.showinfo("Animation Created", 
                         f"Animation '{name}' created with {len(sprite_refs)} frames")
    
    def auto_generate_animations(self):
        """Automatically generate animations based on sprite metadata"""
        if not self.current_editing_asset:
            messagebox.showinfo("Info", "Please select an asset first")
            return
        
        # Get sprites list
        sprites = self.current_editing_asset.get("sprites", [])
        if not sprites:
            messagebox.showinfo("Info", "No sprites available for animation")
            return
        
        # Group sprites by animation_type and direction
        sprite_groups = {}
        for sprite in sprites:
            anim_type = sprite.get("animation_type", "idle")
            direction = sprite.get("direction", "")
            key = (anim_type, direction)
            
            if key not in sprite_groups:
                sprite_groups[key] = []
            
            sprite_groups[key].append(sprite)
        
        # Create animations for each group
        animations_created = 0
        for (anim_type, direction), group_sprites in sprite_groups.items():
            # Sort by frame number
            group_sprites.sort(key=lambda s: s.get("frame", 0))
            
            # Create sprite references
            sprite_refs = [{
                "sprite_id": s["id"],
                "frame_index": s.get("frame", 0)
            } for s in group_sprites]
            
            # Generate name
            if direction:
                name = f"{anim_type}_{direction}"
            else:
                name = anim_type
            
            # Create animation data
            animation = {
                "id": str(uuid.uuid4()),
                "name": name,
                "animation_type": anim_type,
                "direction": direction,
                "fps": 6,  # Default FPS for NES-style animations
                "frames": sprite_refs,
                "loop": True,
                "created": datetime.datetime.now().isoformat()
            }
            
            # Add to asset
            if "animations" not in self.current_editing_asset:
                self.current_editing_asset["animations"] = []
            
            self.current_editing_asset["animations"].append(animation)
            animations_created += 1
        
        # Save the asset
        save_asset(self.base_dir, self.current_editing_asset)
        
        # Update status
        self.status_var.set(f"Auto-generated {animations_created} animations")
        
        messagebox.showinfo("Animations Generated", 
                         f"Successfully created {animations_created} animations")
    
    def browse_export_path(self):
        """Browse for export directory"""
        directory = filedialog.askdirectory(title="Select Export Directory")
        if directory:
            self.export_path.set(directory)
    
    def perform_export(self):
        """Export assets based on current settings"""
        # Get export path
        export_path = self.export_path.get()
        if not export_path:
            messagebox.showwarning("Warning", "Please specify an export directory")
            return
        
        # Create export directory if it doesn't exist
        os.makedirs(export_path, exist_ok=True)
        
        # Clear log
        self.export_log.delete(1.0, tk.END)
        self.log_export_message("Starting export...")        
        
        # Determine which assets to export
        if self.export_selection.get() == "selected":
            if not self.current_asset:
                messagebox.showinfo("Info", "No asset selected for export")
                return
            assets_to_export = [self.current_asset]
        else:  # "all"
            assets_to_export = get_asset_list(self.base_dir)
        
        self.log_export_message(f"Exporting {len(assets_to_export)} assets to: {export_path}")
        
        # Create category directories if organizing by type
        if self.organize_by_type.get():
            for asset_type in ASSET_TYPES.keys():
                os.makedirs(os.path.join(export_path, asset_type.lower()), exist_ok=True)
        
        # Import the export function from core module
        try:
            from asset_wizard_core import export_asset_for_game
        except ImportError as e:
            self.log_export_message(f"Error importing export function: {e}")
            return
        
        # Export each asset
        for asset in assets_to_export:
            try:
                # Determine asset-specific export directory
                if self.organize_by_type.get():
                    asset_export_dir = os.path.join(export_path, asset["type"].lower())
                else:
                    asset_export_dir = export_path
                
                # Export the asset
                asset_name = asset["name"]
                self.log_export_message(f"Exporting {asset_name}...")
                
                # Export JSON with or without sprite files
                result_path = export_asset_for_game(self.base_dir, asset, asset_export_dir)
                
                # If not including sprites, clean up sprite directory
                if not self.include_sprites.get():
                    sprites_dir = os.path.join(asset_export_dir, f"{asset_name.lower().replace(' ', '_')}_sprites")
                    if os.path.exists(sprites_dir):
                        import shutil
                        shutil.rmtree(sprites_dir)
                
                self.log_export_message(f"Successfully exported: {os.path.basename(result_path)}")
            
            except Exception as e:
                self.log_export_message(f"Error exporting {asset['name']}: {e}")
        
        self.log_export_message("Export completed!")
        messagebox.showinfo("Export Complete", f"Successfully exported assets to {export_path}")
    
    def log_export_message(self, message):
        """Add a message to the export log"""
        self.export_log.insert(tk.END, message + "\n")
        self.export_log.see(tk.END)  # Scroll to bottom
        self.root.update_idletasks()  # Update UI
    
    def export_selected_asset(self):
        """Export the currently selected asset"""
        if not self.current_asset:
            messagebox.showinfo("Info", "No asset selected")
            return
        
        # Switch to the export tab
        self.notebook.select(3)
        
        # Set export selection to "selected"
        self.export_selection.set("selected")
        
        # Focus the export button
        self.status_var.set("Ready to export. Click 'Export Now' to proceed.")
        
        # Optional: Auto-perform export
        # self.perform_export()

# Main entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = AssetWizardApp(root)
    root.mainloop()
