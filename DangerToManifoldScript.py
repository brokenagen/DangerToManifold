import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import obd
import threading
import random


class DangerToManifoldGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Danger to Manifold")
        self.geometry("500x400")

        self.shift_indicator_rpm = tk.IntVar(value=4000)
        self.current_rpm = tk.IntVar(value=0)
        self.rpm_direction = tk.IntVar(value=1)
        self.is_demo_mode = tk.BooleanVar(value=False)

        self.create_widgets()
        self.connection = obd.OBD()  # Connect to OBD port
        self.preload_gif()
        self.update_rpm()
        self.wm_state("iconic")

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(pady=10, padx=20)

        settings_frame = ttk.LabelFrame(main_frame, text="Settings")
        settings_frame.grid(row=0, column=0, padx=10, pady=10)

        ttk.Label(settings_frame, text="Shift Indicator RPM:").grid(row=0, column=0, padx=10, pady=10)
        shift_rpm_entry = ttk.Entry(settings_frame, textvariable=self.shift_indicator_rpm, width=10)
        shift_rpm_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(settings_frame, text="Current RPM:").grid(row=1, column=0, padx=10, pady=10)
        current_rpm_label = ttk.Label(settings_frame, textvariable=self.current_rpm, width=10)
        current_rpm_label.grid(row=1, column=1, padx=10, pady=10)

        ttk.Style().configure("DemoButton.TButton", background="white", borderwidth=2, relief="groove")
        demo_button = ttk.Button(settings_frame, text="Demo Mode", style="DemoButton.TButton", command=self.toggle_demo_mode)
        demo_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        self.create_terminal(main_frame)

    def create_terminal(self, parent):
        terminal_frame = ttk.LabelFrame(parent, text="Terminal")
        terminal_frame.grid(row=0, column=1, padx=10, pady=10)

        self.terminal = tk.Text(terminal_frame, wrap=tk.WORD, bg="black", fg="white", height=10, width=40)
        self.terminal.pack(fill=tk.BOTH, expand=True)

    def print_to_terminal(self, message):
        self.terminal.insert(tk.END, message + "\n")
        self.terminal.see(tk.END)

    def toggle_demo_mode(self):
        if self.is_demo_mode.get():
            self.current_rpm.set(0)

        self.is_demo_mode.set(not self.is_demo_mode.get())
        self.print_to_terminal("Demo Mode: " + str(self.is_demo_mode.get()))

    def update_rpm(self):
        if self.is_demo_mode.get():
            # Use mock RPM data for testing purposes
            if self.current_rpm.get() >= 7000:
                self.rpm_direction.set(-1)
            elif self.current_rpm.get() <= 1000:
                self.rpm_direction.set(1)
            self.current_rpm.set(self.current_rpm.get() + self.rpm_direction.get() * 100)
        else:
            cmd = obd.commands.RPM
            response = self.connection.query(cmd)
            if not response.is_null():
                self.current_rpm.set(response.value.magnitude)
                self.print_to_terminal("OBD response valid: RPM = " + str(self.current_rpm.get()))
            else:
                self.print_to_terminal("OBD response invalid")

        rpm_difference = abs(self.current_rpm.get() - self.shift_indicator_rpm.get())
        if rpm_difference > 2000:
            refresh_rate = 200
        else:
            refresh_rate = 50

        self.check_rpm_trigger()
        self.after(refresh_rate, self.update_rpm)

    def check_rpm_trigger(self):
        if self.current_rpm.get() >= self.shift_indicator_rpm.get():
            self.show_gif()
        else:
            if hasattr(self, 'gif_window') and self.gif_window.winfo_exists():
                self.gif_window.destroy()

    def load_frames(self, image):
        frames = []
        try:
            for i in range(image.n_frames):
                image.seek(i)
                frame = ImageTk.PhotoImage(
                    image.copy().resize((self.winfo_screenwidth(), self.winfo_screenheight()), Image.LANCZOS))
                frames.append(frame)
        except EOFError:
            pass
        return frames

    def preload_gif(self):
        gif = Image.open("Danger-to-Manifold.gif")
        self.frames = self.load_frames(gif)

    def show_gif(self):
        if hasattr(self, 'gif_window') and self.gif_window.winfo_exists():
            return

        self.gif_window = tk.Toplevel(self)
        self.gif_window.attributes("-fullscreen", True)
        self.gif_window.attributes("-topmost", True)

        gif_label = ttk.Label(self.gif_window)
        gif_label.pack(expand=True)

        self.current_frame = 0
        self.num_frames = len(self.frames)

        def animate():
            if not self.gif_window.winfo_exists():
                return

            gif_label.config(image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % self.num_frames
            self.gif_window.after(50, animate)  # Replace gif.info[42] with 50

            if self.current_frame == 0 and self.current_rpm.get() >= 7000:
                self.current_rpm.set(1000)

        animate()

        self.gif_window.bind("<Escape>", lambda event: self.gif_window.destroy())

if __name__ == "__main__":
    app = DangerToManifoldGUI()
    app.mainloop()