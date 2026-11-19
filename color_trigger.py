import sys
import time
import threading
import ctypes
import tkinter as tk
from tkinter import ttk
import numpy as np
import mss

# Enable DPI awareness on Windows so screen coordinates and mss match 1:1
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Optional global hotkey support using 'keyboard' library if installed
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False


# --- Windows Mouse Event Constants ---
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP   = 0x0010

def right_click():
    """Simulates a right mouse button press and release."""
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)  # Short press duration for reliable game/app detection
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


class ColorDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Color Trigger")
        self.root.geometry("380x360")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1e1e24")

        # Running flag and worker thread reference
        self.is_running = False
        self.thread = None
        self.detected_count = 0

        # Target Exact Color: RGB(86, 90, 102)
        self.target_r = 86
        self.target_g = 90
        self.target_b = 102

        # Capture Box Dimension
        self.box_size = 400

        # Post-detection cooldown in seconds
        self.cooldown_sec = 5.0

        # Setup GUI elements
        self.setup_ui()

        # Register Hotkey F6 if keyboard module is available
        if HAS_KEYBOARD:
            try:
                keyboard.add_hotkey("F6", self.toggle_hotkey_safe)
            except Exception as e:
                print(f"[Warning] Could not bind hotkey F6: {e}")

        # Proper cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # Header Title
        title_label = tk.Label(
            self.root,
            text="CENTER SCREEN COLOR TRIGGER",
            font=("Segoe UI", 12, "bold"),
            fg="#e0e0e0",
            bg="#1e1e24"
        )
        title_label.pack(pady=(12, 4))

        sub_label = tk.Label(
            self.root,
            text="400x400 Center Zone | Auto Right-Click (5s cooldown)",
            font=("Segoe UI", 8),
            fg="#9e9ea6",
            bg="#1e1e24"
        )
        sub_label.pack(pady=(0, 10))

        # Big ON / OFF Toggle Button
        self.toggle_btn = tk.Button(
            self.root,
            text="STATUS: OFF\n[ Click to Turn ON ]",
            font=("Segoe UI", 14, "bold"),
            bg="#c0392b",
            fg="white",
            activebackground="#962d22",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            height=3,
            command=self.toggle_state
        )
        self.toggle_btn.pack(fill="x", padx=30, pady=8)

        # Info Frame
        info_frame = tk.Frame(self.root, bg="#2a2a34", bd=1, relief="solid")
        info_frame.pack(fill="x", padx=30, pady=10)

        color_info = f"Target Exact Color: RGB({self.target_r}, {self.target_g}, {self.target_b})"
        self.lbl_range = tk.Label(
            info_frame,
            text=color_info,
            font=("Segoe UI", 8, "bold"),
            fg="#a8d8ea",
            bg="#2a2a34"
        )
        self.lbl_range.pack(pady=(6, 2))

        hotkey_text = "Hotkey: F6 toggles ON/OFF" if HAS_KEYBOARD else "Hotkey: Install 'keyboard' for F6 toggle"
        self.lbl_hotkey = tk.Label(
            info_frame,
            text=hotkey_text,
            font=("Segoe UI", 8),
            fg="#f1c40f",
            bg="#2a2a34"
        )
        self.lbl_hotkey.pack(pady=(0, 2))

        self.lbl_count = tk.Label(
            info_frame,
            text="Detections Triggered: 0",
            font=("Segoe UI", 8),
            fg="#e0e0e0",
            bg="#2a2a34"
        )
        self.lbl_count.pack(pady=(0, 6))

        # Status text at bottom
        self.status_lbl = tk.Label(
            self.root,
            text="Detector is stopped.",
            font=("Segoe UI", 9, "italic"),
            fg="#a0a0a0",
            bg="#1e1e24"
        )
        self.status_lbl.pack(side="bottom", pady=10)

    def toggle_hotkey_safe(self):
        # Hotkey callback runs in separate thread, schedule in GUI loop
        self.root.after(0, self.toggle_state)

    def toggle_state(self):
        if not self.is_running:
            self.start_detection()
        else:
            self.stop_detection()

    def start_detection(self):
        self.is_running = True
        self.toggle_btn.configure(
            text="STATUS: ON\n[ Click to Turn OFF ]",
            bg="#27ae60",
            activebackground="#1e8449"
        )
        self.status_lbl.configure(text="Scanning center 400x400 zone...", fg="#2ecc71")

        # Start search loop in a background daemon thread
        self.thread = threading.Thread(target=self.search_loop, daemon=True)
        self.thread.start()

    def stop_detection(self):
        self.is_running = False
        self.toggle_btn.configure(
            text="STATUS: OFF\n[ Click to Turn ON ]",
            bg="#c0392b",
            activebackground="#962d22"
        )
        self.status_lbl.configure(text="Detector is stopped.", fg="#a0a0a0")

    def search_loop(self):
        # Calculate center 400x400 zone
        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
        screen_h = ctypes.windll.user32.GetSystemMetrics(1)
        center_x = screen_w // 2
        center_y = screen_h // 2

        grab_zone = {
            "left": center_x - (self.box_size // 2),
            "top": center_y - (self.box_size // 2),
            "width": self.box_size,
            "height": self.box_size
        }

        # Initialize MSS screen capture context
        # MSS can be used with mss.MSS() or mss.mss()
        sct_factory = getattr(mss, "MSS", mss.mss)
        with sct_factory() as sct:
            while self.is_running:
                try:
                    # 1. Grab center screen area
                    grabbed_img = sct.grab(grab_zone)
                    pmap = np.array(grabbed_img)  # BGRA image

                    # 2. Extract channels as int16
                    # pmap[:, :, 0] -> Blue, [:, :, 1] -> Green, [:, :, 2] -> Red
                    r = pmap[:, :, 2].astype(np.int16)
                    g = pmap[:, :, 1].astype(np.int16)
                    b = pmap[:, :, 0].astype(np.int16)

                    # 3. Exact color mask: RGB(86, 90, 102)
                    mask_r = (r == self.target_r)
                    mask_g = (g == self.target_g)
                    mask_b = (b == self.target_b)
                    mask = mask_r & mask_g & mask_b

                    # 4. Check if matching pixels exist
                    ys, xs = np.where(mask)
                    if xs.size > 0:
                        # Match detected!
                        self.detected_count += 1
                        print(f"[Trigger] Found {xs.size} matching pixels! Executing Right Click...")

                        # Update GUI labels safely
                        self.root.after(0, lambda: self.lbl_count.configure(
                            text=f"Detections Triggered: {self.detected_count}"
                        ))
                        self.root.after(0, lambda: self.status_lbl.configure(
                            text="Target detected! Clicked RMB. Cooling down...",
                            fg="#f39c12"
                        ))

                        # Perform Right Mouse Button Click
                        right_click()

                        # Wait 5 seconds cooldown (responsive sleep to allow quick OFF toggle)
                        cooldown_steps = int(self.cooldown_sec / 0.1)
                        for _ in range(cooldown_steps):
                            if not self.is_running:
                                break
                            time.sleep(0.1)

                        if self.is_running:
                            self.root.after(0, lambda: self.status_lbl.configure(
                                text="Scanning center 400x400 zone...",
                                fg="#2ecc71"
                            ))

                except Exception as e:
                    print(f"[Error in search loop]: {e}")
                    time.sleep(0.5)

                # Small sleep between grabs to prevent 100% CPU usage
                time.sleep(0.01)

    def on_closing(self):
        self.is_running = False
        if HAS_KEYBOARD:
            try:
                keyboard.unhook_all()
            except Exception:
                pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ColorDetectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

