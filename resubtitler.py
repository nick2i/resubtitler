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
# TODO: what happens if you invert rename and have more media than subtitles? more subtitles than media? 
# TODO: go through and cut unused mappings and parameters, I made a bit of a mess working on invert

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
        button_frame = tk.Frame(root)
        self.execute_button = ttk.Button(button_frame, text="Execute Renames", command=self.execute_renames)
        self.execute_button.pack(side="right", anchor="e", pady=5)
        self.preview_button = ttk.Button(button_frame, text="Preview Renames", command=self.preview_renames)
        self.preview_button.pack(side="right", anchor="e", pady=5)
        
        self.is_invert_rename_var = tk.IntVar()
        self.invert_checkbox = ttk.Checkbutton(button_frame, text="Invert rename", variable=self.is_invert_rename_var, command=self._invert_checkbox_pressed)
        self.invert_checkbox.pack(side="right", anchor="e", pady=5)
        button_frame.grid(row=8, column=1)
        self.button_frame = button_frame
    
    def _invert_checkbox_pressed(self):
        # TODO change the labels of the two preview areas
        # TODO (this only makes sense if we add labels to the two preview areas)
        ...
        #print("invert renames")
    
    def is_inverting_rename(self):
        return self.is_invert_rename_var.get() == 1
        
    def sync_scroll(self, *args):
        caller = args[0]

        if caller == 'new':
            self.original_names_area.yview_moveto(args[1])
        elif caller == 'original':
            self.new_names_area.yview_moveto(args[1])
        
    def select_subtitle_dir(self):
        self.subtitle_dir = filedialog.askdirectory()
        # TODO: abbreviate the path so it doesn't stretch the display
        self.subtitle_dir_label.config(text=self.subtitle_dir)
        print(f"select subtitle dir: {self.subtitle_dir}")

    def select_episode_dir(self):
        self.episode_dir = filedialog.askdirectory()
        # TODO: abbreviate the path so it doesn't stretch the display
        self.episode_dir_label.config(text=self.episode_dir)
        print(f"select episode dir: {self.episode_dir}")
        
    
    def match_files(self):
        """
        Returns a list of tuples, structured like:
        
        [
          (
            pathlib.Path object representing the original subtitle path,
            string representing the renamed target subtitle path (nullable),
            string representing the original episode number, possibly 0-padded
          ), 
          . . .
        ]
        """
        subtitle_ext = self.subtitle_ext_entry.get().strip()
        episode_ext = self.episode_ext_entry.get().strip()
        subtitle_regex = self.subtitle_regex_entry.get().strip()
        episode_regex = self.episode_regex_entry.get().strip()

        # Fetch subtitle files
        subtitle_files = [f for f in Path(self.subtitle_dir).glob(f'*.{subtitle_ext}')]

        # Fetch episode files
        episode_files = [f for f in Path(self.episode_dir).glob(f'*.{episode_ext}')]

        # Mapping of episode number to filepath
        self.episode_map = {}
        # Mapping of episode number to (possibly zero-padded) episode number
        self.episode_map_number_raw = {}
        for ep in episode_files:
            # user input -> episode_regex, ep.name is the episode filename
            match = re.search(episode_regex, ep.name)
            if match:
                episode_number_raw = match.group()
                episode_number = episode_number_raw.lstrip('0')
                # TODO have to store a bit more info here to replicate 0-padded numbering schemes, dangit
                self.episode_map[episode_number] = ep
                self.episode_map_number_raw[episode_number] = episode_number_raw
                
        print("episode map:")
        pprint.pprint(self.episode_map)
        
        # Match subtitles to episodes
        matched_files = []
        # Mapping of subtitle filename to episode number
        self.subtitles_to_episode_numbers = {}
        for sub in subtitle_files:
            # user input -> subtitle_regex, sub.name is the subtitle filename
            match = re.search(subtitle_regex, sub.name)
            # we don't want to match if a regex is missing
            if not match:
                matched_files.append((sub.name, None, None))
            else:
                subtitle_number_raw = match.group()
                subtitle_number = subtitle_number_raw.lstrip('0')
                if subtitle_number in self.episode_map and episode_regex and subtitle_regex:
                    episode = self.episode_map[subtitle_number]
                    if self.is_inverting_rename():
                        # The media file will take the subtitle filename pattern
                        new_name = sub.stem + f".{episode_ext}"
                        matched_files.append((ep.name, new_name, subtitle_number))
                        #episode_name = self.episode_map.get(subtitle_episode_number, 'NO MATCH')
                    else:
                        # The subtitle file will take the media filename pattern
                        new_name = episode.stem + f".{subtitle_ext}"
                        matched_files.append((sub.name, new_name, subtitle_number))
            self.subtitles_to_episode_numbers[sub.name] = subtitle_episode_number

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

    def _sort_scrolled_text(self):
        ...

    def _insert_names(self, original, new_name, number):
        self.original_names_area.insert(tk.END, f'{original}\n')
        self.new_names_area.insert(tk.END, f'{new_name}\n')
    
    def preview_renames(self):
        self.original_names_area.delete(1.0, tk.END)
        self.new_names_area.delete(1.0, tk.END)
        matched_files = self.match_files()

        # TODO checkbox - invert name change (subtitle -> episode, rather than episode -> subtitle)
        # Generate preview
        for original, new_name, episode_number in matched_files:
            print(f'{original} --> {new_name}')
            if new_name:
                self._insert_names(original, new_name, episode_number)
            else:
                self._insert_names(original, 'NO MATCH', episode_number)

        def _sort_func(x):
            tmp = int(self.subtitles_to_episode_numbers[x])
            #print(tmp)
            return tmp
        
        print("\n\nSUBTITLES TO EPISODE NUMBERS:\n")
        pprint.pprint(self.subtitles_to_episode_numbers)
        # sort original_names_area
        original_names_content = self.original_names_area.get("1.0", tk.END)
        lines = original_names_content.splitlines()
        lines.sort(key=_sort_func)
        self.original_names_area.delete("1.0", tk.END)
        self.original_names_area.insert("1.0", "\n".join(lines))
        # sort new_names_area
        new_names_content = self.new_names_area.get("1.0", tk.END)
        lines = new_names_content.splitlines()
        lines.sort(key=_sort_func)
        self.new_names_area.delete("1.0", tk.END)
        self.new_names_area.insert("1.0", "\n".join(lines))

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