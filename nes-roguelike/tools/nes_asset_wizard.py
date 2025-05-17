#!/usr/bin/env python3
"""
NES Asset Wizard - Main Launcher
-------------------------------
An all-in-one wizard application for organizing and managing NES game assets
for Craven Caverns or similar NES projects.

This launcher combines the core functionality and UI modules.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import argparse

# Import the wizard modules
try:
    from asset_wizard_core import ensure_asset_directory
    from asset_wizard_ui import AssetWizardApp
except ImportError:
    print("Error: Could not import asset wizard modules.")
    print("Make sure asset_wizard_core.py and asset_wizard_ui.py are in the same directory.")
    sys.exit(1)

def main():
    """Main entry point for the asset wizard application"""
    parser = argparse.ArgumentParser(description="NES Asset Wizard - Sprite Organization Tool")
    parser.add_argument('--base-dir', dest='base_dir', 
                      help='Base directory for storing assets (default: ~/.nes_asset_wizard)')
    parser.add_argument('--project-dir', dest='project_dir',
                      help='Project directory to scan for existing assets')
    
    args = parser.parse_args()
    
    # Set base directory
    if args.base_dir:
        base_dir = args.base_dir
    else:
        base_dir = os.path.join(os.path.expanduser("~"), ".nes_asset_wizard")
    
    # Create the base directory if it doesn't exist
    ensure_asset_directory(base_dir)
    
    # Create and run the main application
    root = tk.Tk()
    app = AssetWizardApp(root, base_dir)
    
    # Set application icon if available
    try:
        # Look for an icon in common locations
        icon_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "icon.png"),
            os.path.join(base_dir, "assets", "icon.png")
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                from PIL import Image, ImageTk
                icon = ImageTk.PhotoImage(file=icon_path)
                root.iconphoto(True, icon)
                break
    except Exception as e:
        print(f"Warning: Could not set application icon: {e}")
    
    # If project directory was specified, scan for assets
    if args.project_dir and os.path.exists(args.project_dir):
        # TODO: Implement project scan functionality
        pass
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main()
