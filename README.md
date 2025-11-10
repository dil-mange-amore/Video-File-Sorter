# Video Sorter

"Sort smarter, not harder"
---

### 📼 Video Sorter – Effortless Resolution-Based Organization

**What it does:**
Video Sorter is a desktop application that instantly scans all video files within a selected folder and automatically sorts them into subfolders based on their resolution: LOQ, HD, FHD, QHD, and 4K.

**How it works:**
This tool uses `ffprobe` (included) to detect each video's vertical resolution and then moves the file into the appropriate category folder. It features a user-friendly graphical interface built with Python's Tkinter library. The process is self-contained, and the application provides real-time progress updates.

**Resolution Categories:**
- **LOQ:** < 720p
- **HD:** >= 720p
- **FHD:** >= 1080p
- **QHD:** >= 1440p
- **4K:** >= 2160p

**Features:**
- 🖱️ **Drag-and-Drop:** Simple drag-and-drop a folder to start sorting.
- 📂 **Browse Manually:** Option to browse and select a folder.
- 📊 **Live Progress:** A real-time progress bar shows the status of the sorting process.
- 🎨 **Theming:** Switch between Light and Dark themes.
- 🔒 **Self-Contained:** Comes bundled with `ffprobe`, so no external downloads are needed for video analysis.
- 🖥️ **Cross-Platform:** Built with Python, making it usable on different operating systems.

### Requirements
- Python 3.x
- Dependencies listed in `requirements.txt`.

### How to Run
1.  **Install Dependencies:**
    Open a terminal or command prompt and run:
    ```
    pip install -r requirements.txt
    ```
2.  **Run the Application:**
    Execute the script from your terminal:
    ```
    python "Video Files Sorter.py"
    ```
3.  **Use the Sorter:**
    - Drag and drop a folder onto the application window.
    - Or, click the "Browse..." button to select a folder.
    - The sorting process will begin automatically.

---
*Concept and design by amol.more@hotmail.com • Built with help from Microsoft Copilot*