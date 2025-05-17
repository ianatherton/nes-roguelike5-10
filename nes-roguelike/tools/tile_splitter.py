#!/usr/bin/env python3
"""
NES Tile Splitter Tool
----------------------
This tool splits multi-tile sprites into individual 8x8 tiles and organizes them
for NES development. It works with the sprite manager to properly handle 
the metadata and relationships between tiles.
"""

import os
import sys
import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk, ImageDraw

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

class TileSplitter:
    """Tool for splitting multi-tile sprites into individual 8x8 tiles"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("NES Tile Splitter")
        self.root.geometry("1000x600")
        
        self.current_image = None
        self.tile_size = 8  # NES tiles are 8x8 pixels
        self.split_tiles = []
        self.current_palette = [0, 1, 2, 3]  # Default palette indices
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main layout with paned window
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left side - controls
        control_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(control_frame, weight=1)
        
        # Load button
        ttk.Button(control_frame, text="Load Sprite to Split", command=self.load_sprite).pack(fill=tk.X, pady=5)
        
        # Configuration options
        config_frame = ttk.LabelFrame(control_frame, text="Configuration", padding=5)
        config_frame.pack(fill=tk.X, pady=5)
        
        # Sprite configuration
        ttk.Label(config_frame, text="Sprite Configuration:").pack(anchor=tk.W)
        self.config_var = tk.StringVar(value="quad")
        config_options = ttk.Combobox(config_frame, textvariable=self.config_var,
                                      values=["single", "double_h", "double_v", "quad"])
        config_options.pack(fill=tk.X, pady=2)
        config_options.bind("<<ComboboxSelected>>", self.update_preview)
        
        # Palette editor
        palette_frame = ttk.LabelFrame(control_frame, text="Palette", padding=5)
        palette_frame.pack(fill=tk.X, pady=5)
        
        # Four color selectors for the palette
        self.palette_buttons = []
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
        
        ttk.Button(palette_frame, text="Apply Palette", command=self.update_preview).pack(fill=tk.X, pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Split Into Tiles", command=self.split_into_tiles).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Save Individual Tiles", command=self.save_tiles).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Export Metadata", command=self.export_metadata).pack(fill=tk.X, pady=2)
        
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
    
    def update_palette_preview(self, index):
        """Update the palette preview button color"""
        color_var, button = self.palette_buttons[index]
        color_index = color_var.get()
        if 0 <= color_index < len(NES_PALETTE):
            rgb = NES_PALETTE[color_index]
            hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            button.config(bg=hex_color)
    
    def load_sprite(self):
        """Load a sprite image to split"""
        filepath = filedialog.askopenfilename(
            title="Select Sprite Image",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            self.current_image = Image.open(filepath)
            self.current_filepath = filepath
            self.update_preview()
            messagebox.showinfo("Image Loaded", f"Loaded image: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")
    
    def update_preview(self, event=None):
        """Update the original sprite preview with current settings"""
        if self.current_image is None:
            return
        
        # Display original with zoom factor
        zoom = 6  # 6x zoom for better visibility
        preview_img = self.current_image.resize(
            (self.current_image.width * zoom, self.current_image.height * zoom),
            Image.NEAREST
        )
        
        # Apply current palette if not in indexed mode
        if self.current_image.mode != "P":
            # This is simplified - a real implementation would need to properly
            # convert the image to the NES palette
            pass
        
        photo = ImageTk.PhotoImage(preview_img)
        self.original_preview.configure(image=photo)
        self.original_preview.image = photo
    
    def split_into_tiles(self):
        """Split the loaded sprite into individual 8x8 tiles"""
        if self.current_image is None:
            messagebox.showinfo("No Image", "Please load a sprite image first")
            return
        
        # Determine the tile configuration
        config = self.config_var.get()
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
                tile = self.current_image.crop(box)
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
        base_name = os.path.splitext(os.path.basename(self.current_filepath))[0]
        config = self.config_var.get()
        
        # Save each tile
        for tile_info in self.split_tiles:
            pos_name = tile_info["position_name"]
            filename = f"{base_name}_{pos_name}.png"
            filepath = os.path.join(save_dir, filename)
            
            tile_info["tile"].save(filepath)
            tile_info["filename"] = filename
            tile_info["filepath"] = filepath
        
        messagebox.showinfo("Tiles Saved", f"Saved {len(self.split_tiles)} tiles to {save_dir}")
    
    def export_metadata(self):
        """Export metadata for the split tiles"""
        if not self.split_tiles:
            messagebox.showinfo("No Tiles", "Please split the sprite into tiles first")
            return
        
        # Create metadata
        metadata = {
            "original_sprite": os.path.basename(self.current_filepath),
            "configuration": self.config_var.get(),
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
    app = TileSplitter(root)
    root.mainloop()
