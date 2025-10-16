import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import pyautogui
import keyboard
import sys
import ctypes
from ctypes import wintypes
import json
import os
import random
import urllib.request
import urllib.error
import subprocess
import tempfile
import shutil

# GitHub repository
GITHUB_REPO = "Cobryn3000/autoclicker"

def get_config_dir():
    """Get the appropriate config directory for the platform"""
    if sys.platform == 'win32':
        # Use AppData/Local for Windows
        config_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'AutoClicker')
    else:
        # Fallback for other platforms
        config_dir = os.path.join(os.path.expanduser('~'), '.autoclicker')
    
    # Create directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_path(filename='config.json'):
    """Get the full path to a config file"""
    return os.path.join(get_config_dir(), filename)

def get_local_version():
    """Get the local version from version.txt in AppData"""
    version_file = get_config_path('version.txt')
    try:
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                return f.read().strip()
        else:
            # Create default version file if it doesn't exist
            default_version = "1.0.0"
            with open(version_file, 'w') as f:
                f.write(default_version)
            return default_version
    except Exception as e:
        print(f"Error reading local version: {e}")
        return "1.0.0"

def set_local_version(version):
    """Save the local version to version.txt in AppData"""
    version_file = get_config_path('version.txt')
    try:
        with open(version_file, 'w') as f:
            f.write(version)
    except Exception as e:
        print(f"Error saving local version: {e}")

