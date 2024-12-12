import tkinter as tk
from tkinter import messagebox
import random
import time
import hashlib
import mysql.connector
from mysql.connector import Error
import re

# Main application class for Typing Speed Testing game
class TypingSpeedTester(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Set up main window dimensions and center it on screen
        window_width = 1200
        window_height = 700
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.resizable(False, False)
        
        self.title("Typing Speed Tester")
        self.configure(bg="peach puff")
        self.level = None
        self.user_logged_in = False
        self.current_user = None
        
        # Initialize database connection
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="typing_speed_db"
            )
            self.cursor = self.connection.cursor(buffered=True)
            
            self.load_records()
            self.create_login_screen()
            
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            messagebox.showerror("Database Error", "Could not connect to database!")
            self.destroy()

    # Database: Safely close database connection
    def close_connection(self):
        if hasattr(self, 'connection') and self.connection:
            self.cursor.close()
            self.connection.close()

    # Security: Hash passwords before storing
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    # Database: Load user records and scores from database
    def load_records(self):
        self.records = {}
        
        if not self.current_user:
            return
            
        try:
            user_query = "SELECT username, password_hash, first_name, last_name, email FROM users WHERE username = %s"
            self.cursor.execute(user_query, (self.current_user,))
            user_data = self.cursor.fetchone()
            
            if user_data:
                self.records[self.current_user] = {
                    "password": user_data[1],
                    "first_name": user_data[2],
                    "last_name": user_data[3],
                    "email": user_data[4],
                    "scores": []
                }
                
                records_query = "SELECT wpm FROM typing_records WHERE username = %s ORDER BY timestamp DESC"
                self.cursor.execute(records_query, (self.current_user,))
                scores = self.cursor.fetchall()
                
                if scores:
                    self.records[self.current_user]["scores"] = [score[0] for score in scores]
        
        except Error as e:
            print(f"Error loading records: {e}")
            self.records = {}

    # Database: Save typing test results
    def save_records(self, wpm):
        try:
            query = "INSERT INTO typing_records (username, wpm) VALUES (%s, %s)"
            self.cursor.execute(query, (self.current_user, wpm))
            self.connection.commit()
            print(f"Record saved: {self.current_user} - {wpm} WPM")
        except Error as e:
            print(f"Error saving record: {e}")
            self.connection.rollback()

    # UI: Create initial login interface
    def create_login_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Login or Register", font=("Arial", 24), bg="peach puff", fg="black").pack(pady=20)

        tk.Label(self, text="Username:", font=("Arial", 14), bg="peach puff", fg="black").pack()
        self.username_entry = tk.Entry(self, font=("Arial", 14))
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Password:", font=("Arial", 14), bg="peach puff", fg="black").pack()
        self.password_entry = tk.Entry(self, font=("Arial", 14), show="*")
        self.password_entry.pack(pady=5)

        button_frame = tk.Frame(self, bg="peach puff")
        button_frame.pack(pady=(30, 10))

        button_width = 12
        tk.Button(button_frame, text="Login", font=("Arial", 14), width=button_width,
                 command=self.validate_login).pack(pady=8)
        tk.Button(button_frame, text="Register", font=("Arial", 14), width=button_width,
                 command=self.create_registration_screen).pack(pady=8)

    # UI: Create registration interface for new users
    def create_registration_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Register New User", font=("Arial", 24), bg="peach puff", fg="black").pack(pady=20)

        tk.Label(self, text="First Name:", font=("Arial", 14), bg="peach puff", fg="black").pack()
        self.first_name_entry = tk.Entry(self, font=("Arial", 14))
        self.first_name_entry.pack(pady=5)

        tk.Label(self, text="Last Name:", font=("Arial", 14), bg="peach puff", fg="black").pack()
        self.last_name_entry = tk.Entry(self, font=("Arial", 14))
        self.last_name_entry.pack(pady=5)

        tk.Label(self, text="Email:", font=("Arial", 14), bg="peach puff", fg="black").pack()
        self.email_entry = tk.Entry(self, font=("Arial", 14))
        self.email_entry.pack(pady=5)

        tk.Label(self, text="Username:", font=("Arial", 14), bg="peach puff", fg="black").pack()
        self.reg_username_entry = tk.Entry(self, font=("Arial", 14))
        self.reg_username_entry.pack(pady=5)

        tk.Label(self, text="Password:", font=("Arial", 14), bg="peach puff", fg="black").pack()
        self.reg_password_entry = tk.Entry(self, font=("Arial", 14), show="*")
        self.reg_password_entry.pack(pady=5)

        button_frame = tk.Frame(self, bg="peach puff")
        button_frame.pack(pady=(30, 10))

        button_width = 12
        tk.Button(button_frame, text="Register", font=("Arial", 14), width=button_width,
                 command=self.register_user).pack(pady=8)
        tk.Button(button_frame, text="Back", font=("Arial", 14), width=button_width,
                 command=self.create_login_screen).pack(pady=8)

    # Authentication: Validate user login credentials
    def validate_login(self):
        username = self.username_entry.get()
        password = self.hash_password(self.password_entry.get())

        try:
            query = "SELECT username, password_hash, first_name, last_name, email FROM users WHERE username = %s AND password_hash = %s"
            self.cursor.execute(query, (username, password))
            user_data = self.cursor.fetchone()

            if user_data:
                self.user_logged_in = True
                self.current_user = username
                self.records[username] = {
                    "password": user_data[1],
                    "first_name": user_data[2],
                    "last_name": user_data[3],
                    "email": user_data[4],
                    "scores": []
                }
                self.create_level_selection()
            else:
                messagebox.showerror("Error", "Invalid username or password! Please try again.")

        except Error as e:
            print(f"Error during login: {e}")
            messagebox.showerror("Error", "Login failed due to database error!")

    # Validation: Check email format using regex
    def validate_email(self, email):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    # User Management: Register new user with validation
    def register_user(self):
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        first_name = self.first_name_entry.get()
        last_name = self.last_name_entry.get()
        email = self.email_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password are required!")
            return

        if not self.validate_email(email):
            messagebox.showerror("Error", "Please enter a valid email address!")
            return

        try:
            check_query = "SELECT username FROM users WHERE username = %s"
            self.cursor.execute(check_query, (username,))
            if self.cursor.fetchone():
                messagebox.showerror("Error", "Username already exists!")
                return

            query = """
            INSERT INTO users (username, password_hash, first_name, last_name, email)
            VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (username, self.hash_password(password), first_name, last_name, email))
            self.connection.commit()
            
            self.records[username] = {
                "password": self.hash_password(password),
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "scores": []
            }
            
            messagebox.showinfo("Success", "Registration successful! You can now log in.")
            self.create_login_screen()

        except Error as e:
            print(f"Error saving user to database: {e}")
            self.connection.rollback()
            messagebox.showerror("Error", "Registration failed!")

    def create_level_selection(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text=f"Welcome, {self.records[self.current_user]['first_name']} {self.records[self.current_user]['last_name']}!", 
                font=("Arial", 20), bg="peach puff", fg="black").pack(pady=20)
        tk.Label(self, text="Choose Difficulty Level", font=("Arial", 20), 
                bg="peach puff", fg="black").pack(pady=20)

        button_frame = tk.Frame(self, bg="peach puff")
        button_frame.pack(pady=10)

        button_width = 15
        button_pady = 10

        tk.Button(button_frame, text="Easy", font=("Arial", 14), 
                 width=button_width, command=lambda: self.start_game("easy")).pack(pady=button_pady)
        tk.Button(button_frame, text="Medium", font=("Arial", 14), 
                 width=button_width, command=lambda: self.start_game("medium")).pack(pady=button_pady)
        tk.Button(button_frame, text="Hard", font=("Arial", 14), 
                 width=button_width, command=lambda: self.start_game("hard")).pack(pady=button_pady)
        tk.Button(button_frame, text="View Records", font=("Arial", 14), 
                 width=button_width, command=self.view_records).pack(pady=button_pady)
        tk.Button(button_frame, text="Logout", font=("Arial", 14), 
                 width=button_width, command=self.create_login_screen).pack(pady=button_pady)

    # Game Logic: Initialize game with selected difficulty level
    def start_game(self, level):
        self.level = level
        # Define text samples for different difficulty levels
        self.words = {
            "easy": [
                # Simple sentences with basic vocabulary
                "The cat sat on the table with an apple.",
                "A dog chased a ball near the book.",
                "The sun shines brightly over the tree.",
                "A small bird flew above the house.", 
                "She wrote her name with a pen on the paper.", 
                "The car is parked next to the door.", 
                "A cloud floated across the blue sky.", 
                "The lamp lit the corner of the room.", 
                "He held a key in his hand by the window.", 
                "The fish swam quickly in the water."
            ],

            "medium": [
                # Programming-related sentences with moderate complexity
                "Programming in Python is fun and helps solve problems.", 
                "The keyboard error caused a need to debug the code.",
                "An efficient algorithm improves the performance of tasks.",
                "The binary system is essential in computer operations.", 
                "Understanding inheritance is crucial in object-oriented design.", 
                "A good interface allows for seamless user interaction.",
                "Exception handling prevents program crashes.",
                "A compiler translates code into a readable machine format.",
                "Recursion is a powerful tool in problem-solving.",
                "Mastering syntax is key to becoming a proficient developer."],

            "hard": [
                # Complex technical sentences with advanced vocabulary
                "Synchronization issues can occur during multithreading tasks.",
                "Proper encapsulation and initialization are key in object-oriented design.",
                "Concurrency can greatly improve system efficiency.",
                "Asynchronous operations reduce latency in high-performance applications.",
                "Virtualization is widely used in cloud computing technologies.",
                "Understanding serialization helps in transferring data efficiently.",
                "Refactoring code improves its maintainability and readability.",
                "Microservices allow for a modular architecture in development.",
                "Advanced cryptography ensures data security during transmission.",
                "Containerization aids in creating portable application environments."
            ]
        }
        self.create_game_ui()

    # Game UI: Create the main typing interface
    def create_game_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        game_frame = tk.Frame(self, bg="peach puff")
        game_frame.pack(expand=True, fill="both", padx=20, pady=20)

        word_frame = tk.Frame(game_frame, bg="peach puff", padx=10, pady=10)
        word_frame.pack(fill="x", pady=(0, 20))
        
        self.word_label = tk.Label(word_frame, text="", font=("Arial", 24), 
                                  bg="peach puff", fg="black",  
                                  wraplength=450)
        self.word_label.pack(pady=10)

        typing_frame = tk.Frame(game_frame, bg="peach puff", padx=10, pady=10)
        typing_frame.pack(fill="x")
        
        self.entry = tk.Text(typing_frame, font=("Arial", 16), height=4, 
                            width=40, wrap=tk.WORD,
                            bg="white",  
                            fg="black",  
                            insertbackground="black")  
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self.check_word)

        self.result_label = tk.Label(game_frame, text="", font=("Arial", 16), 
                                   bg="peach puff", fg="black")  
        self.result_label.pack(pady=20)

        back_button = tk.Button(game_frame, text="Back", font=("Arial", 14), 
                              command=self.create_level_selection,
                              bg="red",
                              fg="black",
                              activebackground="#8B0000")  
        back_button.pack(pady=10)

        self.get_new_word()

    # Game Logic: Select and display random sentence for typing
    def get_new_word(self):
        self.current_word = random.choice(self.words[self.level])
        self.word_label.config(text=self.current_word)
        self.entry.delete("1.0", tk.END)
        self.start_time = time.time()

    def save_wpm_to_db(self, username, wpm, accuracy):
        try:
            query = "INSERT INTO typing_records (username, wpm, accuracy, difficulty) VALUES (%s, %s, %s, %s)"
            self.cursor.execute(query, (username, wpm, accuracy, self.level))
            self.connection.commit()
            print(f"Record saved: {username} - {wpm} WPM - {accuracy:.1f}% - {self.level}")
        except Exception as e:
            print(f"Error saving to database: {e}")
            self.connection.rollback()

    # Performance Tracking: Calculate and save typing metrics
    def check_word(self, event):
        typed_word = self.entry.get("1.0", "end-1c").strip()
        
        # Calculate accuracy by comparing characters
        def calculate_accuracy(s1, s2):
            matches = sum(1 for a, b in zip(s1, s2) if a == b)
            max_len = max(len(s1), len(s2))
            return (matches / max_len) * 100 if max_len > 0 else 0

        accuracy = calculate_accuracy(typed_word, self.current_word)
        elapsed_time = time.time() - self.start_time
        
        # Calculate Words Per Minute (WPM)
        char_count = len(typed_word)
        words = char_count / 5  # Standard: 5 characters = 1 word
        minutes = elapsed_time / 60
        wpm = int(words / minutes)
        
        result_text = f"Speed: {wpm} WPM\nAccuracy: {accuracy:.1f}%"
        text_color = "#333333" if typed_word == self.current_word else "red"

        self.result_label.config(text=result_text, fg=text_color)

        self.save_wpm_to_db(self.current_user, wpm, accuracy)

        self.entry.delete("1.0", tk.END)
        self.after(1500, self.get_new_word())
        return "break"

    # Statistics: Display user's typing history
    def view_records(self):
        for widget in self.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self, bg="peach puff")
        main_frame.pack(expand=True, fill="both")

        title_label = tk.Label(main_frame, text="Player Records", font=("Arial", 24), 
                             bg="peach puff", fg="black")
        title_label.pack(pady=20)

        container_frame = tk.Frame(main_frame, bg="peach puff")
        container_frame.pack(expand=True, fill="both", padx=20)

        canvas = tk.Canvas(container_frame, bg="peach puff", highlightthickness=0)
        scrollbar = tk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        records_frame = tk.Frame(canvas, bg="peach puff")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        try:
            count_query = "SELECT COUNT(*) FROM typing_records WHERE username = %s"
            self.cursor.execute(count_query, (self.current_user,))
            total_records = self.cursor.fetchone()[0]

            query = "SELECT wpm, accuracy, timestamp, id, difficulty FROM typing_records WHERE username = %s ORDER BY timestamp DESC"
            self.cursor.execute(query, (self.current_user,))
            records = self.cursor.fetchall()

            if records:
                col_widths = [8, 8, 10, 10, 20, 8]
                headers = ["Game", "WPM", "Accuracy", "Level", "Date & Time", "Action"]

                for col, (text, width) in enumerate(zip(headers, col_widths)):
                    tk.Label(records_frame, text=text, font=("Arial", 16, "bold"),
                           bg="peach puff", width=width).grid(row=0, column=col, padx=5, pady=5)

                for row, record in enumerate(records, start=1):
                    wpm, accuracy, timestamp, record_id, difficulty = record
                    record_number = total_records - row + 1
                    
                    tk.Label(records_frame, text=f"#{record_number}", font=("Arial", 16),
                           bg="peach puff", width=col_widths[0]).grid(row=row, column=0, padx=5, pady=2)
                    tk.Label(records_frame, text=str(wpm), font=("Arial", 16),
                           bg="peach puff", width=col_widths[1]).grid(row=row, column=1, padx=5, pady=2)
                    tk.Label(records_frame, text=f"{accuracy:.1f}%", font=("Arial", 16),
                           bg="peach puff", width=col_widths[2]).grid(row=row, column=2, padx=5, pady=2)
                    tk.Label(records_frame, text=difficulty.title(), font=("Arial", 16),
                           bg="peach puff", width=col_widths[3]).grid(row=row, column=3, padx=5, pady=2)
                    tk.Label(records_frame, text=timestamp.strftime("%Y-%m-%d %H:%M:%S"), font=("Arial", 16),
                           bg="peach puff", width=col_widths[4]).grid(row=row, column=4, padx=5, pady=2)
                    tk.Button(records_frame, text="Delete", font=("Arial", 14),
                            command=lambda r_id=record_id: self.delete_record(r_id),
                            bg="red", fg="black", width=col_widths[5]).grid(row=row, column=5, padx=5, pady=2)

            else:
                tk.Label(records_frame, text="No records yet.", 
                        font=("Arial", 16), bg="peach puff").pack(pady=50)

        except Error as e:
            print(f"Error fetching records: {e}")
            tk.Label(records_frame, text="Error fetching records.", 
                    font=("Arial", 16), bg="peach puff").pack(pady=50)

        canvas.create_window((0, 0), window=records_frame, anchor="nw")
        records_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        button_container = tk.Frame(main_frame, bg="peach puff")
        button_container.pack(fill="x", pady=20)

        back_button = tk.Button(button_container, text="Back", font=("Arial", 16),
                             command=self.create_level_selection,
                             bg="red", fg="black",
                             activebackground="#8B0000",
                             width=20)
        back_button.pack(expand=True)

        def _on_destroy(event):
            canvas.unbind_all("<MouseWheel>")
        main_frame.bind("<Destroy>", _on_destroy)

    # Record Management: Delete individual typing records
    def delete_record(self, record_id):
        try:
            query = "DELETE FROM typing_records WHERE id = %s"
            self.cursor.execute(query, (record_id,))
            self.connection.commit()
            print(f"Record with ID {record_id} deleted.")

            messagebox.showinfo("Success", "Record deleted successfully!")

            self.view_records()

        except Error as e:
            print(f"Error deleting record: {e}")
            messagebox.showerror("Error", "Failed to delete the record.")
            self.connection.rollback()

    # Database: Safely close database connection
    def close_connection(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()

# Application entry point
if __name__ == "__main__":
    app = TypingSpeedTester()
    app.mainloop()