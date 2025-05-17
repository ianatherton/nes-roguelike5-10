#!/usr/bin/env python3
"""
NES Sprite Sheet Editor
----------------------
A dedicated module for editing sprite sheets and attaching frames to asset database entries.
Provides functionality to select frames from sprite sheets and associate them with
player characters, enemies, items, etc.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
import json
import uuid
import datetime

class SpriteFrame:
    """Class representing a single frame extracted from a sprite sheet"""
    def __init__(self, image, rect, sheet_path, index):
        self.image = image  # PIL Image object
        self.rect = rect    # (x, y, width, height)
        self.sheet_path = sheet_path  # Source sprite sheet
        self.index = index  # Frame index in the sheet
        self.id = str(uuid.uuid4())
        
    def save(self, path):
        """Save the frame to a file"""
        self.image.save(path)
        return path
        
    def get_data(self):
        """Get frame data for JSON export"""
        return {
            "id": self.id,
            "rect": self.rect,
            "source_sheet": os.path.basename(self.sheet_path),
            "index": self.index
        }

class SpriteSheetEditor:
    """Main sprite sheet editor window"""
    
    def __init__(self, parent, callback=None):
        """Initialize the sprite sheet editor
        
        Args:
            parent: Parent tkinter window
            callback: Function to call when frames are selected, with signature:
                      callback(frames, metadata) where frames is a list of SpriteFrame objects
        """
        self.parent = parent
        self.callback = callback
        
        # Create the editor window
        self.window = tk.Toplevel(parent)
        self.window.title("Sprite Sheet Editor")
        self.window.geometry("1000x700")
        self.window.transient(parent)  # Set as child window
        self.window.grab_set()  # Make modal
        
        # State variables
        self.sprite_sheet = None  # PIL Image
        self.sprite_sheet_path = None
        self.sheet_image = None   # Tkinter PhotoImage
        self.frames = []          # List of SpriteFrame objects
        self.selected_frames = [] # List of indices of selected frames
        self.grid_size = 16       # Default grid size (can be changed by user)
        self.zoom_factor = 2      # Default zoom level
        
        # Selection rectangle
        self.selection_start = None
        self.selection_rect = None
        self.current_rect = None
        
        # Setup UI components
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI components"""
        # Main layout - split into left (tools) and right (canvas) panels
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - controls
        left_frame = ttk.Frame(main_paned, width=300)
        main_paned.add(left_frame, weight=1)
        
        # Controls frame
        controls_frame = ttk.LabelFrame(left_frame, text="Controls")
        controls_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Load button
        ttk.Button(controls_frame, text="Load Sprite Sheet", 
                  command=self.load_sprite_sheet).pack(fill=tk.X, pady=2)
        
        # Grid size controls
        grid_frame = ttk.Frame(controls_frame)
        grid_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(grid_frame, text="Grid Size:").pack(side=tk.LEFT, padx=5)
        self.grid_var = tk.IntVar(value=self.grid_size)
        grid_spin = ttk.Spinbox(grid_frame, from_=8, to=64, increment=8, 
                             textvariable=self.grid_var, width=5)
        grid_spin.pack(side=tk.LEFT, padx=5)
        grid_spin.bind("<Return>", lambda e: self.update_grid())
        ttk.Button(grid_frame, text="Update Grid", 
                  command=self.update_grid).pack(side=tk.LEFT, padx=5)
        
        # Zoom controls
        zoom_frame = ttk.Frame(controls_frame)
        zoom_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(zoom_frame, text="Zoom:").pack(side=tk.LEFT, padx=5)
        ttk.Button(zoom_frame, text="-", width=2,
                 command=self.zoom_out).pack(side=tk.LEFT)
        self.zoom_var = tk.IntVar(value=self.zoom_factor)
        ttk.Label(zoom_frame, textvariable=self.zoom_var, width=3).pack(side=tk.LEFT)
        ttk.Button(zoom_frame, text="+", width=2,
                 command=self.zoom_in).pack(side=tk.LEFT)
        
        # Selected frames frame
        frames_frame = ttk.LabelFrame(left_frame, text="Selected Frames")
        frames_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Listbox to show selected frames
        frame_list_frame = ttk.Frame(frames_frame)
        frame_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.frame_listbox = tk.Listbox(frame_list_frame, height=10)
        scrollbar = ttk.Scrollbar(frame_list_frame, orient=tk.VERTICAL, 
                                command=self.frame_listbox.yview)
        self.frame_listbox.configure(yscrollcommand=scrollbar.set)
        self.frame_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame navigation buttons
        btn_frame = ttk.Frame(frames_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Remove Selected", 
                  command=self.remove_selected_frame).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear All", 
                  command=self.clear_all_frames).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Auto-Detect Frames", 
                  command=self.auto_detect_frames).pack(side=tk.LEFT, padx=2)
        
        # Meta-data frame
        meta_frame = ttk.LabelFrame(left_frame, text="Frame Metadata")
        meta_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(meta_frame, text="Frame Size:").pack(anchor=tk.W, padx=5, pady=2)
        size_frame = ttk.Frame(meta_frame)
        size_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(size_frame, text="Width:").pack(side=tk.LEFT, padx=5)
        self.frame_width_var = tk.IntVar(value=16)
        ttk.Spinbox(size_frame, from_=8, to=64, textvariable=self.frame_width_var, 
                  width=5).pack(side=tk.LEFT)
        
        ttk.Label(size_frame, text="Height:").pack(side=tk.LEFT, padx=5)
        self.frame_height_var = tk.IntVar(value=16)
        ttk.Spinbox(size_frame, from_=8, to=64, textvariable=self.frame_height_var, 
                  width=5).pack(side=tk.LEFT)
        
        # Button to attach frames to asset
        attach_frame = ttk.Frame(left_frame)
        attach_frame.pack(fill=tk.X, pady=10, padx=5)
        
        ttk.Button(attach_frame, text="Attach Frames to Asset", 
                  command=self.attach_frames).pack(side=tk.RIGHT)
        ttk.Button(attach_frame, text="Cancel", 
                  command=self.window.destroy).pack(side=tk.LEFT)
        
        # Right panel - sprite sheet display
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        # Canvas for sprite sheet
        canvas_frame = ttk.LabelFrame(right_frame, text="Sprite Sheet")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbars to canvas
        canvas_container = ttk.Frame(canvas_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        
        # Canvas
        self.canvas = tk.Canvas(canvas_container, 
                             xscrollcommand=h_scrollbar.set,
                             yscrollcommand=v_scrollbar.set,
                             bg="light gray")
        
        # Configure scrollbars
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        
        # Layout with scrollbars
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Instructions
        ttk.Label(right_frame, text="Click and drag to select sprite frames. Double-click to auto-select based on grid.", 
                wraplength=500, justify=tk.LEFT).pack(pady=5)
    
    def load_sprite_sheet(self):
        """Load a sprite sheet image"""
        file_path = filedialog.askopenfilename(
            title="Select Sprite Sheet",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if not file_path:
            return
        
        try:
            # Load the image with PIL
            self.sprite_sheet = Image.open(file_path)
            self.sprite_sheet_path = file_path
            
            # Clear previous frames
            self.frames = []
            self.selected_frames = []
            self.frame_listbox.delete(0, tk.END)
            
            # Update canvas
            self.update_canvas()
            
            # Set window title
            self.window.title(f"Sprite Sheet Editor - {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load sprite sheet: {e}")
    
    def update_grid(self):
        """Update the grid size and redraw"""
        self.grid_size = self.grid_var.get()
        self.update_canvas()
    
    def update_canvas(self):
        """Update the canvas with the current sprite sheet and grid"""
        self.canvas.delete("all")  # Clear canvas
        
        if not self.sprite_sheet:
            return
        
        # Apply zoom
        zoomed_width = self.sprite_sheet.width * self.zoom_factor
        zoomed_height = self.sprite_sheet.height * self.zoom_factor
        
        # Resize image for display
        display_img = self.sprite_sheet.resize((zoomed_width, zoomed_height), Image.NEAREST)
        
        # Convert to PhotoImage for tkinter
        self.sheet_image = ImageTk.PhotoImage(display_img)
        
        # Display the image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.sheet_image)
        
        # Set the scroll region
        self.canvas.config(scrollregion=(0, 0, zoomed_width, zoomed_height))
        
        # Draw grid if needed
        if self.grid_size > 0:
            grid_size = self.grid_size * self.zoom_factor
            for x in range(0, zoomed_width, grid_size):
                self.canvas.create_line(x, 0, x, zoomed_height, fill="#0000FF40")
            for y in range(0, zoomed_height, grid_size):
                self.canvas.create_line(0, y, zoomed_width, y, fill="#0000FF40")
        
        # Draw existing frame selections
        for frame in self.frames:
            x, y, w, h = frame.rect
            x *= self.zoom_factor
            y *= self.zoom_factor
            w *= self.zoom_factor
            h *= self.zoom_factor
            self.canvas.create_rectangle(x, y, x+w, y+h, outline="red", width=2, dash=(2, 2))
    
    def zoom_in(self):
        """Increase zoom level"""
        if self.zoom_factor < 8:
            self.zoom_factor += 1
            self.zoom_var.set(self.zoom_factor)
            self.update_canvas()
    
    def zoom_out(self):
        """Decrease zoom level"""
        if self.zoom_factor > 1:
            self.zoom_factor -= 1
            self.zoom_var.set(self.zoom_factor)
            self.update_canvas()
    
    def on_canvas_click(self, event):
        """Handle canvas click event - start selection"""
        if not self.sprite_sheet:
            return
        
        # Get position, adjusted for zoom and scroll
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Snap to grid if needed
        if self.grid_size > 0:
            grid_px = self.grid_size * self.zoom_factor
            x = (x // grid_px) * grid_px
            y = (y // grid_px) * grid_px
        
        # Store start position
        self.selection_start = (x, y)
        
        # Create initial selection rectangle
        self.selection_rect = self.canvas.create_rectangle(
            x, y, x, y, outline="green", width=2
        )
    
    def on_canvas_drag(self, event):
        """Handle canvas drag event - update selection"""
        if not self.selection_start:
            return
        
        # Get current position, adjusted for zoom and scroll
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Snap to grid if needed
        if self.grid_size > 0:
            grid_px = self.grid_size * self.zoom_factor
            x = ((x // grid_px) + 1) * grid_px
            y = ((y // grid_px) + 1) * grid_px
        
        # Update the selection rectangle
        self.canvas.coords(
            self.selection_rect,
            self.selection_start[0], self.selection_start[1], x, y
        )
    
    def on_canvas_release(self, event):
        """Handle canvas release event - finalize selection"""
        if not self.selection_start:
            return
        
        # Get current position, adjusted for zoom and scroll
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Snap to grid if needed
        if self.grid_size > 0:
            grid_px = self.grid_size * self.zoom_factor
            x = ((x // grid_px) + 1) * grid_px
            y = ((y // grid_px) + 1) * grid_px
        
        # Get the selection rectangle
        x1, y1 = self.selection_start
        x2, y2 = x, y
        
        # Ensure x1,y1 is the top-left and x2,y2 is bottom-right
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Convert from zoomed to original coordinates
        orig_x1 = int(x1 / self.zoom_factor)
        orig_y1 = int(y1 / self.zoom_factor)
        orig_x2 = int(x2 / self.zoom_factor)
        orig_y2 = int(y2 / self.zoom_factor)
        
        # Calculate width and height
        width = orig_x2 - orig_x1
        height = orig_y2 - orig_y1
        
        # Check if selection is large enough
        if width <= 0 or height <= 0:
            self.canvas.delete(self.selection_rect)
            self.selection_start = None
            self.selection_rect = None
            return
        
        # Crop the selected region from the original image
        frame_img = self.sprite_sheet.crop((orig_x1, orig_y1, orig_x2, orig_y2))
        
        # Create a new frame object
        frame = SpriteFrame(
            frame_img, 
            (orig_x1, orig_y1, width, height),
            self.sprite_sheet_path,
            len(self.frames)
        )
        
        # Add to frames list
        self.frames.append(frame)
        
        # Add to listbox
        frame_name = f"Frame {len(self.frames)}: {width}x{height} at ({orig_x1},{orig_y1})"
        self.frame_listbox.insert(tk.END, frame_name)
        
        # Update frame width/height vars
        self.frame_width_var.set(width)
        self.frame_height_var.set(height)
        
        # Clear selection
        self.canvas.delete(self.selection_rect)
        self.selection_start = None
        self.selection_rect = None
        
        # Update canvas to show the selection as a frame
        self.update_canvas()
    
    def remove_selected_frame(self):
        """Remove the selected frame from the list"""
        selection = self.frame_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        
        # Remove from frames list
        del self.frames[index]
        
        # Update listbox
        self.frame_listbox.delete(index)
        
        # Renumber the remaining frames
        for i in range(index, len(self.frames)):
            self.frames[i].index = i
            self.frame_listbox.delete(i)
            frame = self.frames[i]
            x, y, w, h = frame.rect
            frame_name = f"Frame {i+1}: {w}x{h} at ({x},{y})"
            self.frame_listbox.insert(i, frame_name)
        
        # Update canvas
        self.update_canvas()
    
    def clear_all_frames(self):
        """Clear all selected frames"""
        if not self.frames:
            return
        
        if not messagebox.askyesno("Confirm", "Clear all selected frames?"):
            return
        
        # Clear frames
        self.frames = []
        self.selected_frames = []
        
        # Clear listbox
        self.frame_listbox.delete(0, tk.END)
        
        # Update canvas
        self.update_canvas()
    
    def auto_detect_frames(self):
        """Automatically detect frames based on grid size"""
        if not self.sprite_sheet:
            return
        
        # Get dimensions
        frame_width = self.frame_width_var.get()
        frame_height = self.frame_height_var.get()
        
        if frame_width <= 0 or frame_height <= 0:
            messagebox.showwarning("Invalid Size", "Frame width and height must be positive")
            return
        
        # Clear existing frames
        self.clear_all_frames()
        
        # Calculate number of frames in each dimension
        cols = self.sprite_sheet.width // frame_width
        rows = self.sprite_sheet.height // frame_height
        
        # Generate frames
        for row in range(rows):
            for col in range(cols):
                x = col * frame_width
                y = row * frame_height
                
                # Crop the frame
                frame_img = self.sprite_sheet.crop(
                    (x, y, x + frame_width, y + frame_height)
                )
                
                # Create a new frame object
                frame = SpriteFrame(
                    frame_img, 
                    (x, y, frame_width, frame_height),
                    self.sprite_sheet_path,
                    len(self.frames)
                )
                
                # Add to frames list
                self.frames.append(frame)
                
                # Add to listbox
                frame_name = f"Frame {len(self.frames)}: {frame_width}x{frame_height} at ({x},{y})"
                self.frame_listbox.insert(tk.END, frame_name)
        
        # Update canvas
        self.update_canvas()
        
        messagebox.showinfo("Auto-Detect", f"Detected {len(self.frames)} frames of size {frame_width}x{frame_height}")
    
    def attach_frames(self):
        """Send selected frames back to parent via callback"""
        if not self.frames:
            messagebox.showinfo("No Frames", "No frames selected to attach")
            return
        
        # If callback is provided, call it with the frames
        if self.callback:
            # Get frame metadata
            metadata = {
                "source_sheet": self.sprite_sheet_path,
                "frame_count": len(self.frames),
                "creation_time": datetime.datetime.now().isoformat()
            }
            
            self.callback(self.frames, metadata)
        
        # Close the window
        self.window.destroy()

# Stand-alone test if run directly
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sprite Sheet Editor Test")
    root.geometry("300x200")
    
    def test_callback(frames, metadata):
        print(f"Got {len(frames)} frames:")
        for i, frame in enumerate(frames):
            print(f"  Frame {i}: {frame.rect}")
        print("Metadata:", metadata)
    
    ttk.Button(root, text="Open Sprite Sheet Editor", 
             command=lambda: SpriteSheetEditor(root, test_callback)).pack(pady=20)
    
    root.mainloop()
