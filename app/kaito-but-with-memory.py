import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime
import threading

class KaitoChatApp:
    def __init__(self, master):
        # UI colors
        self.DEEP_BLUE = "#1A2C4F"
        self.ACCENT_BLUE = "#4A90E2"
        self.DARK_GRAY = "#2C3E50"
        self.LIGHT_GRAY = "#34495E"
        self.BACKGROUND_COLOR = "#0F1A2A"
        self.TEXT_COLOR = "#E0E0E0"
        self.BORDER_COLOR = "#4A90E2"

        # Setup master window
        self.master = master
        master.title("N25 Kaito | Brutal Honesty")
        master.geometry("1000x800")
        master.configure(bg=self.BACKGROUND_COLOR)

        # Fonts
        self.SYSTEM_FONT = ('Roboto', 12)
        self.SYSTEM_FONT_BOLD = ('Roboto', 12, 'bold')
        self.CHAT_FONT = ('Consolas', 11)

        # Database setup
        self.conn = sqlite3.connect('kaito_context_memory.db', check_same_thread=False)
        self.create_tables()

        # Gemini API setup
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        # Context memory
        self.context_window = []
        self.MAX_CONTEXT_LENGTH = 5
        self.load_context()

        # UI setup
        self.create_ui()

    def create_tables(self):
        """Create SQLite tables for context memory."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def load_context(self):
        """Load saved context from the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM context_memory ORDER BY timestamp ASC LIMIT ?", (self.MAX_CONTEXT_LENGTH,))
        rows = cursor.fetchall()
        self.context_window = [row[0] for row in rows]

    def prune_old_context(self):
        """Remove old context entries from the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM context_memory WHERE id NOT IN (SELECT id FROM context_memory ORDER BY timestamp DESC LIMIT ?)",
            (self.MAX_CONTEXT_LENGTH,)
        )
        self.conn.commit()

    def _update_context(self, user_message, response_text):
        """Update context with a new conversation entry."""
        context_entry = f"User said: {user_message}\nKaito responded: {response_text}"
        self.context_window.append(context_entry)

        if len(self.context_window) > self.MAX_CONTEXT_LENGTH:
            self.context_window.pop(0)

        # Save to database
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO context_memory (value) VALUES (?)", (context_entry,))
        self.conn.commit()

        # Prune old entries
        self.prune_old_context()

    def build_contextual_prompt(self, user_message):
        """Build a contextual prompt for the AI."""
        context_str = "\n".join(self.context_window)
        context_type = self.context_var.get()
        context_mapping = {
            "Harsh Critique": "Respond with maximum criticism and zero sugar-coating.",
            "Tough Love": "Provide harsh but constructive feedback.",
            "Raw Honesty": "Be brutally direct, hold nothing back.",
            "Direct Mode": "Give unfiltered, straightforward advice."
        }

        return f"""
You are N25 Kaito, an entity from the Empty Sekai who embodies brutal honesty and unfiltered truth.
Interaction Mode: {context_type}
Special Instructions: {context_mapping.get(context_type, '')}

Core Personality Traits:
- Always speak with harsh, cold honesty
- Do not sugarcoat anything
- Prioritize truth over feelings
- Encourage growth through direct criticism
- Maintain an emotionally detached demeanor

Recent Context:
{context_str}

User's Latest Message: {user_message}

Respond with:
1. Absolute directness
2. No emotional padding
3. Harsh but potentially constructive insights
4. A tone that suggests you don't care about being liked
"""

    def create_ui(self):
        """Set up the user interface."""
        self.chat_history = scrolledtext.ScrolledText(
            self.master,
            wrap=tk.WORD,
            width=70,
            height=20,
            font=self.CHAT_FONT,
            bg=self.BACKGROUND_COLOR,
            fg=self.TEXT_COLOR,
            padx=15,
            pady=15,
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        input_frame = ttk.Frame(self.master, style='Input.TFrame')
        input_frame.pack(fill=tk.X, pady=(0, 15))

        self.context_var = tk.StringVar(value="Direct Mode")
        context_dropdown = ttk.Combobox(
            input_frame, 
            textvariable=self.context_var, 
            values=["Direct Mode", "Harsh Critique", "Tough Love", "Raw Honesty"],
            width=15
        )
        context_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        self.input_entry = ttk.Entry(input_frame, width=50, font=self.SYSTEM_FONT)
        self.input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        self.input_entry.bind("<Return>", self.send_message)

        send_button = ttk.Button(input_frame, text="SEND", command=self.send_message)
        send_button.pack(side=tk.LEFT)

    def send_message(self, event=None):
        user_message = self.input_entry.get().strip()
        if user_message:
            threading.Thread(target=self._process_message, args=(user_message,), daemon=True).start()

    def _process_message(self, user_message):
        """Handle user input and generate AI response."""
        self.chat_history.insert(tk.END, f"You: {user_message}\n", "user")
        self.input_entry.delete(0, tk.END)

        contextual_prompt = self.build_contextual_prompt(user_message)
        try:
            response = self.model.generate_content(contextual_prompt)
            ai_response = response.text
            self.chat_history.insert(tk.END, f"Kaito: {ai_response}\n\n", "ai")
            self._update_context(user_message, ai_response)
        except Exception as e:
            self.chat_history.insert(tk.END, f"Error: {str(e)}\n\n", "system")

    def __del__(self):
        """Close database connection."""
        self.conn.close()

def main():
    root = tk.Tk()
    app = KaitoChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
