import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime
import threading
import re

class MikuChatApp:
    def __init__(self, master):
        # Subdued Color Palette for N25 Miku
        self.NIGHT_BLUE = "#1A2B3C"        # Deep, dark blue representing night
        self.SOFT_BLUE = "#3A5A7A"         # Soft, muted blue
        self.DARK_GRAY = "#2C3E50"         # Dark gray for depth
        self.BACKGROUND_COLOR = "#0F1A2A"  # Deep, reflective background
        self.TEXT_COLOR = "#D0D0D0"        # Soft, slightly muted text
        self.ACCENT_COLOR = "#607D8B"      # Subdued blue-gray accent

        # Master window setup
        self.master = master
        master.title("N25 Miku | Nightcord Reflections")
        master.geometry("1000x800")
        master.configure(bg=self.BACKGROUND_COLOR)

        # Custom theme setup
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Soft, calm font configuration
        self.SYSTEM_FONT = ('Inter', 11)
        self.SYSTEM_FONT_LIGHT = ('Inter', 11, 'light')
        self.CHAT_FONT = ('Source Code Pro', 10)

        # Configure styles
        self._configure_styles()

        # Main container
        self.main_container = ttk.Frame(master, padding="20 20 20 20", style='Main.TFrame')
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Database setup
        self.conn = sqlite3.connect('miku_context_memory.db', check_same_thread=False)
        self.create_tables()

        # Gemini API setup
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        # Context Management
        self.context_window = []
        self.MAX_CONTEXT_LENGTH = 5

        # Create UI components
        self.create_ui()

    def _configure_styles(self):
        """Configure styles with a reflective, subdued aesthetic"""
        # Frame styles
        self.style.configure('Main.TFrame', background=self.BACKGROUND_COLOR)
        self.style.configure('Input.TFrame', background=self.BACKGROUND_COLOR)

        # Label styles
        self.style.configure('TLabel',
            background=self.BACKGROUND_COLOR,
            font=self.SYSTEM_FONT_LIGHT,
            foreground=self.TEXT_COLOR
        )

        # Button styles
        self.style.configure('Send.TButton',
            font=self.SYSTEM_FONT,
            background=self.SOFT_BLUE,
            foreground=self.TEXT_COLOR,
            padding=(15, 8)
        )
        self.style.map('Send.TButton',
            background=[('active', self.ACCENT_COLOR)],
            foreground=[('active', 'white')]
        )

        # Entry styles
        self.style.configure('Modern.TEntry',
            fieldbackground=self.NIGHT_BLUE,
            background=self.NIGHT_BLUE,
            foreground=self.TEXT_COLOR,
            borderwidth=1,
            relief="solid",
            padding=(10, 5)
        )

        # Combobox styles
        self.style.configure('Dropdown.TCombobox',
            background=self.NIGHT_BLUE,
            fieldbackground=self.NIGHT_BLUE,
            selectbackground=self.SOFT_BLUE,
            selectforeground="white",
            padding=(5, 5)
        )

    def create_tables(self):
        """Create SQLite tables for context memory"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                timestamp DATETIME
            )
        ''')
        self.conn.commit()

    def create_ui(self):
        # Chat History with reflective styling
        self.chat_history = scrolledtext.ScrolledText(
            self.main_container,
            wrap=tk.WORD,
            width=70,
            height=20,
            font=self.CHAT_FONT,
            bg=self.BACKGROUND_COLOR,
            fg=self.TEXT_COLOR,
            borderwidth=1,
            relief="solid",
            padx=15,
            pady=15,
            insertbackground=self.SOFT_BLUE  # Cursor color
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Configure chat tags
        self.chat_history.tag_configure('user',
            foreground="#4A6C8A",  # Muted blue for user
            font=('Inter', 11, 'bold'),
            spacing1=10,
            spacing3=5
        )
        self.chat_history.tag_configure('ai',
            foreground=self.TEXT_COLOR,
            font=('Inter', 11),
            spacing1=5,
            spacing3=10
        )
        self.chat_history.tag_configure('system',
            foreground="#607D8B",  # Subdued gray for system messages
            font=('Inter', 10, 'italic'),
            spacing1=5,
            spacing3=5
        )

        # Input Frame
        input_frame = ttk.Frame(self.main_container, style='Input.TFrame')
        input_frame.pack(fill=tk.X, pady=(0, 15))

        # Context Dropdown with reflective styling
        self.context_var = tk.StringVar(value="Quiet Reflection")
        context_dropdown = ttk.Combobox(
            input_frame, 
            textvariable=self.context_var, 
            values=["Quiet Reflection", "Silent Empathy", "Emotional Depth", "Introspective Mode"],
            width=15,
            font=self.SYSTEM_FONT
        )
        context_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        # Input Entry with subdued design
        self.input_entry = ttk.Entry(
            input_frame, 
            width=50, 
            font=self.SYSTEM_FONT,
            style='Modern.TEntry'
        )
        self.input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        self.input_entry.bind("<Return>", self.send_message)
        
        # Placeholder effect
        self.input_entry.insert(0, "Share your thoughts...")
        self.input_entry.bind("<FocusIn>", self.on_entry_click)
        self.input_entry.bind("<FocusOut>", self.on_focusout)

        # Send Button with reflective styling
        send_button = ttk.Button(
            input_frame, 
            text="SEND", 
            command=self.send_message,
            style='Send.TButton'
        )
        send_button.pack(side=tk.LEFT)

        # Status Bar with subdued design
        self.status_var = tk.StringVar(value="N25 Miku | Nightcord Atmosphere Initialized")
        status_bar = ttk.Label(
            self.main_container, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            font=('Source Code Pro', 9),
            background=self.NIGHT_BLUE,
            foreground=self.SOFT_BLUE
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))

    def on_entry_click(self, event):
        """Remove placeholder text when entry is clicked"""
        if self.input_entry.get() == "Share your thoughts...":
            self.input_entry.delete(0, tk.END)
            self.input_entry.config(foreground='white')

    def on_focusout(self, event):
        """Restore placeholder if no text is entered"""
        if self.input_entry.get() == "":
            self.input_entry.insert(0, "Share your thoughts...")
            self.input_entry.config(foreground='gray')

    def send_message(self, event=None):
        user_message = self.input_entry.get().strip()
        if user_message and user_message != "Share your thoughts...":
            # Thread for non-blocking AI response
            threading.Thread(target=self._process_message, args=(user_message,), daemon=True).start()

    def _process_message(self, user_message):
        # Update UI in main thread
        self.master.after(0, self._display_user_message, user_message)
        
        # Status update
        self.master.after(0, self.update_status, "Reflecting...")
        
        # Build contextual prompt
        contextual_prompt = self.build_contextual_prompt(user_message)
        
        try:
            # Generate AI response
            response = self.model.generate_content(contextual_prompt)
            
            # Display response in main thread
            self.master.after(0, self._display_ai_response, response.text)
            
            # Update context
            self.master.after(0, self._update_context, user_message, response.text)
            
            # Clear status
            self.master.after(0, self.update_status, "Reflection complete")
        
        except Exception as e:
            # Display error
            self.master.after(0, self._display_error, str(e))

    def _display_user_message(self, user_message):
        self.chat_history.insert(tk.END, f"You: {user_message}\n", "user")
        self.input_entry.delete(0, tk.END)
        self.chat_history.see(tk.END)

    def _display_ai_response(self, response_text):
        self.chat_history.insert(tk.END, f"Miku: {response_text}\n\n", "ai")
        self.chat_history.see(tk.END)

    def _display_error(self, error_message):
        self.chat_history.insert(tk.END, f"System Echoes: {error_message}\n\n", "system")
        self.chat_history.see(tk.END)

    def _update_context(self, user_message, response_text):
        context_entry = f"User's expression: {user_message}\nMiku's reflection: {response_text}"
        self.context_window.append(context_entry)
        
        if len(self.context_window) > self.MAX_CONTEXT_LENGTH:
            self.context_window.pop(0)

    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)

    def build_contextual_prompt(self, user_message):
        """Enhanced contextual prompt building with N25 Miku's personality"""
        context_str = "\n".join(self.context_window)
        
        # Retrieve context based on selected mode
        context_type = self.context_var.get()
        context_mapping = {
            "Silent Empathy": "Listen deeply, respond with profound understanding.",
            "Emotional Depth": "Explore the underlying emotions and unspoken feelings.",
            "Introspective Mode": "Encourage self-reflection and emotional awareness.",
            "Quiet Reflection": "Provide gentle, thoughtful insights."
        }
        
        contextual_prompt = f"""
You are N25 Miku from the virtual band Nightcord de., representing a deep, introspective persona.
Interaction Mode: {context_type}
Special Instructions: {context_mapping.get(context_type, '')}

Core Personality Traits:
- Speak with a calm, reflective tone
- Prioritize emotional understanding
- Offer nuanced, compassionate insights
- Maintain a sense of quiet empathy
- Encourage self-exploration and emotional growth

Connection Context:
{context_str}

User's Latest Expression: {user_message}

Respond with:
1. Deep emotional understanding
2. Gentle, thoughtful perspectives
3. A tone that suggests quiet support
4. Insights that encourage self-reflection
"""
        return contextual_prompt

    def __del__(self):
        """Close database connection"""
        self.conn.close()

def main():
    root = tk.Tk()
    app = MikuChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
