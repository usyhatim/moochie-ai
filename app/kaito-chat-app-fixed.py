import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime
import threading
import re

class KaitoChatApp:
    def __init__(self, master):
        # Advanced Color Palette for Kaito
        self.DEEP_BLUE = "#1A2C4F"        # Dark navy blue
        self.ACCENT_BLUE = "#4A90E2"      # Bright accent blue
        self.DARK_GRAY = "#2C3E50"        # Dark gray for text
        self.LIGHT_GRAY = "#34495E"       # Slightly lighter gray
        self.BACKGROUND_COLOR = "#0F1A2A" # Deep space blue background
        self.TEXT_COLOR = "#E0E0E0"       # Light gray text
        self.BORDER_COLOR = "#4A90E2"     # Bright blue for borders

        # Master window setup
        self.master = master
        master.title("N25 Kaito | Brutal Honesty")
        master.geometry("1000x800")
        master.configure(bg=self.BACKGROUND_COLOR)

        # Custom theme setup
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Modern, sharp font configuration
        self.SYSTEM_FONT = ('Roboto', 12)
        self.SYSTEM_FONT_BOLD = ('Roboto', 12, 'bold')
        self.CHAT_FONT = ('Consolas', 11)

        # Configure styles
        self._configure_styles()

        # Main container
        self.main_container = ttk.Frame(master, padding="20 20 20 20", style='Main.TFrame')
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Database setup
        self.conn = sqlite3.connect('kaito_context_memory.db', check_same_thread=False)
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
        """Configure all custom styles with a sharp, tech-oriented look"""
        # Frame styles
        self.style.configure('Main.TFrame', background=self.BACKGROUND_COLOR)
        self.style.configure('Input.TFrame', background=self.BACKGROUND_COLOR)

        # Label styles
        self.style.configure('TLabel',
            background=self.BACKGROUND_COLOR,
            font=self.SYSTEM_FONT,
            foreground=self.TEXT_COLOR
        )

        # Button styles
        self.style.configure('Send.TButton',
            font=self.SYSTEM_FONT_BOLD,
            background=self.ACCENT_BLUE,
            foreground="white",
            padding=(20, 10)
        )
        self.style.map('Send.TButton',
            background=[('active', '#3A7CA5')],
            foreground=[('active', 'white')]
        )

        # Entry styles
        self.style.configure('Modern.TEntry',
            fieldbackground=self.LIGHT_GRAY,
            background=self.LIGHT_GRAY,
            foreground=self.TEXT_COLOR,
            borderwidth=1,
            relief="solid",
            padding=(10, 5)
        )

        # Combobox styles
        self.style.configure('Dropdown.TCombobox',
            background=self.LIGHT_GRAY,
            fieldbackground=self.LIGHT_GRAY,
            selectbackground=self.ACCENT_BLUE,
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
        # Chat History with advanced tech styling
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
            insertbackground=self.ACCENT_BLUE  # Cursor color
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Configure chat tags
        self.chat_history.tag_configure('user',
            foreground="#4A90E2",  # Bright blue for user
            font=('Roboto', 12, 'bold'),
            spacing1=10,
            spacing3=5
        )
        self.chat_history.tag_configure('ai',
            foreground=self.TEXT_COLOR,
            font=('Roboto', 12),
            spacing1=5,
            spacing3=10
        )
        self.chat_history.tag_configure('system',
            foreground="#FF4500",  # Orange for system messages
            font=('Roboto', 10, 'italic'),
            spacing1=5,
            spacing3=5
        )

        # Input Frame
        input_frame = ttk.Frame(self.main_container, style='Input.TFrame')
        input_frame.pack(fill=tk.X, pady=(0, 15))

        # Context Dropdown with tech styling
        self.context_var = tk.StringVar(value="Direct Mode")
        context_dropdown = ttk.Combobox(
            input_frame, 
            textvariable=self.context_var, 
            values=["Direct Mode", "Harsh Critique", "Tough Love", "Raw Honesty"],
            width=15,
            font=self.SYSTEM_FONT
        )
        context_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        # Input Entry with advanced design
        self.input_entry = ttk.Entry(
            input_frame, 
            width=50, 
            font=self.SYSTEM_FONT,
            style='Modern.TEntry'
        )
        self.input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        self.input_entry.bind("<Return>", self.send_message)
        
        # Placeholder effect
        self.input_entry.insert(0, "Speak. No Filter.")
        self.input_entry.bind("<FocusIn>", self.on_entry_click)
        self.input_entry.bind("<FocusOut>", self.on_focusout)

        # Send Button with tech styling
        send_button = ttk.Button(
            input_frame, 
            text="SEND", 
            command=self.send_message,
            style='Send.TButton'
        )
        send_button.pack(side=tk.LEFT)

        # Status Bar with advanced design
        self.status_var = tk.StringVar(value="System Online | N25 Kaito Initialized")
        status_bar = ttk.Label(
            self.main_container, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            font=('Consolas', 9),
            background=self.DEEP_BLUE,
            foreground=self.ACCENT_BLUE
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))

    def on_entry_click(self, event):
        """Remove placeholder text when entry is clicked"""
        if self.input_entry.get() == "Speak. No Filter.":
            self.input_entry.delete(0, tk.END)
            self.input_entry.config(foreground='black')

    def on_focusout(self, event):
        """Restore placeholder if no text is entered"""
        if self.input_entry.get() == "":
            self.input_entry.insert(0, "Speak. No Filter.")
            self.input_entry.config(foreground='gray')

    def send_message(self, event=None):
        user_message = self.input_entry.get().strip()
        if user_message and user_message != "Speak. No Filter.":
            # Thread for non-blocking AI response
            threading.Thread(target=self._process_message, args=(user_message,), daemon=True).start()

    def _process_message(self, user_message):
        # Update UI in main thread
        self.master.after(0, self._display_user_message, user_message)
        
        # Status update
        self.master.after(0, self.update_status, "Processing...")
        
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
            self.master.after(0, self.update_status, "Response received")
        
        except Exception as e:
            # Display error
            self.master.after(0, self._display_error, str(e))

    def _display_user_message(self, user_message):
        self.chat_history.insert(tk.END, f"You: {user_message}\n", "user")
        self.input_entry.delete(0, tk.END)
        self.chat_history.see(tk.END)

    def _display_ai_response(self, response_text):
        self.chat_history.insert(tk.END, f"Kaito: {response_text}\n\n", "ai")
        self.chat_history.see(tk.END)

    def _display_error(self, error_message):
        self.chat_history.insert(tk.END, f"System Error: {error_message}\n\n", "system")
        self.chat_history.see(tk.END)

    def _update_context(self, user_message, response_text):
        context_entry = f"User said: {user_message}\nKaito responded: {response_text}"
        self.context_window.append(context_entry)
        
        if len(self.context_window) > self.MAX_CONTEXT_LENGTH:
            self.context_window.pop(0)

    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)

    def build_contextual_prompt(self, user_message):
        """Enhanced contextual prompt building with N25 Kaito's personality"""
        context_str = "\n".join(self.context_window)
        
        # Retrieve context based on selected mode
        context_type = self.context_var.get()
        context_mapping = {
            "Harsh Critique": "Respond with maximum criticism and zero sugar-coating.",
            "Tough Love": "Provide harsh but constructive feedback.",
            "Raw Honesty": "Be brutally direct, hold nothing back.",
            "Direct Mode": "Give unfiltered, straightforward advice."
        }
        
        contextual_prompt = f"""
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
        return contextual_prompt

    def __del__(self):
        """Close database connection"""
        self.conn.close()

def main():
    root = tk.Tk()
    app = KaitoChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
