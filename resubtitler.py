import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import os
import re
from pathlib import Path
import pprint


'''
Subtitle renaming program:

User provides subtitle files and media files (e.g. tv/anime episodes) which are normalized to the same naming scheme.
'''

# TODO: support offsets (positive/negative, e.g. if episode numbering scheme differs from subtitle numbering scheme)
# TODO: support re-timing the subtitles (more involved, probably only one file type--srt?)

class ResubtitlerApp:
    def __init__(self, root):
        self.root = root
        root.title("Subtitle Renamer")
        
        self.subtitle_dir = ""
        self.episode_dir = ""

        # Configure the grid layout
        root.grid_rowconfigure(0, weight=0)
        root.grid_rowconfigure(1, weight=0)
        root.grid_rowconfigure(2, weight=0)
        root.grid_rowconfigure(3, weight=0)
        root.grid_rowconfigure(4, weight=0)
        root.grid_rowconfigure(5, weight=0)
        root.grid_rowconfigure(6, weight=0)
        root.grid_rowconfigure(7, weight=1)  # Allow vertical expansion for preview areas
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        
        ## Component init
        self._init_directory_selection(root)
        self._init_filetype_selection(root)
        self._init_regex_inputs(root)
        self._init_preview_area(root)
    
    @staticmethod
    def _engrid(row, column, entity):
        entity.grid(row=row, column=column, sticky='ew', padx=5, pady=5)
    
    def _init_directory_selection(self, root):
        # Directory selection labels
        self.subtitle_dir_label = ttk.Label(root, text="No directory selected")
        self._engrid(0, 0, self.subtitle_dir_label)

        self.episode_dir_label = ttk.Label(root, text="No directory selected")
        self._engrid(0, 1, self.episode_dir_label)

        # Directory selection buttons
        self.subtitle_dir_button = ttk.Button(root, text="Select Subtitle Directory", command=self.select_subtitle_dir)
        self._engrid(1, 0, self.subtitle_dir_button)
        
        self.episode_dir_button = ttk.Button(root, text="Select Episode Directory", command=self.select_episode_dir)
        self._engrid(1, 1, self.episode_dir_button)
        
    def _init_filetype_selection(self, root):
        # Filetype selection labels
        self.subtitle_filetype_label = ttk.Label(root, text="Subtitle filetype")
        self._engrid(2, 0, self.subtitle_filetype_label)

        self.episode_filetype_label = ttk.Label(root, text="Episode filetype")
        self._engrid(2, 1, self.episode_filetype_label)

        # Filetype entries
        self.subtitle_ext_var = tk.StringVar()
        self.subtitle_ext_var.set("srt")
        self.subtitle_ext_entry = ttk.Entry(root, textvariable=self.subtitle_ext_var, width=10)
        self._engrid(3, 0, self.subtitle_ext_entry)
        self.episode_ext_var = tk.StringVar()
        self.episode_ext_var.set("mkv")
        self.episode_ext_entry = ttk.Entry(self.root, textvariable=self.episode_ext_var, width=10)
        self._engrid(3, 1, self.episode_ext_entry)

    def _init_regex_inputs(self, root):
        # Regex entries and validation labels
        self.subtitle_regex_label = ttk.Label(root, text="Subtitle regex")
        self.subtitle_regex_var = tk.StringVar()
        self.subtitle_regex_var.set(r'\d+')
        self.subtitle_regex_entry = ttk.Entry(root, textvariable=self.subtitle_regex_var, width=20)
        self.subtitle_regex_validation_label = ttk.Label(root, text="")
        self._engrid(4, 0, self.subtitle_regex_label)
        self._engrid(5, 0, self.subtitle_regex_entry)
        self._engrid(6, 0, self.subtitle_regex_validation_label)

        self.episode_regex_label = ttk.Label(root, text="Episode regex")
        self.episode_regex_var = tk.StringVar()
        self.episode_regex_var.set(r'\d+')
        self.episode_regex_entry = ttk.Entry(root, textvariable=self.episode_regex_var, width=20)
        self.episode_regex_validation_label = ttk.Label(root, text="")
        self._engrid(4, 1, self.episode_regex_label)
        self._engrid(5, 1, self.episode_regex_entry)
        self._engrid(6, 1, self.episode_regex_validation_label)

        # Set up tracing
        self.subtitle_regex_var.trace_add("write", lambda *args: self.validate_regex(self.subtitle_regex_var, self.subtitle_regex_validation_label))
        self.episode_regex_var.trace_add("write", lambda *args: self.validate_regex(self.episode_regex_var, self.episode_regex_validation_label))

    def _init_preview_area(self, root):
        # Preview area
        self.original_names_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=40, height=10)
        self.original_names_area.grid(row=7, column=0, sticky='nsew', padx=5, pady=5)

        self.new_names_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=40, height=10)
        self.new_names_area.grid(row=7, column=1, sticky='nsew', padx=5, pady=5)
        
        #self.original_names_area.configure(yscrollcommand=self.sync_scroll)
        #self.new_names_area.configure(yscrollcommand=self.sync_scroll)
        
        self.original_names_area.configure(yscrollcommand=lambda *args: self.sync_scroll('original', *args))
        self.new_names_area.configure(yscrollcommand=lambda *args: self.sync_scroll('new', *args))

        # Buttons for preview and execute
        self.preview_button = ttk.Button(root, text="Preview Renames", command=self.preview_renames)
        self.preview_button.grid(row=8, column=1, sticky='w', padx=5, pady=5)
        self.execute_button = ttk.Button(root, text="Execute Renames", command=self.execute_renames)
        self.execute_button.grid(row=8, column=1, sticky='e', padx=5, pady=5)
        
    def sync_scroll(self, *args):
        print("sync_scroll called")
        print(f"caller: {args[0]}")
        print("other args:")
        pprint.pprint(args[1:])
        
        caller = args[0]

        if caller == 'new':
            self.original_names_area.yview_moveto(args[1])
        elif caller == 'original':
            self.new_names_area.yview_moveto(args[1])
        
    def select_subtitle_dir(self):
        self.subtitle_dir = filedialog.askdirectory()
        self.subtitle_dir_label.config(text=self.subtitle_dir)
        print(f"select subtitle dir: {self.subtitle_dir}")

    def select_episode_dir(self):
        self.episode_dir = filedialog.askdirectory()
        self.episode_dir_label.config(text=self.episode_dir)
        print(f"select episode dir: {self.episode_dir}")
        
    
    def match_files(self):
        subtitle_ext = self.subtitle_ext_entry.get().strip()
        episode_ext = self.episode_ext_entry.get().strip()
        subtitle_regex = self.subtitle_regex_entry.get().strip()
        episode_regex = self.episode_regex_entry.get().strip()

        # Fetch subtitle files
        subtitle_files = [f for f in Path(self.subtitle_dir).glob(f'*.{subtitle_ext}')]

        # Fetch episode files
        episode_files = [f for f in Path(self.episode_dir).glob(f'*.{episode_ext}')]

        # Mapping of episode identifier to filename
        episode_map = {}
        for ep in episode_files:
            match = re.search(episode_regex, ep.name)
            if match:
                episode_number = match.group()
                episode_number = episode_number.lstrip('0')
                episode_map[episode_number] = ep.stem
        print("episode map:")
        pprint.pprint(episode_map)
        # Match subtitles to episodes
        matched_files = []
        for sub in subtitle_files:
            match = re.search(subtitle_regex, sub.name)
            # we don't want to match if a regex is missing
            if match and match.group() in episode_map and episode_regex and subtitle_regex:
                new_name = episode_map[match.group()] + sub.suffix
                matched_files.append((sub.name, new_name))
            else:
                matched_files.append((sub.name, None))

        return matched_files
        
    
    def _convert_to_raw_string(self, pattern):
        # Runs eval with user input :^)    
        # (this saves you from having to escape backslashes, e.g. '\\d' -> '\d', etc.)
        try:
            # Convert to a raw string using eval
            return eval("r'" + pattern.replace("'", "\\'") + "'")
        except Exception as e:
            print("Error in regex pattern:", e)
            return None
    
    def preview_renames(self):
        self.original_names_area.delete(1.0, tk.END)
        self.new_names_area.delete(1.0, tk.END)
        matched_files = self.match_files()

        # Generate preview
        for original, new_name in matched_files:
            print(f'{original} --> {new_name}')
            if new_name:
                self.original_names_area.insert(tk.END, f'{original}\n')
                self.new_names_area.insert(tk.END, f'{new_name}\n')
            else:
                # no match
                self.original_names_area.insert(tk.END, f'{original}\n')
                self.new_names_area.insert(tk.END, 'NO MATCH\n')
            #if new_name:
            #    self.preview_area.insert(tk.END, f'{original.name} --> {new_name}\n')
            #else:
            #    self.preview_area.insert(tk.END, f'{original.name} --> No Match Found\n')


    def validate_regex(self, var, label):
        pattern = var.get().strip()
        if self.is_valid_regex(pattern):
            label.config(text="\u2713")  # Unicode checkmark
        else:
            label.config(text="")

    @staticmethod
    def is_valid_regex(pattern):
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
        

    def execute_renames(self):
        # Add logic to execute renames
        pass


def main():
    # Create the main application window
    root = tk.Tk()
    app = ResubtitlerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()