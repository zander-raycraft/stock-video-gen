import tkinter as tk
from tkinter import ttk, messagebox
import pyaudio
import wave
from pydub import AudioSegment
import numpy as np
import os

class AudioRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Recorder")
        self.root.configure(bg='white')
        self.root.geometry("800x600")

        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.recording = False
        self.saved_files = []
        self.current_file_index = 0
        self.created_files = []  # List of created files
        self.current_run = []
        self.run_index = 0
        self.master_track = "master_track.wav"
        self.last_segment_file = None

        self.status_label = tk.Label(root, text="Not Recording", bg='red', fg='white', width=20)
        self.status_label.pack(pady=10)

        self.device_label = tk.Label(root, text="Select Input Device:", bg='white', fg='black')
        self.device_label.pack(pady=5)

        self.device_combobox = ttk.Combobox(root, values=self.get_input_devices())
        self.device_combobox.pack(pady=5)

        self.record_button = tk.Button(root, text="Record", command=self.start_recording, bg='white', fg='black')
        self.record_button.pack(pady=5)

        self.save_point_button = tk.Button(root, text="Save Point", command=self.save_point, bg='white', fg='black')
        self.save_point_button.pack(pady=5)

        # Frame to hold the 'Save', 'Discard', and 'Stop' buttons
        self.button_frame = tk.Frame(root, bg='white')
        self.button_frame.pack(pady=5)

        # 'Stop' button centered
        self.stop_button = tk.Button(self.button_frame, text="Stop", command=self.stop_recording, bg='white', fg='black')
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 'Save' and 'Discard' buttons next to 'Stop' button
        self.discard_button = tk.Button(self.button_frame, text="Discard", command=self.discard_segment, bg='white', fg='black', state=tk.DISABLED)
        self.discard_button.pack(side=tk.LEFT, padx=5)

        self.save_button_2 = tk.Button(self.button_frame, text="Save", command=self.save_segment, bg='white', fg='black', state=tk.DISABLED)
        self.save_button_2.pack(side=tk.LEFT, padx=5)

        self.save_run_button = tk.Button(root, text="Save Run to Master Track", command=self.save_run_to_master, bg='white', fg='black')
        self.save_run_button.pack(pady=5)

        self.play_last_button = tk.Button(root, text="Play Last Segment", command=self.play_last_segment, bg='white', fg='black')
        self.play_last_button.pack(pady=5)

        self.play_current_run_button = tk.Button(root, text="Play Current Run", command=self.play_current_run, bg='white', fg='black')
        self.play_current_run_button.pack(pady=5)

        self.play_master_button = tk.Button(root, text="Play Master Track", command=self.play_master, bg='white', fg='black')
        self.play_master_button.pack(pady=5)

        self.start_new_button = tk.Button(root, text="Start New", command=self.start_new, bg='white', fg='black')
        self.start_new_button.pack(pady=5)

        self.volume_label = tk.Label(root, text="Mic Volume Level:", bg='white', fg='black')
        self.volume_label.pack(pady=10)

        self.volume_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=200)
        self.volume_bar.pack(pady=10)

        self.update_volume()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_input_devices(self):
        input_devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(f"{device_info['index']}: {device_info['name']}")
        return input_devices

    def start_recording(self):
        if not self.recording:
            try:
                self.selected_device_index = int(self.device_combobox.get().split(':')[0])
                self.frames = []
                self.stream = self.audio.open(format=self.audio_format, channels=self.channels, rate=self.rate, input=True,
                                              input_device_index=self.selected_device_index, frames_per_buffer=self.chunk)
                self.recording = True
                self.status_label.config(text="Recording", bg='green')
                self.root.after(1, self.record)
            except ValueError:
                messagebox.showerror("Error", "Please select a valid input device.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

    def record(self):
        if self.recording:
            try:
                data = self.stream.read(self.chunk)
                self.frames.append(data)
                self.root.after(1, self.record)
                self.save_point_button.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
                self.stop_recording()

    def save_point(self):
        if self.recording or self.frames:
            filename = f"segment_{self.current_file_index}.wav"
            self.current_file_index += 1
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            self.saved_files.append(filename)
            self.created_files.append(filename)
            self.current_run.append(filename)
            self.last_segment_file = filename
            self.frames = []

    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.stream.stop_stream()
            self.stream.close()
            self.status_label.config(text="Not Recording", bg='red')
            self.save_point()
            self.show_save_or_discard_buttons()

    def show_save_or_discard_buttons(self):
        self.save_run_button.pack_forget()
        self.record_button.config(state=tk.DISABLED)
        self.save_point_button.config(state=tk.DISABLED)

        # Enable 'Save' and 'Discard' buttons and set their colors
        self.discard_button.config(state=tk.NORMAL, bg='red', fg='white')
        self.save_button_2.config(state=tk.NORMAL, bg='green', fg='white')

    def hide_save_or_discard_buttons(self):
        # Disable 'Save' and 'Discard' buttons and set their colors
        self.discard_button.config(state=tk.DISABLED, bg='white', fg='black')
        self.save_button_2.config(state=tk.DISABLED, bg='white', fg='black')

        self.record_button.config(state=tk.NORMAL)
        self.save_run_button.pack(pady=5)

    def save_segment(self):
        if self.last_segment_file:
            self.saved_files.append(self.last_segment_file)
        self.hide_save_or_discard_buttons()

    def discard_segment(self):
        if self.last_segment_file:
            # Remove the file from disk
            try:
                os.remove(self.last_segment_file)
            except FileNotFoundError:
                pass
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting file {self.last_segment_file}: {e}")

            # Update tracking lists
            if self.last_segment_file in self.saved_files:
                self.saved_files.remove(self.last_segment_file)
            if self.last_segment_file in self.created_files:
                self.created_files.remove(self.last_segment_file)

            # Clear the last segment reference
            self.last_segment_file = None
            
            # Remove the last segment from the current run
            if self.current_run:
                self.current_run.pop()

        self.hide_save_or_discard_buttons()

    def play_last_segment(self):
        if self.last_segment_file and os.path.exists(self.last_segment_file):
            os.system(f"start {self.last_segment_file}")

    def play_current_run(self):
        if self.current_run:
            combined = AudioSegment.empty()
            for file in self.current_run:
                if os.path.exists(file):
                    segment = AudioSegment.from_wav(file)
                    combined += segment
            combined.export("temp_run.wav", format="wav")
            os.system("start temp_run.wav")

    def play_master(self):
        if os.path.exists(self.master_track):
            os.system(f"start {self.master_track}")

    def save_run_to_master(self):
        if self.current_run:
            run_filename = f"run_{self.run_index}.wav"
            self.run_index += 1

            combined_run = AudioSegment.empty()
            for file in self.current_run:
                if os.path.exists(file):
                    segment = AudioSegment.from_wav(file)
                    combined_run += segment
            combined_run.export(run_filename, format="wav")
            self.created_files.append(run_filename)

            if os.path.exists(self.master_track):
                master_track = AudioSegment.from_wav(self.master_track)
                combined_run = master_track + combined_run
                combined_run.export(self.master_track, format="wav")
            else:
                combined_run.export(self.master_track, format="wav")

            self.current_run = []

    def start_new(self):
        self.frames = []
        self.saved_files = []
        self.current_file_index = 0
        self.current_run = []
        self.run_index = 0

    def update_volume(self):
        try:
            volume = np.abs(np.random.randn(1)[0])  # Placeholder for actual volume level measurement
            self.volume_bar['value'] = volume * 100
        except Exception as e:
            print(f"Error updating volume: {e}")
        self.root.after(100, self.update_volume)

    def on_closing(self):
        # Add 'temp_run.wav' to the list of files to delete
        temp_run_file = "temp_run.wav"
        self.created_files.append(temp_run_file)
        for file in self.created_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except FileNotFoundError:
                    pass
                except Exception as e:
                    messagebox.showerror("Error", f"Error deleting file {file}: {e}")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorder(root)
    root.mainloop()