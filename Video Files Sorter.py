import os, sys, shutil, subprocess, threading
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import tkinter.font as tkfont
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except Exception:
    HAS_DND = False
    TkinterDnD = None  # type: ignore
    DND_FILES = None  # type: ignore

# --------- Config ---------
video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm'}
resolution_map = {
    'LOQ':  lambda h: h is not None and h < 720,
    'HD':   lambda h: h is not None and 720 <= h < 1080,
    'FHD':  lambda h: h is not None and 1080 <= h < 1440,
    'QHD':  lambda h: h is not None and 1440 <= h < 2160,
    '4K':  lambda h: h is not None and 2160 <= h
}

def resource_path(rel_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, rel_path)

ffprobe_path = resource_path("ffprobe_bin/ffprobe.exe")

# --------- Core Logic ---------
def get_frame_height(file_path):
    cmd = [
        ffprobe_path, '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=height',
        '-of', 'csv=p=0',
        '-i', file_path
    ]
    try:
        height = subprocess.check_output(
            cmd,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode().strip()
        return int(height.split(',')[0].strip())
    except Exception as e:
        print(f"ffprobe error for {file_path}: {e}")
        return None

def classify(height):
    for label, test in resolution_map.items():
        if test(height): return label
    return None

def sort_videos_in_folder(folder, progress_callback=None):
    video_files = []
    for root, _, files in os.walk(folder):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in video_extensions:
                video_files.append(os.path.join(root, name))

    total = len(video_files)
    moved = 0

    for i, full_path in enumerate(video_files):
        height = get_frame_height(full_path)
        category = classify(height)
        if category:
            dest = os.path.join(folder, category)
            os.makedirs(dest, exist_ok=True)
            try:
                shutil.move(full_path, os.path.join(dest, os.path.basename(full_path)))
                moved += 1
            except Exception:
                pass
        if progress_callback:
            progress_callback(i + 1, total)

    return moved

# --------- GUI ---------
TkBase = TkinterDnD.Tk if HAS_DND else tk.Tk

class DropSimApp(TkBase):
    def __init__(self):
        super().__init__()
        self.title("Video Sorter")
        self.geometry("420x260")
        self.minsize(420, 260)
        self.resizable(True, False)
        self.center_window()

        # State
        self.selected_folder = ""
        self._is_running = False
        self.theme_var = tk.StringVar(value="dark")

        # Fonts
        self.fonts = {
            "heading": tkfont.Font(family="Segoe UI", size=12, weight="bold"),
            "regular": tkfont.Font(family="Segoe UI", size=10),
            "small": tkfont.Font(family="Segoe UI", size=8),
        }

        # Theme setup (default to dark)
        self.style = ttk.Style()
        try:
            # Use a customizable theme for color overrides
            if "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            pass
        self._init_palettes()
        self.apply_theme(self.theme_var.get())

        # Menu
        menubar = tk.Menu(self)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_radiobutton(label="Light", value="light", variable=self.theme_var, command=self._on_theme_change)
        view_menu.add_radiobutton(label="Dark", value="dark", variable=self.theme_var, command=self._on_theme_change)
        menubar.add_cascade(label="View", menu=view_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

        # Header
        header_text = "Drop a folder or click to browse" if HAS_DND else "Click to browse (Drag & Drop unavailable)"
        self.header_label = tk.Label(self, text=header_text, font=self.fonts["heading"])
        self.header_label.pack(pady=(10, 6))

        # Drop area
        self.drop_area = tk.Label(
            self,
            text="⬇ Drop Folder Here or Click ⬇",
            bg=self.colors["surface"],
            width=46,
            height=5,
            relief="ridge",
            font=self.fonts["regular"],
            fg=self.colors["text"]
        )
        self.drop_area.pack(pady=(4, 8), padx=12, fill="x")

        if HAS_DND:
            self.drop_area.drop_target_register(DND_FILES)
            self.drop_area.dnd_bind('<<Drop>>', self.handle_drop)
            self.drop_area.dnd_bind('<<DragEnter>>', self.on_drag_enter)
            self.drop_area.dnd_bind('<<DragLeave>>', self.on_drag_leave)
        self.drop_area.bind("<Button-1>", self.handle_click)

        # Legend
        self.legend_label = tk.Label(self, text=">=720p→HD | >=1080p→FHD | >=1440p→QHD | >=2160p→4K | <720p→LOQ", font=self.fonts["small"])
        self.legend_label.pack()

        # Folder row
        folder_row = ttk.Frame(self)
        folder_row.pack(fill="x", padx=12)
        ttk.Label(folder_row, text="Folder:").pack(side="left")
        self.folder_var = tk.StringVar(value="(none)")
        self.folder_label = ttk.Label(folder_row, textvariable=self.folder_var, width=46)
        self.folder_label.pack(side="left", padx=(6, 6))
        ttk.Button(folder_row, text="Browse…", command=lambda: self.handle_click(None)).pack(side="right")

        # Progress
        self.progress = ttk.Progressbar(self, length=380, mode='determinate')
        self.progress.pack(pady=(10, 2), padx=12, fill="x")
        self.progress_text = ttk.Label(self, text="Idle")
        self.progress_text.pack(pady=(0, 6))

        # Actions row
        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=12)
        self.open_btn = ttk.Button(actions, text="Open in Explorer", command=self.open_in_explorer, state="disabled")
        self.open_btn.pack(side="left")
        ttk.Label(actions, text=" ").pack(side="left", expand=True)  # spacer
        self.start_btn = ttk.Button(actions, text="Start", command=self.start_sort)
        self.start_btn.pack(side="right")

        # Footer
        self.footer_label = tk.Label(
            self,
            text="Concept and design by amol.more@hotmail.com • Built with help from Microsoft Copilot",
            font=self.fonts["small"]
        )
        self.footer_label.pack(pady=(6, 6))

        # Check ffprobe availability
        if not os.path.isfile(ffprobe_path):
            messagebox.showwarning(
                "ffprobe not found",
                "ffprobe.exe was not found in 'ffprobe_bin'.\nSome files may not be readable."
            )

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def handle_click(self, event):
        folder = filedialog.askdirectory(title="Select Folder to Sort")
        if folder:
            self.set_selected_folder(folder)

    def handle_drop(self, event):
        folder = event.data.strip('{}')
        if os.path.isdir(folder):
            self.set_selected_folder(folder)
        else:
            messagebox.showwarning("Invalid Drop", "Please drop a valid folder.")

    def on_drag_enter(self, _event):
        if HAS_DND and not self._is_running:
            self.drop_area.configure(bg=self.colors["hover"])

    def on_drag_leave(self, _event):
        if HAS_DND and not self._is_running:
            self.drop_area.configure(bg=self.colors["surface"])

    def set_selected_folder(self, folder):
        self.selected_folder = folder
        self.folder_var.set(folder)
        self.open_btn.configure(state="normal")
        # Allow immediate start from click on drop_area as before
        self.start_sort()

    def open_in_explorer(self):
        if self.selected_folder and os.path.isdir(self.selected_folder):
            try:
                os.startfile(self.selected_folder)
            except Exception:
                pass

    def start_sort(self):
        if self._is_running:
            return
        folder = self.selected_folder or None
        if not folder or not os.path.isdir(folder):
            # If no folder yet, mimic previous behavior: click drop area opens dialog
            self.handle_click(None)
            return
        self.process_folder(folder)

    def process_folder(self, folder):
        # UI state
        self._is_running = True
        self.start_btn.configure(state="disabled")
        self.open_btn.configure(state="disabled")
        self.drop_area.configure(cursor="watch")
        self.progress["value"] = 0
        self.progress_text.configure(text="Scanning…")

        def update_progress(current, total):
            # Called from worker thread -> marshal to UI thread
            def _apply():
                if total > 0:
                    if self.progress["maximum"] != total:
                        self.progress["maximum"] = total
                    self.progress["value"] = current
                    pct = int((current / total) * 100)
                    self.progress_text.configure(text=f"Processing {current}/{total} ({pct}%)…")
                else:
                    self.progress["maximum"] = 1
                    self.progress["value"] = 0
                    self.progress_text.configure(text="No videos found")
            self.after(0, _apply)

        def worker():
            try:
                count = sort_videos_in_folder(folder, progress_callback=update_progress)
            except Exception as e:
                def _err():
                    messagebox.showerror("Error", f"An error occurred while sorting:\n{e}")
                self.after(0, _err)
                count = 0
            finally:
                def _done():
                    self._is_running = False
                    self.start_btn.configure(state="normal")
                    self.open_btn.configure(state="normal")
                    self.drop_area.configure(cursor="")
                    if self.progress["maximum"] == 100:
                        # In case old style percent was left
                        self.progress["value"] = 100
                    self.progress_text.configure(text="Done")
                    messagebox.showinfo("Sort Complete", f"Moved {count} video(s) into resolution folders.")
                self.after(0, _done)

        threading.Thread(target=worker, daemon=True).start()

    def show_about(self):
        messagebox.showinfo(
            "About Video Sorter",
            "Video Sorter\n\nSorts videos into folders by resolution (LOQ/HD/FHD/QHD/4K).\n\nDrop a folder, browse to select, then Start."
        )

    # --- Theming ---
    def _init_palettes(self):
        self.palettes = {
            "dark": {
                "bg": "#1e1e1e",
                "surface": "#2d2d2d",
                "border": "#3a3a3a",
                "text": "#e6e6e6",
                "muted": "#b0b0b0",
                "accent": "#0a84ff",
                "hover": "#314961",
            },
            "light": {
                "bg": "#f4f4f4",
                "surface": "#ededed",
                "border": "#d0d0d0",
                "text": "#202020",
                "muted": "#666666",
                "accent": "#0078d4",
                "hover": "#dbeafe",
            },
        }

    def _on_theme_change(self):
        self.apply_theme(self.theme_var.get())

    def apply_theme(self, mode: str):
        self.colors = self.palettes.get(mode, self.palettes["dark"])
        bg = self.colors["bg"]
        text = self.colors["text"]

        # Window background
        try:
            self.configure(bg=bg)
        except Exception:
            pass

        # ttk global styles
        try:
            self.style.configure("TFrame", background=bg)
            self.style.configure("TLabel", background=bg, foreground=text, font=self.fonts["regular"])
            self.style.configure("TButton", font=self.fonts["regular"])
            self.style.map("TButton",
                           foreground=[("disabled", self.colors["muted"])],
                           background=[])
            # Progressbar
            self.style.configure(
                "Horizontal.TProgressbar",
                troughcolor=self.colors["surface"],
                background=self.colors["accent"],
                lightcolor=self.colors["accent"],
                darkcolor=self.colors["accent"],
                bordercolor=self.colors["border"],
            )
        except Exception:
            pass

        # Tk labels and custom areas
        for lbl in (getattr(self, "header_label", None),
                    getattr(self, "legend_label", None),
                    getattr(self, "footer_label", None)):
            if lbl is not None:
                try:
                    lbl.configure(bg=bg, fg=text)
                except Exception:
                    pass

        if getattr(self, "drop_area", None) is not None:
            try:
                self.drop_area.configure(bg=self.colors["surface"], fg=text)
            except Exception:
                pass

# --------- Entry Point ---------
if __name__ == "__main__":
    DropSimApp().mainloop()
