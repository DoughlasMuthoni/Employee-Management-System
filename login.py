from customtkinter import *
from PIL import Image, ImageTk
from tkinter import messagebox, simpledialog
import customtkinter as ctk
from authentication import admin_login, get_db_connection, verify_password,  hash_password  # Import admin authentication
import bcrypt
from employee_dashboard import EmployeeDashboard  # Import the Employee Dashboard class
def login():
    employee_id = usernameEntry.get()
    password = passwordEntry.get()
    
    if not employee_id or not password:
        messagebox.showerror('Error', 'All fields are required')
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check in users table for Admins
    cursor.execute("SELECT role, password_hash FROM users WHERE employee_id = %s", (employee_id,))
    user_data = cursor.fetchone()
    
    if user_data:
        role, stored_hash = user_data
        if verify_password(password, stored_hash):
            messagebox.showinfo('Success', 'Login successful!')
            root.destroy()  # Close login window
            if role == 'Admin':
                import ems  # Load Admin Panel
            else:
                dashboard = EmployeeDashboard(employee_id)  # Load Employee Dashboard
                dashboard.mainloop()  # Start the GUI loop
        else:
            messagebox.showerror('Error', 'Wrong Credentials')
    else:
        # Check in data table for Employees
        cursor.execute("SELECT phone FROM data WHERE id = %s", (employee_id,))
        employee_data = cursor.fetchone()
        if employee_data and password == employee_data[0]:  # Compare password with phone
            messagebox.showinfo('Success', 'Login successful!')
            root.destroy()  # Close login window
            dashboard = EmployeeDashboard(employee_id)  # Load Employee Dashboard
            dashboard.mainloop()  # Start the GUI loop
        else:
            messagebox.showerror('Error', 'User not found or incorrect password')
    
    conn.close()

def toggle_password():
    if passwordEntry.cget("show") == "*":
        passwordEntry.configure(show="")  # Show password
        toggle_button.configure(text="👁️")  # Change icon
    else:
        passwordEntry.configure(show="*")  # Hide password
        toggle_button.configure(text="🙈")  # Change icon

def forgot_password():
    forgot_window = ctk.CTkToplevel(root)
    forgot_window.title("Forgot Password")
    forgot_window.geometry("350x300")
    forgot_window.resizable(False, False)
    forgot_window.configure(bg="#FFFFFF")
    
    forgot_window.transient(root)  # Make it a child of root
    forgot_window.grab_set()  # Block interactions with the main window until closed
    forgot_window.focus_set()  # Bring it to the front
    
    CTkLabel(forgot_window, text="Reset Password", font=("Arial", 18, "bold"), text_color="#0056b3").pack(pady=20)

    # Input fields for ID and Phone Number
    id_entry = CTkEntry(forgot_window, placeholder_text='Enter Employee ID', width=250, height=40, corner_radius=10)
    id_entry.pack(pady=10)

    phone_entry = CTkEntry(forgot_window, placeholder_text='Enter Registered Phone', width=250, height=40, corner_radius=10)
    phone_entry.pack(pady=10)

    # Reset Password Button - Calls `reset_password()`
    reset_button = CTkButton(forgot_window, text='Reset Password', width=250, height=40, corner_radius=10, 
                             command=lambda: reset_password(id_entry.get(), phone_entry.get(), forgot_window))
    reset_button.pack(pady=20)


def reset_password(employee_id, phone_number, forgot_window):
    if not employee_id or not phone_number:
        messagebox.showerror("Error", "Both fields are required")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify ID and Phone Number
    cursor.execute("SELECT id FROM data WHERE id = %s AND phone = %s", (employee_id, phone_number))
    user = cursor.fetchone()

    if user:
        # Prompt user to enter a new password
        new_password = simpledialog.askstring("Reset Password", "Enter New Password:")
        if new_password:
            # Store the new password as plain text (Not Recommended for Security)
            cursor.execute("UPDATE data SET phone = %s WHERE id = %s", (new_password, employee_id))
            conn.commit()
            
            messagebox.showinfo("Success", "Password reset successfully!")
            forgot_window.destroy()  # Close the reset window
        else:
            messagebox.showwarning("Cancelled", "Password reset cancelled")
    else:
        messagebox.showerror("Error", "Invalid Employee ID or Phone Number")
    
    conn.close()



def resize_bg(event=None):
    global bg_image, bg_photo
    bg_image = Image.open('mwala_img4.jpg')
    bg_image = bg_image.resize((root.winfo_width(), root.winfo_height()), Image.LANCZOS)  # Resize dynamically
    bg_photo = ImageTk.PhotoImage(bg_image)
    canvas.itemconfig(bg_item, image=bg_photo)

# Set theme & scaling
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1.2)

# Main window
root = ctk.CTk()
root.geometry('800x500')
root.title('Login')

# Create Canvas for Background Image
canvas = ctk.CTkCanvas(root, highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Load and Place Background Image
bg_image = Image.open('mwala_img4.jpg')
bg_photo = ImageTk.PhotoImage(bg_image)
bg_item = canvas.create_image(0, 0, anchor="nw", image=bg_photo)

# Centered Login Frame
frame = ctk.CTkFrame(root, corner_radius=20, fg_color="#FFFFFF")
frame.place(relx=0.5, rely=0.5, anchor=CENTER)

# Heading Label
headinglabel = ctk.CTkLabel(frame, text='Employee Management System', 
                            font=('Goudy Old Style', 24, 'bold'), 
                            text_color='#0056b3')
headinglabel.pack(pady=(30, 15), padx=20)

# Username Entry
usernameEntry = ctk.CTkEntry(frame, placeholder_text='Enter Username', 
                             width=250, height=40, corner_radius=10)
usernameEntry.pack(pady=10)

# Password Entry with Toggle Button
password_frame = ctk.CTkFrame(frame, fg_color="transparent")
password_frame.pack(pady=10)
passwordEntry = ctk.CTkEntry(password_frame, placeholder_text='Enter Password', 
                             show='*', width=220, height=40, corner_radius=10)
passwordEntry.pack(side='left')
toggle_button = ctk.CTkButton(password_frame, text='👁', width=30, command=toggle_password)
toggle_button.pack(side='right', padx=5)

# Login Button
loginButton = ctk.CTkButton(frame, text='Login', cursor='hand2', 
                            width=250, height=40, corner_radius=10, 
                            command=login)
loginButton.pack(pady=10)

# Forgot Password Button
forgotPasswordButton = ctk.CTkButton(frame, text='Forgot Password?', fg_color="transparent", text_color="red", 
                                     cursor='hand2', command=forgot_password)
forgotPasswordButton.pack(pady=5)

# Bind Window Resize Event to Update Background
root.bind("<Configure>", resize_bg)

# Run the application
root.mainloop()
