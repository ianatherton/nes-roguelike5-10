import os
import json
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk

class SpriteManagerTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Arkista's Ring Sprite Manager")
        self.root.geometry("1200x800")
        
        self.sprite_data = {}
        self.current_sprite = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Left panel - sprite list and navigation
        left_frame = ttk.Frame(self.root, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Button(left_frame, text="Load Sprite Directory", command=self.load_directory).pack(pady=5)
        
        ttk.Label(left_frame, text="Sprite List:").pack(pady=5)
        self.sprite_listbox = tk.Listbox(left_frame, width=30, height=30)
        self.sprite_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        self.sprite_listbox.bind('<<ListboxSelect>>', self.select_sprite)
        
        # Right panel - sprite details and tagging
        right_frame = ttk.Frame(self.root, padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Sprite preview
        preview_frame = ttk.LabelFrame(right_frame, text="Sprite Preview", padding=10)
        preview_frame.pack(pady=10, fill=tk.X)
        
        self.sprite_preview = ttk.Label(preview_frame)
        self.sprite_preview.pack(pady=10)
        
        # Sprite data entry
        data_frame = ttk.LabelFrame(right_frame, text="Sprite Data", padding=10)
        data_frame.pack(pady=10, fill=tk.X)
        
        # Name field
        name_frame = ttk.Frame(data_frame)
        name_frame.pack(pady=5, fill=tk.X)
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(name_frame, width=30)
        self.name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Type dropdown
        type_frame = ttk.Frame(data_frame)
        type_frame.pack(pady=5, fill=tk.X)
        ttk.Label(type_frame, text="Type:").pack(side=tk.LEFT)
        self.type_combo = ttk.Combobox(type_frame, values=["Player", "Enemy", "Item", "Environment", "UI", "Unknown"])
        self.type_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Bank field
        bank_frame = ttk.Frame(data_frame)
        bank_frame.pack(pady=5, fill=tk.X)
        ttk.Label(bank_frame, text="Bank:").pack(side=tk.LEFT)
        self.bank_entry = ttk.Entry(bank_frame, width=10)
        self.bank_entry.pack(side=tk.LEFT, padx=5)
        
        # Animation frames
        anim_frame = ttk.Frame(data_frame)
        anim_frame.pack(pady=5, fill=tk.X)
        ttk.Label(anim_frame, text="Animation Frames:").pack(side=tk.LEFT)
        self.anim_entry = ttk.Entry(anim_frame, width=30)
        self.anim_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Notes field
        notes_frame = ttk.Frame(data_frame)
        notes_frame.pack(pady=5, fill=tk.X)
        ttk.Label(notes_frame, text="Notes:").pack(anchor=tk.NW)
        self.notes_text = tk.Text(notes_frame, height=5, width=40)
        self.notes_text.pack(pady=5, fill=tk.X)
        
        # Save button
        ttk.Button(data_frame, text="Save Sprite Data", command=self.save_sprite_data).pack(pady=10)
        
        # Export button
        ttk.Button(right_frame, text="Export All Sprite Data", command=self.export_all_data).pack(pady=10)
    
    def load_directory(self):
        directory = filedialog.askdirectory(title="Select Sprite Directory")
        if not directory:
            return
            
        self.sprite_listbox.delete(0, tk.END)
        self.sprite_data = {}
        
        # Load all PNG files from directory
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.png'):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, directory)
                    self.sprite_listbox.insert(tk.END, relative_path)
                    
                    # Check for metadata file
                    metadata_path = os.path.splitext(full_path)[0] + '.json'
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            self.sprite_data[relative_path] = json.load(f)
                    else:
                        self.sprite_data[relative_path] = {
                            "name": os.path.splitext(file)[0],
                            "type": "Unknown",
                            "bank": "",
                            "animation_frames": "",
                            "notes": ""
                        }
    
    def select_sprite(self, event):
        selected_indices = self.sprite_listbox.curselection()
        if not selected_indices:
            return
            
        self.current_sprite = self.sprite_listbox.get(selected_indices[0])
        data = self.sprite_data[self.current_sprite]
        
        # Load sprite image
        directory = os.path.dirname(os.path.dirname(self.sprite_listbox.get(0)))
        image_path = os.path.join(directory, self.current_sprite)
        
        try:
            image = Image.open(image_path)
            # Scale image, maintaining aspect ratio
            base_size = 200
            width, height = image.size
            scale = min(base_size/width, base_size/height)
            new_size = (int(width*scale*4), int(height*scale*4))  # 4x zoom for NES sprites
            
            image = image.resize(new_size, Image.NEAREST)
            photo = ImageTk.PhotoImage(image)
            
            self.sprite_preview.configure(image=photo)
            self.sprite_preview.image = photo  # Keep reference
        except Exception as e:
            print(f"Error loading image: {e}")
        
        # Populate form fields
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, data.get("name", ""))
        
        self.type_combo.set(data.get("type", "Unknown"))
        
        self.bank_entry.delete(0, tk.END)
        self.bank_entry.insert(0, data.get("bank", ""))
        
        self.anim_entry.delete(0, tk.END)
        self.anim_entry.insert(0, data.get("animation_frames", ""))
        
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", data.get("notes", ""))
    
    def save_sprite_data(self):
        if not self.current_sprite:
            return
            
        self.sprite_data[self.current_sprite] = {
            "name": self.name_entry.get(),
            "type": self.type_combo.get(),
            "bank": self.bank_entry.get(),
            "animation_frames": self.anim_entry.get(),
            "notes": self.notes_text.get("1.0", tk.END).strip()
        }
        
        # Save to JSON file
        directory = os.path.dirname(os.path.dirname(self.sprite_listbox.get(0)))
        image_path = os.path.join(directory, self.current_sprite)
        metadata_path = os.path.splitext(image_path)[0] + '.json'
        
        with open(metadata_path, 'w') as f:
            json.dump(self.sprite_data[self.current_sprite], f, indent=2)
    
    def export_all_data(self):
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
            for sprite_type, count in types.items():
                f.write(f"  {sprite_type}: {count}\n")
            
            f.write("\nDetailed Sprite List:\n")
            for sprite, data in self.sprite_data.items():
                f.write(f"\n{sprite}\n")
                f.write(f"  Name: {data.get('name', '')}\n")
                f.write(f"  Type: {data.get('type', 'Unknown')}\n")
                f.write(f"  Bank: {data.get('bank', '')}\n")
                f.write(f"  Animation: {data.get('animation_frames', '')}\n")
                if data.get('notes'):
                    f.write(f"  Notes: {data.get('notes', '')}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = SpriteManagerTool(root)
    root.mainloop()
