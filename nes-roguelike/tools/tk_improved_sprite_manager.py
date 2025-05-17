#!/usr/bin/env python3
"""
Improved Sprite Manager for NES Roguelike
Supports individual 8x8 sprites and configurable multi-tile sprites
"""
import os
import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk

class ImprovedSpriteManager:
    def __init__(self, root):
        self.root = root
        self.root.title("NES Sprite Manager")
        self.root.geometry("1200x800")
        
        self.sprite_data = {}
        self.current_sprite = None
        self.sprite_configs = {
            "single": (1, 1),     # 1x1 (8x8) single sprite
            "double_h": (2, 1),   # 2x1 (16x8) horizontal double sprite
            "double_v": (1, 2),   # 1x2 (8x16) vertical double sprite
            "quad": (2, 2)        # 2x2 (16x16) quad sprite (standard character)
        }
        
        self.current_config = "quad"  # Default to quad sprites (16x16)
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame with two panes
        self.main_panes = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_panes.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - sprite list and navigation
        left_frame = ttk.Frame(self.main_panes, padding=5)
        self.main_panes.add(left_frame, weight=1)
        
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
        right_frame = ttk.Frame(self.main_panes, padding=5)
        self.main_panes.add(right_frame, weight=2)
        
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
    
    def filter_sprite_list(self, *args):
        """Filter sprite list based on search text"""
        search_text = self.search_var.get().lower()
        
        self.sprite_listbox.delete(0, tk.END)
        for sprite_path in sorted(self.sprite_data.keys()):
            if search_text in sprite_path.lower() or search_text in self.sprite_data[sprite_path].get("name", "").lower():
                self.sprite_listbox.insert(tk.END, sprite_path)
    
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
        if not self.current_sprite or not hasattr(self, 'base_directory'):
            return
            
        self.sprite_data[self.current_sprite] = {
            "name": self.name_entry.get(),
            "type": self.type_combo.get(),
            "bank": self.bank_entry.get(),
            "animation_frames": self.anim_entry.get(),
            "size": self.size_entry.get(),
            "palette": self.palette_entry.get(),
            "notes": self.notes_text.get("1.0", tk.END).strip(),
            "configuration": self.current_config
        }
        
        # Use the stored base directory for resolving paths
        image_path = os.path.join(self.base_directory, self.current_sprite)
        metadata_path = os.path.splitext(image_path)[0] + '.json'
        
        # Save metadata file
        with open(metadata_path, 'w') as f:
            json.dump(self.sprite_data[self.current_sprite], f, indent=2)
            
        messagebox.showinfo("Saved", f"Metadata saved for {self.current_sprite}")
    
    def tag_similar(self):
        """Apply current sprite's tags to visually similar sprites"""
        if not self.current_sprite or not self.sprite_data:
            return
            
        current_type = self.type_combo.get()
        if current_type == "Unknown":
            messagebox.showwarning("Warning", "Please set a specific type before tagging similar sprites")
            return
            
        # Ask user for confirmation
        if not messagebox.askyesno("Confirm", f"Apply '{current_type}' type to similar sprites?"):
            return
            
        # Get current sprite data
        current_data = self.sprite_data[self.current_sprite]
        tag_count = 0
        
        # Apply to all sprites with similar names
        current_base = os.path.basename(self.current_sprite)
        current_prefix = current_base.split('_')[0] if '_' in current_base else ""
        
        if not current_prefix:
            messagebox.showwarning("Warning", "Couldn't determine sprite prefix for similarity matching")
            return
            
        for sprite_path in self.sprite_data:
            # Skip current sprite
            if sprite_path == self.current_sprite:
                continue
                
            # Check if sprite name has same prefix
            sprite_base = os.path.basename(sprite_path)
            if sprite_base.startswith(current_prefix):
                # Update type and other relevant fields
                self.sprite_data[sprite_path]["type"] = current_data["type"]
                
                # If animation frame info exists, preserve it but update other fields
                if not self.sprite_data[sprite_path].get("animation_frames"):
                    self.sprite_data[sprite_path]["animation_frames"] = current_data.get("animation_frames", "")
                
                # Always copy these fields
                self.sprite_data[sprite_path]["bank"] = current_data.get("bank", "")
                self.sprite_data[sprite_path]["configuration"] = current_data.get("configuration", self.current_config)
                self.sprite_data[sprite_path]["size"] = current_data.get("size", "")
                self.sprite_data[sprite_path]["palette"] = current_data.get("palette", "")
                
                # Save the updated metadata
                if hasattr(self, 'base_directory'):
                    metadata_path = os.path.splitext(os.path.join(self.base_directory, sprite_path))[0] + '.json'
                    with open(metadata_path, 'w') as f:
                        json.dump(self.sprite_data[sprite_path], f, indent=2)
                else:
                    messagebox.showerror("Error", "Base directory not set. Please reload sprites.")
                
                tag_count += 1
        
        messagebox.showinfo("Tagging Complete", f"Applied tags to {tag_count} similar sprites")
    
    def detect_animations(self):
        """Auto-detect animation sequences in the current selection"""
        if not self.current_sprite:
            return
            
        current_base = os.path.basename(self.current_sprite)
        parts = current_base.split('_')
        
        if len(parts) < 2:
            messagebox.showwarning("Warning", "Sprite filename doesn't follow the convention for animation detection")
            return
            
        # Assume format like sprite_012.png where 012 is sequence number
        try:
            # Try to find numeric part that might be frame number
            frame_number = None
            for part in parts:
                if part.isdigit():
                    frame_number = int(part)
                    break
            
            if frame_number is None:
                raise ValueError("No frame number found")
                
            # Find prefix (everything before frame number)
            prefix = current_base[:current_base.find(str(frame_number))]
            
            # Find all sprites with same prefix
            animation_frames = []
            for sprite_path in sorted(self.sprite_data.keys()):
                sprite_base = os.path.basename(sprite_path)
                if sprite_base.startswith(prefix):
                    # Extract frame number
                    for part in sprite_base.split('_'):
                        if part.isdigit():
                            animation_frames.append(int(part))
                            break
            
            # Sort frame numbers
            animation_frames.sort()
            
            # Update animation frames field
            self.anim_entry.delete(0, tk.END)
            self.anim_entry.insert(0, ",".join(map(str, animation_frames)))
            
            messagebox.showinfo("Animation Detection", 
                               f"Detected {len(animation_frames)} frames in animation sequence")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error detecting animation: {e}")
    
    def export_all_data(self):
        """Export all sprite metadata to a JSON file"""
        if not self.sprite_data:
            messagebox.showwarning("Warning", "No sprite data to export")
            return
            
        output_file = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export All Sprite Data"
        )
        
        if not output_file:
            return
        
        # Create a more organized data structure for export
        export_data = {
            "metadata": {
                "total_sprites": len(self.sprite_data),
                "export_date": "2025-05-13",
                "categories": {}
            },
            "sprites": self.sprite_data
        }
        
        # Count sprites by type
        for sprite, data in self.sprite_data.items():
            sprite_type = data.get("type", "Unknown")
            if sprite_type not in export_data["metadata"]["categories"]:
                export_data["metadata"]["categories"][sprite_type] = 0
            export_data["metadata"]["categories"][sprite_type] += 1
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        # Generate report
        report_file = os.path.splitext(output_file)[0] + "_report.txt"
        self.generate_sprite_report(report_file)
        
        messagebox.showinfo("Export Complete", 
                           f"Exported {len(self.sprite_data)} sprite metadata entries to {output_file}\n" +
                           f"Report saved to {report_file}")
    
    def generate_sprite_report(self, report_file):
        """Generate a detailed report of all sprites"""
        with open(report_file, 'w') as f:
            f.write("Arkista's Ring Sprite Report\n")
            f.write("==========================\n\n")
            
            # Count by type
            types = {}
            for sprite, data in self.sprite_data.items():
                sprite_type = data.get("type", "Unknown")
                if sprite_type not in types:
                    types[sprite_type] = 0
                types[sprite_type] += 1
            
            f.write("Sprite Count by Type:\n")
            for sprite_type, count in sorted(types.items()):
                f.write(f"  {sprite_type}: {count}\n")
            
            # By animation
            animations = {}
            for sprite, data in self.sprite_data.items():
                if data.get("animation_frames"):
                    anim_key = f"{data.get('name', 'unknown')} animation"
                    if anim_key not in animations:
                        animations[anim_key] = []
                    animations[anim_key].append(sprite)
            
            if animations:
                f.write("\nAnimation Sequences:\n")
                for anim_name, sprites in animations.items():
                    f.write(f"  {anim_name}: {len(sprites)} frames\n")
            
            # Detailed list
            f.write("\nDetailed Sprite List:\n")
            for sprite, data in sorted(self.sprite_data.items()):
                f.write(f"\n{sprite}\n")
                f.write(f"  Name: {data.get('name', '')}\n")
                f.write(f"  Type: {data.get('type', 'Unknown')}\n")
                f.write(f"  Bank: {data.get('bank', '')}\n")
                f.write(f"  Size: {data.get('size', '')}\n")
                if data.get('animation_frames'):
                    f.write(f"  Animation: {data.get('animation_frames', '')}\n")
                if data.get('notes'):
                    f.write(f"  Notes: {data.get('notes', '')}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImprovedSpriteManager(root)
    root.mainloop()
