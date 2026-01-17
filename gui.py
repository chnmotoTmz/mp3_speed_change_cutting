import customtkinter as ctk
from tkinter import filedialog
import threading
import os
from mp3_processor import process_audio

# Set appearance and color theme
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MP3 Processor")
        self.geometry("700x750")

        self.file_paths = []

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Input Sources Frame ---
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        # Folder selection
        self.folder_path = ctk.StringVar()
        folder_entry = ctk.CTkEntry(input_frame, textvariable=self.folder_path, placeholder_text="Select a folder to process...")
        folder_entry.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        browse_folder_btn = ctk.CTkButton(input_frame, text="Browse Folder", command=self.browse_folder, width=120)
        browse_folder_btn.grid(row=0, column=1, padx=(0, 20), pady=(10, 5))

        # Individual file selection
        add_files_btn = ctk.CTkButton(input_frame, text="Add MP3 Files", command=self.browse_files)
        add_files_btn.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

        self.scrollable_file_list = ctk.CTkScrollableFrame(self, label_text="Files to Process")
        self.scrollable_file_list.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)


        # --- Processing Settings Frame ---
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        speed_label = ctk.CTkLabel(settings_frame, text="Speed Factor:")
        speed_label.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
        self.speed_factor = ctk.StringVar(value="1.5")
        speed_entry = ctk.CTkEntry(settings_frame, textvariable=self.speed_factor, width=120)
        speed_entry.grid(row=0, column=1, padx=(0, 20), pady=10, sticky="w")

        segment_label = ctk.CTkLabel(settings_frame, text="Segment Length (mins):")
        segment_label.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="w")
        self.segment_length = ctk.StringVar(value="15")
        segment_entry = ctk.CTkEntry(settings_frame, textvariable=self.segment_length, width=120)
        segment_entry.grid(row=1, column=1, padx=(0, 20), pady=10, sticky="w")

        # --- Execution Frame ---
        execution_frame = ctk.CTkFrame(self)
        execution_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        execution_frame.grid_columnconfigure(0, weight=1)

        self.start_button = ctk.CTkButton(execution_frame, text="Start Processing", command=self.start_processing)
        self.start_button.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        # --- Log Display ---
        self.log_area = ctk.CTkTextbox(self, wrap=ctk.WORD, height=150)
        self.log_area.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.log_area.configure(state="disabled")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.log(f"Folder selected: {folder}")
            self.update_file_list_from_folder(folder)

    def browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select MP3 files",
            filetypes=(("MP3 files", "*.mp3"), ("All files", "*.*"))
        )
        if files:
            self.log(f"Adding {len(files)} file(s)...")
            for file in files:
                if file not in self.file_paths:
                    self.file_paths.append(file)
            self.update_ui_file_list()

    def update_file_list_from_folder(self, folder):
        self.log("Scanning folder for MP3 files...")
        folder_files = []
        if folder and os.path.isdir(folder):
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith('.mp3'):
                        full_path = os.path.join(root, file)
                        if full_path not in self.file_paths:
                             folder_files.append(full_path)
        if folder_files:
            self.file_paths.extend(folder_files)
            self.update_ui_file_list()

    def remove_file(self, file_path_to_remove):
        self.file_paths.remove(file_path_to_remove)
        self.update_ui_file_list()
        self.log(f"Removed: {os.path.basename(file_path_to_remove)}")

    def update_ui_file_list(self):
        # Clear existing widgets in the scrollable frame
        for widget in self.scrollable_file_list.winfo_children():
            widget.destroy()

        # Add a frame for each file
        for i, file_path in enumerate(self.file_paths):
            file_frame = ctk.CTkFrame(self.scrollable_file_list)
            file_frame.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            file_frame.grid_columnconfigure(0, weight=1)

            file_label = ctk.CTkLabel(file_frame, text=os.path.basename(file_path), anchor="w")
            file_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

            remove_btn = ctk.CTkButton(
                file_frame, text="X", command=lambda p=file_path: self.remove_file(p),
                width=30, height=30, fg_color="transparent", text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30")
            )
            remove_btn.grid(row=0, column=1, padx=5, pady=2)

    def start_processing(self):
        speed = float(self.speed_factor.get())
        segment_mins = int(self.segment_length.get())
        
        # We use self.file_paths directly now
        if not self.file_paths:
            self.log("No MP3 files selected to process.")
            return

        self.log(f"Found {len(self.file_paths)} MP3 file(s) to process.")
        self.log("Starting processing...")
        self.start_button.configure(state="disabled")
        
        thread = threading.Thread(target=self.process_in_background, args=(list(self.file_paths), speed, segment_mins))
        thread.start()

    def process_in_background(self, files_to_process, speed, segment_mins):
        try:
            output_base_dir = os.path.dirname(files_to_process[0]) if files_to_process else '.'
            
            # Redirect stdout to the log method
            import sys
            original_stdout = sys.stdout
            sys.stdout = self

            process_audio(files_to_process, speed, segment_mins, output_base_dir)
            self.log("\nProcessing complete!")

        except Exception as e:
            self.log(f"\nAn error occurred: {e}")
        finally:
            # Restore stdout and re-enable the button
            sys.stdout = original_stdout
            self.start_button.configure(state="normal")

    def write(self, text):
        """Redirects print statements to the log area."""
        self.log(text, end="")
    
    def flush(self):
        """Required for stdout redirection."""
        pass

    def log(self, message, end="\n"):
        """Logs a message to the text area."""
        self.log_area.configure(state="normal")
        self.log_area.insert(ctk.END, message + end)
        self.log_area.see(ctk.END)
        self.log_area.configure(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()

