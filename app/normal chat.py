import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime
import threading
import re

class EnhancedContextAwareChatApp:
    def __init__(self, master):
        # Modern styling
        self.master = master
        master.title("Gemini AI Companion")
        master.geometry("800x700")
        master.configure(bg="#f0f4f8")  # Soft background color

        # Custom theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background="#f0f4f8")
        self.style.configure('TLabel', background="#f0f4f8", font=('Segoe UI', 10))
        self.style.configure('TButton', 
            font=('Segoe UI', 10, 'bold'), 
            background="#4a90e2", 
            foreground="white"
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

    def create_ui(self):
        # Chat History with improved scrolling and styling
        self.chat_history = scrolledtext.ScrolledText(
            self.main_container, 
            wrap=tk.WORD, 
            width=70, 
            height=20,
            font=('Consolas', 10),
            bg="#ffffff", 
            fg="#333333",
            borderwidth=1,
            relief="solid"
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Tag configuration for different message types
        self.chat_history.tag_config('user', foreground="#2c3e50", font=('Segoe UI', 10, 'bold'))
        self.chat_history.tag_config('ai', foreground="#2980b9")
        self.chat_history.tag_config('system', foreground="#7f8c8d", font=('Segoe UI', 9, 'italic'))

        # Input Frame with modern design
        input_frame = ttk.Frame(self.main_container)
        input_frame.pack(fill=tk.X, pady=(10, 0))

        # Context Dropdown
        self.context_var = tk.StringVar(value="Default Context")
        context_dropdown = ttk.Combobox(
            input_frame, 
            textvariable=self.context_var, 
            values=["Default Context", "Professional", "Casual", "Creative"],
            width=15
        )
        context_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        # Input Entry with placeholder
        self.input_entry = ttk.Entry(input_frame, width=50)
        self.input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        self.input_entry.bind("<Return>", self.send_message)
        
        # Placeholder effect
        self.input_entry.insert(0, "Type your message here...")
        self.input_entry.bind("<FocusIn>", self.on_entry_click)
        self.input_entry.bind("<FocusOut>", self.on_focusout)

        # Send Button with modern styling
        send_button = ttk.Button(
            input_frame, 
            text="Send", 
            command=self.send_message,
            style='TButton'
        )
        send_button.pack(side=tk.LEFT)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.main_container, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))

        # Context Management
        self.context_window = []
        self.MAX_CONTEXT_LENGTH = 5

    def on_entry_click(self, event):
        """Remove placeholder text when entry is clicked"""
        if self.input_entry.get() == "Type your message here...":
            self.input_entry.delete(0, tk.END)
            self.input_entry.config(foreground='black')

    def on_focusout(self, event):
        """Restore placeholder if no text is entered"""
        if self.input_entry.get() == "":
            self.input_entry.insert(0, "Type your message here...")
            self.input_entry.config(foreground='gray')

    def send_message(self, event=None):
        user_message = self.input_entry.get()
        if user_message.strip() and user_message != "Type your message here...":
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
        self.chat_history.insert(tk.END, f"Gemini: {response_text}\n\n", "ai")
        self.chat_history.see(tk.END)

    def _display_error(self, error_message):
        self.chat_history.insert(tk.END, f"Error: {error_message}\n\n", "system")
        self.chat_history.see(tk.END)

    def _update_context(self, user_message, response_text):
        context_entry = f"User said: {user_message}\nAI responded: {response_text}"
        self.context_window.append(context_entry)
        
        if len(self.context_window) > self.MAX_CONTEXT_LENGTH:
            self.context_window.pop(0)

    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)

    def build_contextual_prompt(self, user_message):
        """Enhanced contextual prompt building"""
        context_str = "\n".join(self.context_window)
        
        # Retrieve context based on selected context type
        context_type = self.context_var.get()
        context_mapping = {
            "Professional": "Maintain a formal, professional tone.",
            "Casual": "Use a friendly, conversational tone.",
            "Creative": "Respond with creativity and imagination.",
            "Default Context": ""
        }
        
        contextual_prompt = f"""
Context Type: {context_type}
Special Instructions: {context_mapping.get(context_type, '')}

Recent Conversation Context:
{context_str}

User's Latest Message: {user_message}

Please craft a response that:
1. Directly addresses the user's message
2. Reflects the selected context type
3. Maintains conversation coherence
"""
        return contextual_prompt

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

    def __del__(self):
        """Close database connection"""
        self.conn.close()

def main():
    root = tk.Tk()
    app = EnhancedContextAwareChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