class AutoClicker:
    def __init__(self):
        self.clicking = False
        self.click_thread = None
        self.hotkey_thread = None
        self.waiting_for_key = False
        self.picking_location = False
        
        # Get version from file
        self.version = get_local_version()
        
        # Clean up update files on startup
        self.cleanup_update_files()
        
        # Check and perform first launch setup
        self.check_first_launch()
        
        # Windows API constants
        self.MOUSEEVENTF_LEFTDOWN = 0x0002
        self.MOUSEEVENTF_LEFTUP = 0x0004
        self.MOUSEEVENTF_RIGHTDOWN = 0x0008
        self.MOUSEEVENTF_RIGHTUP = 0x0010
        self.MOUSEEVENTF_ABSOLUTE = 0x8000
        
        # Get Windows API functions
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # Disable pyautogui delays and failsafe for position getting
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = True
        
        # Config file path
        self.config_file = get_config_path('config.json')
        
        # Load settings
        self.load_settings()
        
        self.setup_ui()
        
        # Minimize window on startup if enabled
        if self.settings.get('minimize_on_start', False):
            self.root.after(0, self.root.iconify)
        
        self.setup_hotkey()
        
        # Check for updates in background
        self.check_for_updates_async()
    
    def cleanup_update_files(self):
        """Clean up leftover update files from previous update"""
        try:
            update_dir = get_config_dir()
            
            # Files to clean up
            cleanup_files = [
                os.path.join(update_dir, "autoclicker_update.exe"),
                os.path.join(update_dir, "update.bat")
            ]
            
            for file_path in cleanup_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"Cleaned up: {file_path}")
                    except Exception as e:
                        print(f"Could not remove {file_path}: {e}")
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def check_for_updates_async(self):
        """Check for updates in background thread"""
        def check_updates():
            try:
                time.sleep(2)  # Wait for UI to load
                latest_version = self.get_latest_version_from_file()
                download_url = self.get_exe_download_url()
                
                if latest_version and download_url and self.is_newer_version(latest_version):
                    self.root.after(0, lambda: self.prompt_update(latest_version, download_url))
            except Exception as e:
                print(f"Update check failed: {e}")
        
        threading.Thread(target=check_updates, daemon=True).start()
    
    def get_latest_version_from_file(self):
        """Get latest version from version.txt file in GitHub repo"""
        try:
            # Raw GitHub URL for the version file
            version_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.txt"
            
            req = urllib.request.Request(version_url)
            req.add_header('User-Agent', 'AutoClicker')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                version = response.read().decode().strip()
                # Remove 'v' prefix if present
                return version.lstrip('v')
        except Exception as e:
            print(f"Error reading version file: {e}")
            return None
    
    def get_exe_download_url(self):
        """Get download URL for AutoClicker.exe from GitHub repo"""
        try:
            # Direct link to the exe in the repo
            exe_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/AutoClicker.exe"
            
            # Verify the file exists
            req = urllib.request.Request(exe_url, method='HEAD')
            req.add_header('User-Agent', 'AutoClicker')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return exe_url
            
            return None
        except Exception as e:
            print(f"Error getting exe URL: {e}")
            return None
    
    def get_latest_version(self):
        """Get latest version from GitHub releases (fallback method)"""
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            
            req = urllib.request.Request(api_url)
            req.add_header('User-Agent', 'AutoClicker')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                version = data.get('tag_name', '').lstrip('v')
                
                # Find the AutoClicker.exe asset
                download_url = None
                for asset in data.get('assets', []):
                    if asset.get('name', '') == 'AutoClicker.exe':
                        download_url = asset.get('browser_download_url')
                        break
                
                return version, download_url
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return None, None
    
    def is_newer_version(self, latest_version):
        """Compare version strings"""
        try:
            current = [int(x) for x in self.version.split('.')]
            latest = [int(x) for x in latest_version.split('.')]
            
            return latest > current
        except:
            return False
    
    def prompt_update(self, latest_version, download_url):
        """Prompt user to update"""
        if not download_url:
            return
        
        response = messagebox.askyesno(
            "Update Available",
            f"A new version (v{latest_version}) is available!\n"
            f"Current version: v{self.version}\n\n"
            f"Would you like to download and install it now?",
            icon='info'
        )
        
        if response:
            self.download_and_update(download_url, latest_version)
    
    def download_and_update(self, download_url, new_version):
        """Download and install update"""
        def download():
            try:
                self.root.after(0, lambda: self.status_label.config(
                    text="Status: Downloading update...", foreground="blue"))
                
                # Download to a persistent location
                update_dir = get_config_dir()
                temp_file = os.path.join(update_dir, "autoclicker_update.exe")
                readme_file = os.path.join(update_dir, "README.md")
                
                # Download executable
                urllib.request.urlretrieve(download_url, temp_file)
                
                # Download README.md
                try:
                    readme_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/README.md"
                    urllib.request.urlretrieve(readme_url, readme_file)
                    print("README.md downloaded successfully")
                except Exception as e:
                    print(f"Could not download README.md: {e}")
                
                # Update local version file
                set_local_version(new_version)
                
                # Create batch script to replace exe
                if getattr(sys, 'frozen', False):
                    # Running as compiled exe
                    current_exe = sys.executable
                    batch_file = os.path.join(update_dir, "update.bat")
                    
                    with open(batch_file, 'w') as f:
                        f.write('@echo off\n')
                        f.write('echo Updating AutoClicker...\n')
                        f.write('timeout /t 3 /nobreak > nul\n')
                        f.write('\n')
                        f.write(':retry\n')
                        f.write(f'taskkill /F /IM "{os.path.basename(current_exe)}" >nul 2>&1\n')
                        f.write('timeout /t 2 /nobreak > nul\n')
                        f.write('\n')
                        f.write(f'if exist "{current_exe}" (\n')
                        f.write(f'  del /f /q "{current_exe}" >nul 2>&1\n')
                        f.write(f'  if exist "{current_exe}" (\n')
                        f.write('    timeout /t 1 /nobreak > nul\n')
                        f.write('    goto retry\n')
                        f.write('  )\n')
                        f.write(')\n')
                        f.write('\n')
                        f.write(f'if exist "{temp_file}" (\n')
                        f.write(f'  ren "{temp_file}" "{os.path.basename(current_exe)}"\n')
                        f.write('  if errorlevel 1 (\n')
                        f.write('    echo Update failed - could not rename file!\n')
                        f.write('    timeout /t 5\n')
                        f.write('    exit /b 1\n')
                        f.write('  )\n')
                        f.write(')\n')
                        f.write('\n')
                        f.write(f'if exist "{os.path.join(update_dir, os.path.basename(current_exe))}" (\n')
                        f.write(f'  move /y "{os.path.join(update_dir, os.path.basename(current_exe))}" "{current_exe}" >nul 2>&1\n')
                        f.write('  if errorlevel 1 (\n')
                        f.write('    echo Update failed - could not move file!\n')
                        f.write('    timeout /t 5\n')
                        f.write('    exit /b 1\n')
                        f.write('  )\n')
                        f.write(')\n')
                        f.write('\n')
                        f.write('timeout /t 1 /nobreak > nul\n')
                        f.write(f'if exist "{current_exe}" (\n')
                        f.write(f'  start "" "{current_exe}"\n')
                        f.write(') else (\n')
                        f.write('  echo Update failed - executable not found!\n')
                        f.write('  timeout /t 5\n')
                        f.write(')\n')
                    
                    # Run batch script silently
                    subprocess.Popen(['cmd', '/c', batch_file], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    # Force exit immediately without showing message
                    self.root.after(100, lambda: os._exit(0))
                else:
                    # Running as script - just notify
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Update", f"Update downloaded to:\n{temp_file}\n\n"
                        "Please replace your executable manually."))
                    self.root.after(0, lambda: self.status_label.config(
                        text="Status: Idle", foreground="black"))
            
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Update Error", f"Failed to download update:\n{str(e)}"))
                self.root.after(0, lambda: self.status_label.config(
                    text="Status: Idle", foreground="black"))
        
        threading.Thread(target=download, daemon=True).start()
    
    def check_first_launch(self):
        """Check if this is the first launch and perform setup"""
        config_file = get_config_path('config.json')
        
        # Load or create config
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    first_launch = config.get('first_launch', True)
            except:
                first_launch = True
        else:
            first_launch = True
        
        if first_launch and getattr(sys, 'frozen', False):
            # Only do first launch setup if running as compiled exe
            self.perform_first_launch_setup()
    
    def perform_first_launch_setup(self):
        """Perform first launch setup: move exe to AppData and create shortcut"""
        try:
            current_exe = sys.executable
            appdata_dir = get_config_dir()
            target_exe = os.path.join(appdata_dir, os.path.basename(current_exe))
            
            # Check if we're already in AppData
            if os.path.normpath(os.path.dirname(current_exe)) == os.path.normpath(appdata_dir):
                # Already in AppData, just create shortcut
                self.create_desktop_shortcut(current_exe)
                self.mark_first_launch_complete()
                return
            
            # Copy exe to AppData
            if not os.path.exists(target_exe):
                shutil.copy2(current_exe, target_exe)
                print(f"Copied executable to: {target_exe}")
            
            # Create desktop shortcut
            self.create_desktop_shortcut(target_exe)
            
            # Mark first launch as complete
            self.mark_first_launch_complete()
            
            # Show message and restart from new location
            messagebox.showinfo(
                "Setup Complete",
                f"AutoClicker has been installed to:\n{appdata_dir}\n\n"
                "A desktop shortcut has been created.\n"
                "The application will now restart from the new location."
            )
            
            # Start new instance from AppData
            subprocess.Popen([target_exe], creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Exit current instance
            os._exit(0)
            
        except Exception as e:
            print(f"First launch setup error: {e}")
            # Continue anyway, mark as complete to avoid retry
            self.mark_first_launch_complete()
    
    def create_desktop_shortcut(self, target_path):
        """Create a desktop shortcut to the executable"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "AutoClicker.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target_path
            shortcut.WorkingDirectory = os.path.dirname(target_path)
            shortcut.IconLocation = target_path
            shortcut.Description = "AutoClicker - Fast and precise mouse automation"
            shortcut.save()
            
            print(f"Desktop shortcut created: {shortcut_path}")
            
        except ImportError:
            # Fallback: Use PowerShell to create shortcut
            try:
                desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
                shortcut_path = os.path.join(desktop, "AutoClicker.lnk")
                
                ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target_path}"
$Shortcut.WorkingDirectory = "{os.path.dirname(target_path)}"
$Shortcut.Description = "AutoClicker - Fast and precise mouse automation"
$Shortcut.Save()
'''
                subprocess.run(['powershell', '-Command', ps_script], 
                             creationflags=subprocess.CREATE_NO_WINDOW,
                             capture_output=True)
                
                print(f"Desktop shortcut created: {shortcut_path}")
                
            except Exception as e:
                print(f"Could not create desktop shortcut: {e}")
    
    def mark_first_launch_complete(self):
        """Mark first launch as complete in config"""
        config_file = get_config_path('config.json')
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            config['first_launch'] = False
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"Could not mark first launch complete: {e}")
    
    def load_settings(self):
        """Load settings from config file"""
        default_settings = {
            'first_launch': True,
            'hours': 0,
            'minutes': 0,
            'seconds': 0,
            'milliseconds': 100,
            'random_offset': False,
            'random_offset_ms': 40,
            'mouse_button': 'Left',
            'click_type': 'Single',
            'repeat_mode': 'until_stopped',
            'repeat_times': 1,
            'cursor_position': 'current',
            'pick_x': 0,
            'pick_y': 0,
            'hotkey': 'f9',
            'prevent_mouse_movement': False,
            'minimize_on_start': False
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle missing keys
                    self.settings = {**default_settings, **loaded}
            else:
                self.settings = default_settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = default_settings
        
        self.current_hotkey = self.settings['hotkey']
    
    def save_settings(self):
        """Save current settings to config file"""
        try:
            settings = {
                'first_launch': False,
                'hours': int(self.hours_var.get() or 0),
                'minutes': int(self.minutes_var.get() or 0),
                'seconds': int(self.seconds_var.get() or 0),
                'milliseconds': int(self.ms_var.get() or 100),
                'random_offset': self.random_offset_var.get(),
                'random_offset_ms': int(self.random_offset_ms_var.get() or 40),
                'mouse_button': self.mouse_button_var.get(),
                'click_type': self.click_type_var.get(),
                'repeat_mode': self.repeat_mode_var.get(),
                'repeat_times': int(self.repeat_times_var.get() or 1),
                'cursor_position': self.cursor_position_var.get(),
                'pick_x': int(self.pick_x_var.get() or 0),
                'pick_y': int(self.pick_y_var.get() or 0),
                'hotkey': self.current_hotkey,
                'prevent_mouse_movement': self.prevent_mouse_movement_var.get(),
                'minimize_on_start': self.minimize_on_start_var.get()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
        
    def setup_ui(self):
        """Setup the GUI interface"""
        self.root = tk.Tk()
        self.root.title(f"AutoClicker v{self.version}")
        self.root.geometry("380x470")
        self.root.resizable(False, False)
        
        # Configure grid weights for proper sizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        main_frame = ttk.Frame(self.root, padding="12")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Bind click on main frame to remove focus from entries
        main_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        
        # Click interval section
        interval_frame = ttk.LabelFrame(main_frame, text="Click interval", padding="12")
        interval_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        interval_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        
        time_frame = ttk.Frame(interval_frame)
        time_frame.pack(fill=tk.X, pady=(0, 8))
        time_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        
        # Hours
        self.hours_var = tk.StringVar(value=str(self.settings['hours']))
        hours_entry = ttk.Entry(time_frame, textvariable=self.hours_var, width=6)
        hours_entry.pack(side=tk.LEFT, padx=(0, 2))
        self.add_placeholder(hours_entry, self.hours_var, "0")
        hours_label = ttk.Label(time_frame, text="hours")
        hours_label.pack(side=tk.LEFT, padx=(2, 8))
        hours_label.bind('<Button-1>', lambda e: self.root.focus_set())
        
        # Minutes
        self.minutes_var = tk.StringVar(value=str(self.settings['minutes']))
        minutes_entry = ttk.Entry(time_frame, textvariable=self.minutes_var, width=6)
        minutes_entry.pack(side=tk.LEFT, padx=(0, 2))
        self.add_placeholder(minutes_entry, self.minutes_var, "0")
        mins_label = ttk.Label(time_frame, text="mins")
        mins_label.pack(side=tk.LEFT, padx=(2, 8))
        mins_label.bind('<Button-1>', lambda e: self.root.focus_set())
        
        # Seconds
        self.seconds_var = tk.StringVar(value=str(self.settings['seconds']))
        seconds_entry = ttk.Entry(time_frame, textvariable=self.seconds_var, width=6)
        seconds_entry.pack(side=tk.LEFT, padx=(0, 2))
        self.add_placeholder(seconds_entry, self.seconds_var, "0")
        secs_label = ttk.Label(time_frame, text="secs")
        secs_label.pack(side=tk.LEFT, padx=(2, 8))
        secs_label.bind('<Button-1>', lambda e: self.root.focus_set())
        
        # Milliseconds
        self.ms_var = tk.StringVar(value=str(self.settings['milliseconds']))
        ms_entry = ttk.Entry(time_frame, textvariable=self.ms_var, width=6)
        ms_entry.pack(side=tk.LEFT, padx=(0, 2))
        self.add_placeholder(ms_entry, self.ms_var, "100")
        ms_label = ttk.Label(time_frame, text="ms")
        ms_label.pack(side=tk.LEFT, padx=2)
        ms_label.bind('<Button-1>', lambda e: self.root.focus_set())
        
        # Random offset
        random_frame = ttk.Frame(interval_frame)
        random_frame.pack(fill=tk.X)
        random_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        
        self.random_offset_var = tk.BooleanVar(value=self.settings['random_offset'])
        offset_check = ttk.Checkbutton(random_frame, text="Random offset ±", variable=self.random_offset_var)
        offset_check.pack(side=tk.LEFT)
        self.random_offset_ms_var = tk.StringVar(value=str(self.settings['random_offset_ms']))
        offset_entry = ttk.Entry(random_frame, textvariable=self.random_offset_ms_var, width=6)
        offset_entry.pack(side=tk.LEFT, padx=(5, 2))
        self.add_placeholder(offset_entry, self.random_offset_ms_var, "40")
        offset_label = ttk.Label(random_frame, text="ms")
        offset_label.pack(side=tk.LEFT, padx=2)
        offset_label.bind('<Button-1>', lambda e: self.root.focus_set())
        
        # Click options section
        options_frame = ttk.LabelFrame(main_frame, text="Click options", padding="12")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 4), pady=(0, 8))
        options_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        
        # Mouse button row
        mouse_row = ttk.Frame(options_frame)
        mouse_row.pack(anchor=tk.W, fill=tk.X, pady=(0, 8))
        mouse_row.bind('<Button-1>', lambda e: self.root.focus_set())
        mouse_label = ttk.Label(mouse_row, text="Mouse button:", width=13)
        mouse_label.pack(side=tk.LEFT, padx=(0, 4))
        mouse_label.bind('<Button-1>', lambda e: self.root.focus_set())
        self.mouse_button_var = tk.StringVar(value=self.settings['mouse_button'])
        mouse_combo = ttk.Combobox(mouse_row, textvariable=self.mouse_button_var, 
                                   values=["Left", "Right", "Middle"], state="readonly", width=10)
        mouse_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Click type row
        click_row = ttk.Frame(options_frame)
        click_row.pack(anchor=tk.W, fill=tk.X, pady=(0, 8))
        click_row.bind('<Button-1>', lambda e: self.root.focus_set())
        click_label = ttk.Label(click_row, text="Click type:", width=13)
        click_label.pack(side=tk.LEFT, padx=(0, 4))
        click_label.bind('<Button-1>', lambda e: self.root.focus_set())
        self.click_type_var = tk.StringVar(value=self.settings['click_type'])
        click_combo = ttk.Combobox(click_row, textvariable=self.click_type_var,
                                   values=["Single", "Double"], state="readonly", width=10)
        click_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # New checkboxes
        self.prevent_mouse_movement_var = tk.BooleanVar(value=self.settings['prevent_mouse_movement'])
        prevent_check = ttk.Checkbutton(options_frame, text="Prevent mouse movement", 
                                       variable=self.prevent_mouse_movement_var)
        prevent_check.pack(anchor=tk.W, pady=(0, 4))
        
        self.minimize_on_start_var = tk.BooleanVar(value=self.settings['minimize_on_start'])
        minimize_check = ttk.Checkbutton(options_frame, text="Minimize on start", 
                                        variable=self.minimize_on_start_var)
        minimize_check.pack(anchor=tk.W)
        
        # Click repeat section
        repeat_frame = ttk.LabelFrame(main_frame, text="Click repeat", padding="12")
        repeat_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(4, 0), pady=(0, 8))
        repeat_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        
        self.repeat_mode_var = tk.StringVar(value=self.settings['repeat_mode'])
        repeat_radio = ttk.Radiobutton(repeat_frame, text="Repeat", variable=self.repeat_mode_var, 
                       value="repeat")
        repeat_radio.pack(anchor=tk.W)
        
        times_frame = ttk.Frame(repeat_frame)
        times_frame.pack(anchor=tk.W, padx=(20, 0), pady=(4, 8))
        times_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        self.repeat_times_var = tk.StringVar(value=str(self.settings['repeat_times']))
        repeat_entry = ttk.Entry(times_frame, textvariable=self.repeat_times_var, width=8)
        repeat_entry.pack(side=tk.LEFT, padx=(0, 4))
        self.add_placeholder(repeat_entry, self.repeat_times_var, "1")
        times_label = ttk.Label(times_frame, text="times")
        times_label.pack(side=tk.LEFT)
        times_label.bind('<Button-1>', lambda e: self.root.focus_set())
        
        until_radio = ttk.Radiobutton(repeat_frame, text="Until stopped", 
                       variable=self.repeat_mode_var, value="until_stopped")
        until_radio.pack(anchor=tk.W)
        
        # Cursor position section
        cursor_frame = ttk.LabelFrame(main_frame, text="Cursor position", padding="12")
        cursor_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        cursor_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        
        self.cursor_position_var = tk.StringVar(value=self.settings['cursor_position'])
        current_radio = ttk.Radiobutton(cursor_frame, text="Current location", 
                       variable=self.cursor_position_var, value="current")
        current_radio.pack(anchor=tk.W, pady=(0, 4))
        
        pick_frame = ttk.Frame(cursor_frame)
        pick_frame.pack(anchor=tk.W, fill=tk.X)
        pick_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        
        pick_radio = ttk.Radiobutton(pick_frame, text="Pick location", 
                       variable=self.cursor_position_var, value="pick")
        pick_radio.pack(side=tk.LEFT)
        
        coord_frame = ttk.Frame(pick_frame)
        coord_frame.pack(side=tk.LEFT, padx=(12, 0))
        coord_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        x_label = ttk.Label(coord_frame, text="X:")
        x_label.pack(side=tk.LEFT, padx=(0, 2))
        x_label.bind('<Button-1>', lambda e: self.root.focus_set())
        self.pick_x_var = tk.StringVar(value=str(self.settings['pick_x']))
        x_entry = ttk.Entry(coord_frame, textvariable=self.pick_x_var, width=7)
        x_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.add_placeholder(x_entry, self.pick_x_var, "0")
        y_label = ttk.Label(coord_frame, text="Y:")
        y_label.pack(side=tk.LEFT, padx=(0, 2))
        y_label.bind('<Button-1>', lambda e: self.root.focus_set())
        self.pick_y_var = tk.StringVar(value=str(self.settings['pick_y']))
        y_entry = ttk.Entry(coord_frame, textvariable=self.pick_y_var, width=7)
        y_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.add_placeholder(y_entry, self.pick_y_var, "0")
        
        # Pick location button
        pick_button = ttk.Button(coord_frame, text="Select", command=self.start_location_picker, width=8)
        pick_button.pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 8))
        button_frame.bind('<Button-1>', lambda e: self.root.focus_set())
        
        self.start_button = ttk.Button(button_frame, text="Start", command=self.toggle_clicking, width=18)
        self.start_button.pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(button_frame, text="Stop", command=self.stop_clicking, width=18).pack(side=tk.LEFT)
        
        # Hotkey info
        self.hotkey_label = ttk.Label(main_frame, 
                                      text=f"Hotkey: {self.current_hotkey.upper()} (Click to change)",
                                      foreground="blue", cursor="hand2", font=("Arial", 9))
        self.hotkey_label.grid(row=4, column=0, columnspan=2, pady=(0, 4))
        self.hotkey_label.bind("<Button-1>", lambda e: self.change_hotkey())
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Status: Idle", font=("Arial", 9, "italic"))
        self.status_label.grid(row=5, column=0, columnspan=2)
        self.status_label.bind('<Button-1>', lambda e: self.root.focus_set())
        
        # Version label
        version_label = ttk.Label(main_frame, text=f"v{self.version}", 
                                 font=("Arial", 8), foreground="gray")
        version_label.grid(row=6, column=0, columnspan=2, pady=(4, 0))
        version_label.bind('<Button-1>', lambda e: self.check_for_updates_manual())
        
        # Bind save on changes
        for var in [self.hours_var, self.minutes_var, self.seconds_var, self.ms_var,
                   self.random_offset_ms_var, self.repeat_times_var, self.pick_x_var, self.pick_y_var]:
            var.trace_add('write', lambda *args: self.save_settings())
        
        for var in [self.random_offset_var, self.mouse_button_var, self.click_type_var,
                   self.repeat_mode_var, self.cursor_position_var, self.prevent_mouse_movement_var,
                   self.minimize_on_start_var]:
            var.trace_add('write', lambda *args: self.save_settings())
    
    def add_placeholder(self, entry, var, placeholder):
        """Add placeholder text to entry widget"""
        # Store original value
        original_value = var.get()
        
        # If empty or zero, show placeholder in gray
        if not original_value or original_value == "0":
            var.set(placeholder)
            entry.config(foreground='gray')
        
        def on_focus_in(event):
            if var.get() == placeholder:
                var.set('')
                entry.config(foreground='black')
        
        def on_focus_out(event):
            current = var.get().strip()
            if not current or current == "":
                var.set("0")
                entry.config(foreground='black')
            else:
                entry.config(foreground='black')
        
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        
    def setup_hotkey(self):
        """Setup the hotkey listener"""
        def hotkey_listener():
            try:
                keyboard.unhook_all()
                keyboard.add_hotkey(self.current_hotkey, self.toggle_clicking)
                keyboard.wait()
            except Exception as e:
                print(f"Hotkey error: {e}")
            
        if self.hotkey_thread and self.hotkey_thread.is_alive():
            keyboard.unhook_all()
            
        self.hotkey_thread = threading.Thread(target=hotkey_listener, daemon=True)
        self.hotkey_thread.start()
    
    def change_hotkey(self):
        """Change the hotkey binding"""
        if self.waiting_for_key or self.clicking:
            return
            
        self.waiting_for_key = True
        self.hotkey_label.config(text="Press any key...")
        
        # Temporarily unhook all hotkeys to avoid interference
        keyboard.unhook_all()
        
        def key_capture():
            try:
                # Wait a bit to ensure unhook is complete
                time.sleep(0.1)
                event = keyboard.read_event(suppress=True)
                if event.event_type == keyboard.KEY_DOWN:
                    new_key = event.name.lower()
                    # Ignore common modifier-only keys
                    if new_key not in ['shift', 'ctrl', 'alt', 'win', 'windows']:
                        self.current_hotkey = new_key
                        self.save_settings()
                    self.root.after(0, self.update_hotkey_ui)
                    self.root.after(200, self.setup_hotkey)
            except Exception as e:
                print(f"Key capture error: {e}")
                self.root.after(0, self.update_hotkey_ui)
                self.root.after(200, self.setup_hotkey)
        
        threading.Thread(target=key_capture, daemon=True).start()
    
    def update_hotkey_ui(self):
        """Update the UI after hotkey change"""
        self.waiting_for_key = False
        self.hotkey_label.config(text=f"Hotkey: {self.current_hotkey.upper()} (Click to change)")
    
    def start_location_picker(self):
        """Start the location picker mode"""
        if self.picking_location:
            return
        
        self.picking_location = True
        self.status_label.config(text="Status: Click anywhere to pick location", foreground="blue")
        
        def pick_location():
            try:
                # Wait for mouse click
                from pynput import mouse
                
                def on_click(x, y, button, pressed):
                    if pressed:
                        self.pick_x_var.set(str(int(x)))
                        self.pick_y_var.set(str(int(y)))
                        self.cursor_position_var.set("pick")
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"Status: Location set to ({int(x)}, {int(y)})", 
                            foreground="green"))
                        self.picking_location = False
                        return False  # Stop listener
                
                with mouse.Listener(on_click=on_click) as listener:
                    listener.join()
                    
            except ImportError:
                # Fallback if pynput is not available
                messagebox.showinfo("Pick Location", 
                    "Move your mouse to the desired location and press Enter")
                self.root.wait_variable(self.pick_x_var)
                x, y = pyautogui.position()
                self.pick_x_var.set(str(x))
                self.pick_y_var.set(str(y))
                self.cursor_position_var.set("pick")
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Status: Location set to ({x}, {y})", 
                    foreground="green"))
                self.picking_location = False
            except Exception as e:
                print(f"Location picker error: {e}")
                self.root.after(0, lambda: self.status_label.config(
                    text="Status: Idle", foreground="black"))
                self.picking_location = False
        
        threading.Thread(target=pick_location, daemon=True).start()
    
    def get_click_interval(self):
        """Calculate total click interval in seconds"""
        try:
            hours = int(self.hours_var.get() or 0)
            minutes = int(self.minutes_var.get() or 0)
            seconds = int(self.seconds_var.get() or 0)
            milliseconds = int(self.ms_var.get() or 100)
            
            total_ms = (hours * 3600000) + (minutes * 60000) + (seconds * 1000) + milliseconds
            
            if self.random_offset_var.get():
                offset = int(self.random_offset_ms_var.get() or 0)
                # Add random offset between -offset and +offset
                total_ms += random.randint(-offset, offset)
            
            return max(1, total_ms) / 1000.0  # Convert to seconds, minimum 1ms
        except ValueError:
            return 0.1  # Default 100ms
    
    def fast_click(self, x, y, button='left', double=False):
        """Perform a fast click using Windows API"""
        if button.lower() == 'left':
            down_flag = self.MOUSEEVENTF_LEFTDOWN
            up_flag = self.MOUSEEVENTF_LEFTUP
        elif button.lower() == 'right':
            down_flag = self.MOUSEEVENTF_RIGHTDOWN
            up_flag = self.MOUSEEVENTF_RIGHTUP
        else:  # middle
            down_flag = 0x0020  # MOUSEEVENTF_MIDDLEDOWN
            up_flag = 0x0040    # MOUSEEVENTF_MIDDLEUP
        
        # When prevent_mouse_movement is TRUE, we SHOULD move cursor
        # When prevent_mouse_movement is FALSE, we should NOT move cursor
        should_move_cursor = self.cursor_position_var.get() == "pick" or self.prevent_mouse_movement_var.get()
        
        if should_move_cursor:
            # Move cursor to target position (no checking needed, just move)
            self.user32.SetCursorPos(int(x), int(y))
        
        # Click at the position (current or moved)
        self.user32.mouse_event(down_flag, 0, 0, 0, 0)
        self.user32.mouse_event(up_flag, 0, 0, 0, 0)
        
        # Second click for double-click
        if double:
            self.user32.mouse_event(down_flag, 0, 0, 0, 0)
            self.user32.mouse_event(up_flag, 0, 0, 0, 0)
        
    def toggle_clicking(self):
        """Toggle the autoclicker on/off"""
        if self.clicking:
            self.stop_clicking()
        else:
            self.start_clicking()
    
    def start_clicking(self):
        """Start the autoclicker"""
        try:
            # Remove focus from any entry field
            self.root.focus_set()
            
            # Get click position based on mode
            if self.cursor_position_var.get() == "pick":
                # Use picked location
                self.click_x = int(self.pick_x_var.get() or 0)
                self.click_y = int(self.pick_y_var.get() or 0)
            else:
                # Use current cursor location
                self.click_x, self.click_y = pyautogui.position()
            
            self.clicking = True
            self.start_button.config(text="Running...")
            self.status_label.config(text="Status: Active", foreground="green")
            
            # Disable hotkey label
            self.hotkey_label.config(foreground="gray", cursor="")
            
            self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
            self.click_thread.start()
            
        except ValueError as e:
            messagebox.showerror("Error", "Invalid coordinates. Please enter valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def stop_clicking(self):
        """Stop the autoclicker"""
        self.clicking = False
        self.start_button.config(text="Start")
        self.status_label.config(text="Status: Idle", foreground="black")
        
        # Re-enable hotkey label
        self.hotkey_label.config(foreground="blue", cursor="hand2")
        
        # Remove focus from any entry field
        self.root.focus_set()
    
    def click_loop(self):
        """Main clicking loop"""
        click_count = 0
        max_clicks = int(self.repeat_times_var.get() or 1) if self.repeat_mode_var.get() == "repeat" else -1
        
        # Cache values to avoid lookups in tight loop
        button = self.mouse_button_var.get()
        double = (self.click_type_var.get() == "Double")
        check_emergency_every = 100  # Only check emergency stop every N clicks
        
        # For high precision timing
        import ctypes
        kernel32 = ctypes.windll.kernel32
        
        while self.clicking:
            try:
                # Check for emergency stop only occasionally (not every click)
                if click_count % check_emergency_every == 0:
                    current_x, current_y = pyautogui.position()
                    if current_x < 10 and current_y < 10:
                        self.root.after(0, self.stop_clicking)
                        break
                
                # Get interval before click for precise timing
                interval = self.get_click_interval()
                start_time = time.perf_counter()
                
                # Perform click
                self.fast_click(self.click_x, self.click_y, button, double)
                
                click_count += 1
                
                # Check if we've reached max clicks
                if max_clicks > 0 and click_count >= max_clicks:
                    self.root.after(0, self.stop_clicking)
                    break
                
                # High-precision sleep accounting for click time
                if interval > 0:
                    elapsed = time.perf_counter() - start_time
                    remaining = interval - elapsed
                    if remaining > 0:
                        # Use high precision sleep for very short intervals
                        if remaining < 0.010:  # Less than 10ms
                            # Busy wait for high precision
                            end_time = time.perf_counter() + remaining
                            while time.perf_counter() < end_time:
                                pass
                        else:
                            time.sleep(remaining)
                
            except Exception as e:
                print(f"Click error: {e}")
                self.root.after(0, self.stop_clicking)
                break
    
    def exit_app(self):
        """Clean exit"""
        self.clicking = False
        self.save_settings()
        try:
            keyboard.unhook_all()
        except:
            pass
        self.root.quit()
        sys.exit()
    
    def run(self):
        """Start the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.exit_app()

if __name__ == "__main__":
    try:
        app = AutoClicker()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")