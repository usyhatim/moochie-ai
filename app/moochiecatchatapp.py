import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime
import threading
import re

class MoochieCatChatApp:
    def __init__(self, master):
        # Pastel Pink Color Palette
        self.PASTEL_PINK = "#FFD1DC"  # Soft pastel pink
        self.LIGHT_PINK = "#FFF0F5"   # Very light pink for background
        self.DARK_PINK = "#FFC0CB"    # Slightly darker pink for accents
        self.TEXT_COLOR = "#4A4A4A"   # Soft dark gray for readability

        # Master window setup
        self.master = master
        master.title("Moochie Cat AI")
        master.geometry("800x700")
        master.configure(bg=self.LIGHT_PINK)

        # Custom theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Apple-like font configuration
        self.SYSTEM_FONT = ('SF Pro Text', 11)
        self.SYSTEM_FONT_BOLD = ('SF Pro Text', 11, 'bold')
        self.MONOSPACE_FONT = ('SF Mono', 10)

        self.style.configure('TFrame', background=self.LIGHT_PINK)
        self.style.configure('TLabel', 
            background=self.LIGHT_PINK, 
            font=self.SYSTEM_FONT,
            foreground=self.TEXT_COLOR
        )
        self.style.configure('TButton', 
            font=self.SYSTEM_FONT_BOLD, 
            background=self.PASTEL_PINK, 
            foreground=self.TEXT_COLOR
        )

        # Main container
        self.main_container = ttk.Frame(master, padding="20 20 20 20")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Database setup
        self.conn = sqlite3.connect('context_memory.db', check_same_thread=False)
        self.create_tables()

        # Gemini API setup
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        # Create UI components
        self.create_ui()

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
        # Chat History with pastel styling
        self.chat_history = scrolledtext.ScrolledText(
            self.main_container, 
            wrap=tk.WORD, 
            width=70, 
            height=20,
            font=self.MONOSPACE_FONT,
            bg="#FFFFFF", 
            fg=self.TEXT_COLOR,
            borderwidth=1,
            relief="solid"
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Tag configuration for different message types
        self.chat_history.tag_config('user', 
            foreground="#8B4513",  # Soft brown for user messages 
            font=('SF Pro Text', 11, 'bold')
        )
        self.chat_history.tag_config('ai', 
            foreground="#FF69B4",  # Hot pink for Moochie Cat
            font=self.SYSTEM_FONT
        )
        self.chat_history.tag_config('system', 
            foreground="#C71585",  # Medium violet red for system messages
            font=('SF Pro Text', 9, 'italic')
        )

        # Input Frame with pastel design
        input_frame = ttk.Frame(self.main_container)
        input_frame.pack(fill=tk.X, pady=(10, 0))

        # Context Dropdown with pastel styling
        self.context_var = tk.StringVar(value="Moochie Mode")
        context_dropdown = ttk.Combobox(
            input_frame, 
            textvariable=self.context_var, 
            values=["Moochie Mode", "Playful", "Cuddly", "Sassy"],
            width=15,
            font=self.SYSTEM_FONT
        )
        context_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        # Input Entry with pastel design
        self.input_entry = ttk.Entry(
            input_frame, 
            width=50, 
            font=self.SYSTEM_FONT
        )
        self.input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        self.input_entry.bind("<Return>", self.send_message)
        
        # Placeholder effect
        self.input_entry.insert(0, "Meow to Moochie Cat...")
        self.input_entry.bind("<FocusIn>", self.on_entry_click)
        self.input_entry.bind("<FocusOut>", self.on_focusout)

        # Send Button with pastel styling
        send_button = ttk.Button(
            input_frame, 
            text="Send", 
            command=self.send_message,
            style='TButton'
        )
        send_button.pack(side=tk.LEFT)

        # Status Bar with pastel design
        self.status_var = tk.StringVar(value="Moochie Cat is Ready to Purr!")
        status_bar = ttk.Label(
            self.main_container, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            font=('SF Pro Text', 9),
            background=self.PASTEL_PINK,
            foreground=self.TEXT_COLOR
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))

        # Context Management
        self.context_window = []
        self.MAX_CONTEXT_LENGTH = 5

    def on_entry_click(self, event):
        """Remove placeholder text when entry is clicked"""
        if self.input_entry.get() == "Meow to Moochie Cat...":
            self.input_entry.delete(0, tk.END)
            self.input_entry.config(foreground='black')

    def on_focusout(self, event):
        """Restore placeholder if no text is entered"""
        if self.input_entry.get() == "":
            self.input_entry.insert(0, "Meow to Moochie Cat...")
            self.input_entry.config(foreground='gray')

    def send_message(self, event=None):
        user_message = self.input_entry.get()
        if user_message.strip() and user_message != "Meow to Moochie Cat...":
            # Thread for non-blocking AI response
            threading.Thread(target=self._process_message, args=(user_message,), daemon=True).start()

    def _process_message(self, user_message):
        # Update UI in main thread
        self.master.after(0, self._display_user_message, user_message)
        
        # Status update
        self.master.after(0, self.update_status, "Generating response...")
        
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
        self.chat_history.insert(tk.END, f"Moochie Cat: {response_text}\n\n", "ai")
        self.chat_history.see(tk.END)

    def _display_error(self, error_message):
        self.chat_history.insert(tk.END, f"Error: {error_message}\n\n", "system")
        self.chat_history.see(tk.END)

    def _update_context(self, user_message, response_text):
        context_entry = f"User said: {user_message}\nMoochie Cat responded: {response_text}"
        self.context_window.append(context_entry)
        
        if len(self.context_window) > self.MAX_CONTEXT_LENGTH:
            self.context_window.pop(0)

    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)

    def build_contextual_prompt(self, user_message):
        """Enhanced contextual prompt building with Moochie Cat personality"""
        context_str = "\n".join(self.context_window)
        
        # Retrieve context based on selected context type
        context_type = self.context_var.get()
        context_mapping = {
            "Playful": "Respond with a playful, kitten-like enthusiasm.",
            "Cuddly": "Give warm, comforting responses like a cute cat.",
            "Sassy": "Respond with a touch of cat-like sass and attitude.",
            "Moochie Mode": "Respond as Moochie Cat, with a mix of cute and clever responses."
        }
        
        contextual_prompt = f"""
You are Moochie Cat, an adorable AI companion with a charming personality.
Context Type: {context_type}
Special Instructions: {context_mapping.get(context_type, '')}

Recent Conversation Context:
{context_str}

User's Latest Message: {user_message}

Craft a response that:
1. Directly addresses the user's message
2. Reflects the Moochie Cat personality
3. Adds a touch of feline charm
4. Maintains conversation flow
"""
        return contextual_prompt

    def __del__(self):
        """Close database connection"""
        self.conn.close()

def main():
    root = tk.Tk()
    app = MoochieCatChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()