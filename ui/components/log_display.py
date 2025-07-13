"""
Log display component for Elite Dangerous Records Helper.
Captures and displays log messages from the application.
"""

import sys
import io
import threading
import time
import customtkinter as ctk
from typing import Optional, List, Callable


class StdoutRedirector(io.StringIO):
    """Redirects stdout to a callback function."""

    def __init__(self, callback: Callable[[str], None]):
        """Initialize the stdout redirector.

        Args:
            callback: Function to call with captured output.
        """
        super().__init__()
        self.callback = callback
        self.original_stdout = sys.stdout

    def write(self, string: str):
        """Write to the redirected stdout.

        Args:
            string: The string to write.
        """
        # Write to original stdout
        self.original_stdout.write(string)
        self.original_stdout.flush()

        # Call the callback with the string
        self.callback(string)

        # Return the string for potential chaining
        return string

    def flush(self):
        """Flush the redirected stdout."""
        self.original_stdout.flush()


class LogDisplay(ctk.CTkFrame):
    """Component for displaying log messages."""

    def __init__(self, parent, **kwargs):
        """Initialize the log display.

        Args:
            parent: The parent widget.
            **kwargs: Additional keyword arguments for the frame.
        """
        super().__init__(parent, **kwargs)

        # Set up UI
        self._setup_ui()

        # Initialize variables
        self.log_buffer = []
        self.max_buffer_size = 1000
        self.auto_scroll = True
        self.redirector = None

        # Start log capture
        self._start_capture()

    def _setup_ui(self):
        """Set up the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create header frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

        # Create title label
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Application Logs",
            font=("Segoe UI", 14, "bold"),
            text_color="#FF7F50"
        )
        self.title_label.pack(side="left")

        # Create auto-scroll checkbox
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        self.auto_scroll_checkbox = ctk.CTkCheckBox(
            self.header_frame,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            command=self._toggle_auto_scroll
        )
        self.auto_scroll_checkbox.pack(side="right")

        # Create clear button
        self.clear_button = ctk.CTkButton(
            self.header_frame,
            text="Clear",
            width=80,
            height=25,
            command=self.clear_logs
        )
        self.clear_button.pack(side="right", padx=10)

        # Create log text widget
        self.log_text = ctk.CTkTextbox(
            self,
            wrap="word",
            font=("Consolas", 12),
            text_color="#B0B0B0",
            fg_color="#1f1f1f"
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Make text widget read-only
        self.log_text.configure(state="disabled")

    def _start_capture(self):
        """Start capturing stdout."""
        # Create redirector
        self.redirector = StdoutRedirector(self._on_log)

        # Redirect stdout
        sys.stdout = self.redirector

        # Print initial message
        print("[INFO] Log capture started")

    def _stop_capture(self):
        """Stop capturing stdout."""
        # Restore original stdout
        if self.redirector:
            sys.stdout = self.redirector.original_stdout
            self.redirector = None

    def _on_log(self, message: str):
        """Handle a log message.

        Args:
            message: The log message.
        """
        # Add to buffer
        self.log_buffer.append(message)

        # Trim buffer if needed
        if len(self.log_buffer) > self.max_buffer_size:
            self.log_buffer = self.log_buffer[-self.max_buffer_size:]

        # Update display
        self._update_display()

    def _update_display(self):
        """Update the log display."""
        # Enable text widget for editing
        self.log_text.configure(state="normal")

        # Clear current content
        self.log_text.delete("1.0", "end")

        # Add all messages from buffer
        for message in self.log_buffer:
            # Color-code messages based on level
            if "[ERROR]" in message:
                self.log_text.insert("end", message, ("error",))
            elif "[WARNING]" in message:
                self.log_text.insert("end", message, ("warning",))
            elif "[DEBUG]" in message:
                self.log_text.insert("end", message, ("debug",))
            elif "[INFO]" in message:
                self.log_text.insert("end", message, ("info",))
            else:
                self.log_text.insert("end", message)

        # Configure tags for colored text
        self.log_text.tag_config("error", foreground="#E74C3C")
        self.log_text.tag_config("warning", foreground="#F39C12")
        self.log_text.tag_config("debug", foreground="#3498DB")
        self.log_text.tag_config("info", foreground="#4ECDC4")

        # Auto-scroll to end if enabled
        if self.auto_scroll:
            self.log_text.see("end")

        # Make text widget read-only again
        self.log_text.configure(state="disabled")

    def _toggle_auto_scroll(self):
        """Toggle auto-scroll setting."""
        self.auto_scroll = self.auto_scroll_var.get()

        # If auto-scroll is enabled, scroll to end
        if self.auto_scroll:
            self.log_text.see("end")

    def clear_logs(self):
        """Clear all logs."""
        # Clear buffer
        self.log_buffer = []

        # Update display
        self._update_display()

        # Print clear message
        print("[INFO] Logs cleared")

    def destroy(self):
        """Clean up before destroying the widget."""
        # Stop capturing stdout
        self._stop_capture()

        # Call parent destroy
        super().destroy()
