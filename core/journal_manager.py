"""
Journal manager for Elite Dangerous Records Helper.
Handles journal file monitoring, parsing, and event processing.
"""

import os
import json
import time
import threading
import re
from datetime import datetime


class JournalManager:
    """Manages journal file monitoring and event processing"""

    def __init__(self, config_manager, event_callback=None):
        """Initialize the journal manager.

        Args:
            config_manager: The configuration manager instance.
            event_callback (callable, optional): Callback function for journal events.
        """
        self.config = config_manager
        self.event_callback = event_callback
        self.journal_path = self.config.get("journal_path", "")
        self.current_journal = None
        self.commander_name = "Unknown"
        self._stop_event = threading.Event()
        self._monitor_thread = None

    def start_monitoring(self):
        """Start journal monitoring in a separate thread.

        Returns:
            bool: True if monitoring started successfully, False otherwise.
        """
        if self._monitor_thread and self._monitor_thread.is_alive():
            print("Journal monitoring already running")
            return False

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_thread_func,
            daemon=True
        )
        self._monitor_thread.start()
        return True

    def stop_monitoring(self):
        """Stop journal monitoring.

        Returns:
            bool: True if monitoring stopped successfully, False otherwise.
        """
        if not self._monitor_thread or not self._monitor_thread.is_alive():
            return False

        self._stop_event.set()
        self._monitor_thread.join(timeout=2.0)
        return not self._monitor_thread.is_alive()

    def _monitor_thread_func(self):
        """Monitor journal files for changes."""
        last_journal = None
        last_size = 0
        last_mtime = 0

        # Try to get the initial journal file
        initial_journal = self.config.get_current_journal_path()
        if not initial_journal or not os.path.exists(initial_journal):
            initial_journal = self.find_latest_journal_with_valid_data()
            if not initial_journal:
                initial_journal = self.find_latest_journal_with_fsdjump()
            if not initial_journal:
                initial_journal = self.get_latest_journal_file()

        if initial_journal:
            last_journal = initial_journal
            self.config.save_current_journal_path(initial_journal)
            self.commander_name = self.extract_commander_name(initial_journal)

        while not self._stop_event.is_set():
            try:
                # Check if the journal directory exists
                if not os.path.exists(self.journal_path):
                    print(f"[ERROR] Journal directory does not exist: {self.journal_path}")
                    time.sleep(5)
                    continue

                # Get the latest journal file
                latest_journal = self.get_latest_journal_file()
                if not latest_journal:
                    time.sleep(1)
                    continue

                # Check if the journal file has changed
                if latest_journal != last_journal:
                    last_journal = latest_journal
                    last_size = 0
                    last_mtime = 0
                    self.config.save_current_journal_path(latest_journal)

                    # Extract commander name from the new journal
                    new_cmdr = self.extract_commander_name(latest_journal)
                    if new_cmdr != "Unknown":
                        self.commander_name = new_cmdr

                # Check if the journal file has been modified
                try:
                    stat = os.stat(last_journal)
                    current_size = stat.st_size
                    current_mtime = stat.st_mtime

                    if current_size > last_size or current_mtime > last_mtime:
                        # Process new journal entries
                        self._process_journal_events(last_journal, last_size)
                        last_size = current_size
                        last_mtime = current_mtime
                except Exception as e:
                    print(f"[ERROR] Error checking journal file: {e}")

                # Sleep to avoid high CPU usage
                time.sleep(1)
            except Exception as e:
                print(f"[ERROR] Journal monitoring error: {e}")
                time.sleep(5)

    def _process_journal_events(self, journal_path, start_position=0):
        """Process journal events and call callback.

        Args:
            journal_path (str): Path to the journal file.
            start_position (int, optional): Position to start reading from.
        """
        if not self.event_callback:
            return

        try:
            if not os.path.exists(journal_path):
                print(f"[ERROR] Journal file does not exist: {journal_path}")
                return

            with open(journal_path, 'r', encoding='utf-8') as f:
                try:
                    f.seek(start_position)
                    line_count = 0
                    event_count = 0

                    for line in f:
                        line_count += 1
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            event = json.loads(line)
                            event_type = event.get("event", "Unknown")

                            # Call the event callback
                            try:
                                self.event_callback(event)
                                event_count += 1
                            except Exception as e:
                                print(f"[ERROR] Error in event callback for event type {event_type}: {e}")

                        except json.JSONDecodeError:
                            # Silently skip invalid JSON
                            pass
                        except Exception as e:
                            print(f"[ERROR] Unexpected error parsing journal line: {e}")

                except Exception as e:
                    print(f"[ERROR] Error reading journal file: {e}")
        except Exception as e:
            print(f"[ERROR] Error processing journal events: {e}")

    def get_latest_journal_file(self):
        """Get the latest journal file in the journal directory.

        Returns:
            str: Path to the latest journal file, or None if not found.
        """
        if not os.path.exists(self.journal_path):
            return None

        journal_files = []
        for filename in os.listdir(self.journal_path):
            if filename.startswith("Journal.") and filename.endswith(".log"):
                filepath = os.path.join(self.journal_path, filename)
                journal_files.append(filepath)

        if not journal_files:
            return None

        # Sort by modification time (newest first)
        journal_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return journal_files[0]

    def find_latest_journal_with_fsdjump(self):
        """Find the latest journal file containing FSDJump events.

        Returns:
            str: Path to the latest journal file with FSDJump events, or None if not found.
        """
        if not os.path.exists(self.journal_path):
            return None

        journal_files = self.list_sorted_journals()

        for journal_file in journal_files:
            if self.has_fsdjump(journal_file):
                return journal_file

        return None

    def has_fsdjump(self, filepath):
        """Check if a journal file contains FSDJump events.

        Args:
            filepath (str): Path to the journal file.

        Returns:
            bool: True if the file contains FSDJump events, False otherwise.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if '"event":"FSDJump"' in line:
                        return True
        except:
            pass
        return False

    def find_latest_journal_with_valid_data(self):
        """Find the latest journal file containing valid data.

        Returns:
            str: Path to the latest journal file with valid data, or None if not found.
        """
        fsdjump_journal = self.find_latest_journal_with_fsdjump()
        if fsdjump_journal:
            return fsdjump_journal

        latest_journal = self.get_latest_journal_file()
        if latest_journal:
            return latest_journal

        return None

    def list_sorted_journals(self):
        """List journal files sorted by timestamp (newest first).

        Returns:
            list: List of journal file paths sorted by timestamp.
        """
        if not os.path.exists(self.journal_path):
            return []

        journal_files = []
        for filename in os.listdir(self.journal_path):
            if filename.startswith("Journal.") and filename.endswith(".log"):
                filepath = os.path.join(self.journal_path, filename)
                journal_files.append(filepath)

        # Sort by journal timestamp in filename
        def extract_timestamp(filepath):
            filename = os.path.basename(filepath)
            match = re.search(r'Journal\.(.+?)\.log', filename)
            if match:
                timestamp_str = match.group(1)
                try:
                    # Parse the timestamp format used in Elite Dangerous journal files
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H%M%S.%f")
                    return dt.timestamp()
                except:
                    pass
            return 0

        journal_files.sort(key=extract_timestamp, reverse=True)
        return journal_files

    def extract_commander_name(self, journal_path):
        """Extract commander name from a journal file.

        Args:
            journal_path (str): Path to the journal file.

        Returns:
            str: Commander name, or "Unknown" if not found.
        """
        if not os.path.exists(journal_path):
            return "Unknown"

        try:
            with open(journal_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event.get("event") == "Commander" and "Name" in event:
                            return event["Name"]
                        elif event.get("event") == "LoadGame" and "Commander" in event:
                            return event["Commander"]
                    except:
                        continue
        except:
            pass

        return "Unknown"

    def detect_commander_renames(self):
        """Detect commander renames by checking all journal files.

        Returns:
            list: List of commander names found in the journal files.
        """
        if not os.path.exists(self.journal_path):
            return []

        commanders = set()
        journal_files = self.list_sorted_journals()

        for journal_file in journal_files:
            cmdr = self.extract_commander_name(journal_file)
            if cmdr != "Unknown":
                commanders.add(cmdr)

        return list(commanders)
