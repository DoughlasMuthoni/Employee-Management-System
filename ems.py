from customtkinter import *
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from database import get_monthly_attendance, mycursor, conn, connect_database
from tkinter import messagebox, Toplevel, StringVar, filedialog
import database
from datetime import datetime
from datetime import date
from tkinter import END, Text  
from employee_dashboard import get_db_connection
from tkcalendar import Calendar, DateEntry
from datetime import datetime
import pymysql 
from fpdf import FPDF 


def delete_all():
    result = messagebox.askyesno('Confirm', 'Do you really want to delete all the records?')  # Store the return value
    if result:
        database.deleteall_records()



def show_all():
    treeview_data()
    searchEntry.delete(0,END)
    searchBox.set('Search By')

def search_employee(event=None):  # Accepts an optional event argument for bindings
    search_value = searchEntry.get().strip()  # Remove extra spaces
    search_category = searchBox.get().strip()  # Ensure proper selection

    if not search_value:
        messagebox.showerror('Error', 'Enter a value to search')
        return

    if search_category == 'Search By' or not search_category:
        messagebox.showerror('Error', 'Please select a search category')
        return

    try:
        search_data = database.search(search_category, search_value)  # Fetch results

        # Clear existing tree data
        tree.delete(*tree.get_children())

        if search_data:
            for employee in search_data:
                tree.insert('', 'end', values=employee)
        else:
            messagebox.showinfo('No Results', 'No matching records found')

    except Exception as e:
        messagebox.showerror('Error', f'Error while searching: {e}')


def delete_employee():
    selected_item = tree.selection()
    
    if not selected_item:
        messagebox.showerror('Error', 'Select Data to Delete')
    else:
        # Get Id from dictionary entry
        employee_id = entries['Id'].get()

        # Call delete function in database
        database.delete(employee_id)

        # Refresh Treeview and clear fields
        treeview_data()
        clear()

        messagebox.showinfo('Success', 'Data is Deleted')


def update_employee():
    selected_item = tree.selection()

    if not selected_item:
        messagebox.showerror('Error', 'Select an employee to update')
        return

    # ✅ Get Employee ID from the selected row
    employee_id = tree.item(selected_item)['values'][0]

    # ✅ Fetch all updated values from entry fields
    employee_data = {field: entries[field].get().strip() for field in entries}

    # ✅ Convert numeric fields to float & handle empty inputs
    for key in ['Salary', 'Deductions']:
        if not employee_data[key]:  # If empty input
            employee_data[key] = 0  
        else:
            try:
                employee_data[key] = float(employee_data[key])
            except ValueError:
                messagebox.showerror('Error', f'Invalid number format for {key}')
                return

    # ✅ Automatically recalculate NetPay
    new_netpay = employee_data['Salary'] - employee_data['Deductions']

    # ✅ Call the database update function (Step 2 below)
    database.update_employee_data(
        employee_id,  
        employee_data['Name'],
        employee_data['Phone'],
        employee_data['Role'],
        employee_data['Gender'],  
        employee_data['Salary'],
        employee_data['Deductions'],
        new_netpay  # ✅ Updated NetPay
    )

    # ✅ Refresh the TreeView after successful update
    treeview_data()
    messagebox.showinfo('Success', 'Employee details updated successfully!')




def selection(event=None):  # Accepts event argument
    selected_item = tree.selection()  # Get selected row(s)
    
    if selected_item:  # Ensure something is selected
        row = tree.item(selected_item[0])['values']  # Get values from first selected row
        
        # Fields stored in dictionary (order must match the database columns)
        field_names = ['Id', 'Name', 'Phone', 'Role', 'Gender', 'Salary', 'Deductions', 'NetPay']
        
        # Clear and insert new values dynamically
        for index, field in enumerate(field_names):
            if field in ['Role', 'Gender']:  # For dropdown (ComboBox)
                entries[field].set(row[index])
            else:  # For normal Entry fields
                entries[field].delete(0, 'end')
                entries[field].insert(0, row[index])


        


def clear(value=False):
    if value:
        tree.selection_remove(tree.focus())
    for field, entry in entries.items():
        if isinstance(entry, ctk.CTkEntry):  # If it's an entry field, clear text
            entry.delete(0, END)
        elif isinstance(entry, ctk.CTkComboBox):  # If it's a dropdown, reset to default
            if field == "Role":
                entry.set('Web Developer')  
            elif field == "Gender":
                entry.set('Male')  

def treeview_data():
    employees = database.fetch_employees()
    tree.delete(*tree.get_children())
    for employee in employees:
        tree.insert('', END, values = employee)





def add_employee():
    # Retrieve values from entries dictionary
    employee_data = {field: entries[field].get() for field in entries}

    # Check if required fields are empty (EXCLUDE NetPay)
    if any(employee_data[field] == '' for field in ['Id', 'Name', 'Phone', 'Salary', 'Deductions']):
        messagebox.showerror('Error', 'All Fields are Required')
        return  # Stop execution if validation fails

    # Check if ID already exists
    if database.Id_exists(employee_data['Id']):
        messagebox.showerror('Error', 'Id Already Exists!!')
        return  # Stop execution if ID exists

    # Validate ID format
    if not employee_data['Id'].startswith('Emp'):
        messagebox.showerror('Error', 'Invalid Id format! Use "Emp" followed by a number (e.g., "Emp45")')
        return  # Stop execution

    # Insert into database (EXCLUDE NetPay)
    database.insert(
        employee_data['Id'],
        employee_data['Name'],
        employee_data['Phone'],
        employee_data['Role'],
        employee_data['Gender'],  
        employee_data['Salary'],
        employee_data['Deductions']  # ✅ Exclude NetPay
    )

    treeview_data()  # Refresh treeview
    clear()  # Clear input fields
    messagebox.showinfo('Success', 'Employee Added Successfully')




def download_payrolls_as_pdf(payrolls, parent_window):
    """Generate and save the payroll records as a PDF file, ensuring popups stay on top."""
    
    if not payrolls:
        messagebox.showerror("Error", "No payroll records to download.", parent=parent_window)
        return

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "All Generated Payrolls", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    headers = ["ID", "Name", "Role", "Salary", "Deductions", "Net Pay", "Payroll Date"]
    col_widths = [30, 40, 30, 30, 30, 30, 30]

    # Table Header
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align="C")
    pdf.ln()

    pdf.set_font("Arial", size=10)

    # Add payroll data
    for payroll in payrolls:
        for i, value in enumerate(payroll):
            pdf.cell(col_widths[i], 10, str(value), border=1, align="C")
        pdf.ln()

    # Ask user where to save the file (keep dialog on top)
    pdf_filename = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save Payroll Report As",
        parent=parent_window  # ✅ Keep on top
    )

    if not pdf_filename:  
        return  # User canceled save

    pdf.output(pdf_filename)
    
    # Check if file exists
    if os.path.exists(pdf_filename):
        messagebox.showinfo("Success", f"Payrolls downloaded as {pdf_filename}", parent=parent_window)  # ✅ Keep on top
    else:
        messagebox.showerror("Error", "Failed to save the PDF.", parent=parent_window)  # ✅ Keep on top


def refresh_attendance_calendar(employee_id, calendar_widget):
    """Fetch fresh attendance records and update the calendar UI."""

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ✅ Always fetch the latest attendance records
        cursor.execute("SELECT date, status FROM attendance WHERE employee_id = %s", (employee_id,))
        attendance_data = cursor.fetchall()

        # 🗑 Remove old events before adding new ones
        calendar_widget.calevent_remove('all')

        # 🎨 Add fresh attendance records to the calendar
        for date_obj, status in attendance_data:
            if isinstance(date_obj, datetime):
                date_obj = date_obj.date()  # Convert datetime to date
            elif isinstance(date_obj, str):  # Convert string to date
                try:
                    date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
                except ValueError:
                    print(f"❌ Invalid date format: {date_obj}")  # Debugging
                    continue  # Skip invalid entries

            print(f"✅ Adding event: {date_obj} - {status}")  # Debugging

            if status == "Present":
                calendar_widget.calevent_create(date_obj, "Present", tags=("present_tag",))
            elif status == "Absent":
                calendar_widget.calevent_create(date_obj, "Absent", tags=("absent_tag",))

        # ✅ Apply colors to tags
        calendar_widget.tag_config("present_tag", background="green", foreground="white")
        calendar_widget.tag_config("absent_tag", background="red", foreground="white")

        print("🚀 Attendance calendar updated!")

    except pymysql.MySQLError as e:
        messagebox.showerror("Database Error", f"Failed to fetch attendance: {e}")

    finally:
        cursor.close()
        conn.close()  # ✅ Ensure DB connection is closed


def modify_attendance(employee_id, calendar_widget, refresh_calendar_callback):
    """Allows the admin to modify attendance for any day in the month."""

    if not employee_id:
        messagebox.showerror("Error", "No employee selected!")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Create Modify Attendance Window
    modify_window = Toplevel()
    modify_window.title("Modify Attendance")
    modify_window.geometry("400x250")
    modify_window.configure(bg="#1E2749")  # Dark theme

    # 🏷 Title
    CTkLabel(modify_window, text=f"Modify Attendance for Employee ID: {employee_id}", 
             font=("Arial", 14, "bold"), text_color="white").pack(pady=10)

    # 📆 Date Picker
    CTkLabel(modify_window, text="Select Date:", text_color="white").pack()
    date_entry = DateEntry(modify_window, width=20, background="darkblue", 
                           foreground="white", borderwidth=2)
    date_entry.pack(pady=5)

    # 🎯 Attendance Status Dropdown
    CTkLabel(modify_window, text="Attendance Status:", text_color="white").pack()
    status_var = StringVar(value="Absent")  # Default: Absent
    status_dropdown = CTkComboBox(modify_window, values=["Present", "Absent"], 
                                  variable=status_var, state="readonly", width=150)
    status_dropdown.pack(pady=5)

    # ✅ Submit Changes Function
    def submit_changes():
        attendance_date = date_entry.get()
        attendance_status = status_var.get()

        try:
            formatted_date = datetime.strptime(attendance_date, "%m/%d/%y").strftime("%Y-%m-%d")

            cursor.execute("SELECT status FROM attendance WHERE employee_id = %s AND date = %s", 
                           (employee_id, formatted_date))
            existing_record = cursor.fetchone()

            if existing_record:
                cursor.execute("UPDATE attendance SET status=%s WHERE employee_id=%s AND date=%s", 
                               (attendance_status, employee_id, formatted_date))
            else:
                cursor.execute("INSERT INTO attendance (employee_id, date, status) VALUES (%s, %s, %s)", 
                               (employee_id, formatted_date, attendance_status))

            conn.commit()
            messagebox.showinfo("Success", f"Attendance updated for {employee_id} on {formatted_date}")

            modify_window.destroy()  # 🚪 Close window
            refresh_calendar_callback()  # 🚀 Refresh the calendar

        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Failed to update attendance: {e}")

        finally:
            cursor.close()
            conn.close()  # ✅ Ensure DB connection is closed

    # 🚀 Submit Button
    CTkButton(modify_window, text="Update Attendance", command=submit_changes).pack(pady=10)

    # 🚪 Cancel Button
    CTkButton(modify_window, text="Cancel", command=modify_window.destroy).pack()

    modify_window.transient()
    modify_window.grab_set()
    modify_window.focus_force()

    modify_window.mainloop()

def view_attendance_calendar(employee_id):
    """Opens a modern window to display attendance in a calendar format with real-time updates."""

    employee_id = get_selected_employee_id()

    if not employee_id:
        messagebox.showerror("Error", "Please select an employee!")
        return

    # ✅ Check if Employee Exists
    mycursor.execute("SELECT COUNT(*) FROM data WHERE id = %s", (employee_id,))
    if mycursor.fetchone()[0] == 0:
        messagebox.showerror("Error", "Employee ID does not exist!")
        return

    # 🌟 Calendar Window
    calendar_window = ctk.CTkToplevel(window)
    calendar_window.title(f"Attendance Calendar - Employee ID: {employee_id}")
    calendar_window.geometry("500x500")
    calendar_window.resizable(False, False)
    calendar_window.configure(fg_color="white")

    # ✅ Focus Window
    calendar_window.focus_force()

    # 🏷 Title Label
    title_label = ctk.CTkLabel(
        calendar_window, text=f"Attendance Calendar - ID: {employee_id}",
        font=("Arial", 18, "bold"), text_color="cyan", bg_color="white"
    )
    title_label.pack(pady=15)

    # 📆 Enlarged Calendar Widget
    cal = Calendar(
        calendar_window, selectmode="day",
        year=datetime.now().year, month=datetime.now().month,
        font=("Arial", 12),
        borderwidth=2, relief="solid",
        background="white", foreground="black", headersbackground="#f0f0f0",
        normalbackground="white", weekendbackground="#f9f9f9",
        selectbackground="#007BFF", selectforeground="white",
    )
    cal.pack(pady=9, padx=18, expand=True, fill="both")

    # ✅ Function to Fetch and Highlight Attendance
    def update_calendar():
        cal.calevent_remove("all")  # Clear previous events

        attendance_data = get_monthly_attendance(employee_id)

        for date_obj, status in attendance_data:
            if isinstance(date_obj, datetime):
                date_obj = date_obj.date()  # Ensure it's a date object

            if status == "Present":
                cal.calevent_create(date_obj, "Present", tags=("present_tag",))
            else:
                cal.calevent_create(date_obj, "Absent", tags=("absent_tag",))

        # ✅ Apply different colors to Present and Absent dates
        cal.tag_config("present_tag", background="green", foreground="white")
        cal.tag_config("absent_tag", background="red", foreground="white")

    # 🔄 Load Data Initially
    update_calendar()

    modify_attendance_button = ctk.CTkButton(
    calendar_window, text="Modify Attendance",
    font=("Arial", 14, "bold"), fg_color="#007BFF",
    hover_color="#0056b3", text_color="white", corner_radius=10,
    command=lambda: modify_attendance(employee_id, cal, lambda: refresh_attendance_calendar(employee_id, cal))  # ✅ Pass refresh function
    )
    modify_attendance_button.pack(pady=5)

    # 🔄 Refresh Button to Update Attendance
    refresh_button = ctk.CTkButton(
        calendar_window, text="Refresh", command=update_calendar,
        font=("Arial", 14, "bold"), fg_color="#28a745",
        hover_color="#218838", text_color="white", corner_radius=10
    )
    refresh_button.pack(pady=5)

    # 🚪 Close Button (Rounded)
    close_button = ctk.CTkButton(
        calendar_window, text="Close", command=calendar_window.destroy,
        font=("Arial", 14, "bold"), fg_color="#FF3B3F",
        hover_color="#D32F2F", text_color="white", corner_radius=10
    )
    close_button.pack(pady=10)

def generate_payroll():
    employee_id = entries['Id'].get().strip()  # Get Employee ID

    if not employee_id:
        messagebox.showerror("Error", "Please enter Employee ID!")
        return

    if not database.Id_exists(employee_id):  # Check if ID exists
        messagebox.showerror("Error", "Employee ID does not exist!")
        return

    # ✅ Fetch Employee & Payroll Data
    payroll_data = database.calculate_payroll(employee_id)  

    if not payroll_data:
        messagebox.showerror("Error", "Failed to retrieve employee or payroll data!")
        return

    # ✅ Check if Payroll has already been generated
    if payroll_data["payroll_date"] is not None:  # 🔹 Now correctly checking for existing payroll
        messagebox.showwarning("Warning", f"Payroll has already been generated on {payroll_data['payroll_date']}!")
        return

    # 🏷 Extract Employee Details & Payroll Info
    name = payroll_data["name"]
    phone = payroll_data["phone"]
    role = payroll_data["role"]
    gender = payroll_data["gender"]
    salary = payroll_data["salary"]
    deductions = payroll_data["deductions"]
    net_pay = salary - deductions
    payroll_date = date.today()  # ✅ Get current date

    # ✅ Update NetPay and PayrollDate in Database
    database.update_netpay(employee_id, net_pay, payroll_date)

    # ✅ Refresh the TreeView
    treeview_data()

    # 🖥 Display Payroll Details in a Popup Window
    payroll_window = Toplevel(window)
    payroll_window.title("Payroll Details")
    payroll_window.geometry("400x500")
    payroll_window.resizable(False, False) 
    payroll_window.configure(bg="#161C30")

    ctk.CTkLabel(payroll_window, text="📄 Payroll Details", font=("Arial", 16, "bold"), text_color="cyan").pack(pady=5)
    ctk.CTkLabel(payroll_window, text=f"Employee ID: {employee_id}", font=("Arial", 14), text_color="white").pack(pady=3)
    ctk.CTkLabel(payroll_window, text=f"Name: {name}", font=("Arial", 14), text_color="white").pack(pady=3)
    ctk.CTkLabel(payroll_window, text=f"Phone: {phone}", font=("Arial", 14), text_color="white").pack(pady=3)
    ctk.CTkLabel(payroll_window, text=f"Role: {role}", font=("Arial", 14), text_color="white").pack(pady=3)
    ctk.CTkLabel(payroll_window, text=f"Gender: {gender}", font=("Arial", 14), text_color="white").pack(pady=3)
    ctk.CTkLabel(payroll_window, text=f"Salary: Ksh{salary:,.2f}", font=("Arial", 14), text_color="yellow").pack(pady=3)
    ctk.CTkLabel(payroll_window, text=f"Deductions: Ksh{deductions:,.2f}", font=("Arial", 14), text_color="red").pack(pady=3)
    ctk.CTkLabel(payroll_window, text=f"Net Pay: Ksh{net_pay:,.2f}", font=("Arial", 14, "bold"), text_color="green").pack(pady=3)
    ctk.CTkLabel(payroll_window, text=f"Payroll Date: {payroll_date}", font=("Arial", 14), text_color="cyan").pack(pady=3)
    close_button = ctk.CTkButton(payroll_window, text="Close", command=payroll_window.destroy)
    close_button.pack(pady=10)


def download_payrolls_as_pdf(payrolls):
    """Generate and save the payroll records as a PDF file."""
    
    if not payrolls:
        messagebox.showerror("Error", "No payroll records to download.")
        return

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "All Generated Payrolls", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    headers = ["ID", "Name", "Role", "Salary", "Deductions", "Net Pay", "Payroll Date"]
    col_widths = [30, 40, 30, 30, 30, 30, 30]

    # Table Header
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1, align="C")
    pdf.ln()

    pdf.set_font("Arial", size=10)

    # Add payroll data
    for payroll in payrolls:
        for i, value in enumerate(payroll):
            pdf.cell(col_widths[i], 10, str(value), border=1, align="C")
        pdf.ln()

    # Ask user where to save the file
    pdf_filename = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save Payroll Report As"
    )

    if not pdf_filename:  
        return  # User canceled save

    pdf.output(pdf_filename)
    
    # Check if file exists
    if os.path.exists(pdf_filename):
        messagebox.showinfo("Success", f"Payrolls downloaded as {pdf_filename}")
    else:
        messagebox.showerror("Error", "Failed to save the PDF.")
def view_all_payrolls():
    """Fetch and display all generated payrolls with search functionality."""
    global conn, mycursor

    # Ensure database connection is active
    if conn is None or mycursor is None:
        print("❌ No active database connection!")
        messagebox.showerror("Database Error", "Could not connect to the database.")
        return

    try:
        print("✅ Fetching all payrolls...")

        # Fetch all payroll records sorted by ID in ascending order
        mycursor.execute("SELECT Id, Name, Role, Salary, Deductions, NetPay, PayrollDate FROM data WHERE PayrollDate IS NOT NULL ORDER BY Id ASC")
        payrolls = mycursor.fetchall()

        if not payrolls:
            print("ℹ️ No payrolls found in the database.")
            messagebox.showinfo("No Payrolls", "No payrolls have been generated yet.")
            return

        # Create Payroll Window
        payroll_window = tk.Toplevel()
        payroll_window.title("All Generated Payrolls")
        payroll_window.geometry("950x500")

        # Search Frame
        search_frame = tk.Frame(payroll_window)
        search_frame.pack(pady=5, fill="x")

        # Search Label
        search_label = tk.Label(search_frame, text="Search By:", font=("Arial", 12))
        search_label.grid(row=0, column=0, padx=5)

        # Search Dropdown (Filter by ID, Name, Role, Payroll Date)
        search_options = ["ID", "Name", "Role", "Payroll Date"]
        search_by = tk.StringVar(value="ID")
        search_menu = ttk.Combobox(search_frame, textvariable=search_by, values=search_options, state="readonly")
        search_menu.grid(row=0, column=1, padx=5)

        # Search Entry Box
        search_entry = tk.Entry(search_frame, font=("Arial", 12))
        search_entry.grid(row=0, column=2, padx=5)

        # Function to Filter Payroll Data
        def search_payrolls():
            """Filters payrolls based on search criteria."""
            query = search_entry.get().strip().lower()
            filter_type = search_by.get()

            # Clear TreeView
            tree.delete(*tree.get_children())

            # Filter Data
            for payroll in payrolls:
                payroll_dict = {
                    "ID": payroll[0].lower(),
                    "Name": payroll[1].lower(),
                    "Role": payroll[2].lower(),
                    "Payroll Date": str(payroll[6]).lower(),
                }
                if query in payroll_dict[filter_type]:
                    tree.insert("", "end", values=payroll)

        # Search Button
        search_button = tk.Button(search_frame, text="🔍 Search", font=("Arial", 12, "bold"), bg="#007BFF", fg="white",
                                  padx=10, pady=2, command=search_payrolls)
        search_button.grid(row=0, column=3, padx=5)

        # Reset Search Button
        reset_button = tk.Button(search_frame, text="🔄 Reset", font=("Arial", 12, "bold"), bg="gray", fg="white",
                                 padx=10, pady=2, command=lambda: refresh_treeview(tree, payrolls))
        reset_button.grid(row=0, column=4, padx=5)

        # TreeView Frame
        frame = tk.Frame(payroll_window)
        frame.pack(expand=True, fill="both")

        # Scrollbar
        scrollbar = tk.Scrollbar(frame, orient="vertical")

        # TreeView Table
        columns = ("ID", "Name", "Role", "Salary", "Deductions", "Net Pay", "Payroll Date")
        tree = ttk.Treeview(frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)

        # Define Column Headers
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")

        # Insert Payroll Data
        def refresh_treeview(tree_widget, data):
            """Refreshes the treeview with new data."""
            tree_widget.delete(*tree_widget.get_children())
            for record in data:
                tree_widget.insert("", "end", values=record)

        refresh_treeview(tree, payrolls)

        tree.pack(side="left", expand=True, fill="both")
        scrollbar.config(command=tree.yview)
        scrollbar.pack(side="right", fill="y")

        # Buttons
        button_frame = tk.Frame(payroll_window)
        button_frame.pack(pady=10)

        download_button = tk.Button(button_frame, text="📥 Download PDF", font=("Arial", 12, "bold"), bg="#007BFF", fg="white", padx=10, pady=5,
                                    command=lambda: download_payrolls_as_pdf(payrolls, payroll_window))
        download_button.grid(row=0, column=0, padx=5)

        close_button = tk.Button(button_frame, text="❌ Close", font=("Arial", 12, "bold"), bg="red", fg="white", padx=10, pady=5,
                                 command=payroll_window.destroy)
        close_button.grid(row=0, column=1, padx=5)

    except pymysql.MySQLError as e:
        print(f"❌ Database Error: {e}")
        messagebox.showerror("Database Error", f"Failed to retrieve payrolls: {e}")

def view_report(employee_id=None):
    """Displays a formatted report for a selected employee, including attendance."""

    if employee_id is None:
        messagebox.showerror('Error', 'Please select an employee!')
        return

    report_data = database.generate_report(employee_id)  # ✅ Fetch employee report
    attendance_data = get_monthly_attendance(employee_id)  # ✅ Fetch attendance for current month

    if not report_data:
        messagebox.showerror('Error', 'No report found for this employee!')
        return

    # ✅ Extract values from the dictionary
    emp_id = report_data["id"]
    name = report_data["name"]
    phone = report_data["phone"]
    role = report_data["role"]
    gender = report_data["gender"]
    salary = report_data["salary"]
    deductions = report_data["deductions"]
    net_pay = report_data["net_pay"]
    payroll_date = report_data["payroll_date"]

    # 🎯 Count Attendance
    total_present = sum(1 for _, status in attendance_data if status == "Present")
    total_absent = sum(1 for _, status in attendance_data if status == "Absent")
    total_days = total_present + total_absent

   # 🔹 Styled Report Window
    report_window = CTkToplevel(window)
    report_window.title(f"Employee Report - {name}")
    report_window.geometry("500x600")  # Increased size for better visibility
    report_window.resizable(False, False)
    report_window.configure(bg="#1E2749")  # Dark Blue Theme

    # ✅ Ensure window appears on top initially
    report_window.attributes('-topmost', True)
    report_window.after(200, lambda: report_window.attributes('-topmost', False))  # Reset after 200ms

    # ✅ Force focus to prevent opening in the background
    report_window.focus_force()


    # 📄 Scrollable Report Frame
    report_frame = CTkScrollableFrame(report_window, fg_color="#2A2E4F", corner_radius=15)
    report_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # 🎯 Title Label
    title_label = CTkLabel(
        report_frame, text=f"Employee Report: {name}",
        font=('Arial', 18, 'bold'), text_color="cyan"
    )
    title_label.grid(row=0, column=0, columnspan=2, pady=10)

    # 📌 Employee Details
    details = [
        ("Employee ID:", emp_id),
        ("Name:", name),
        ("Phone:", phone),
        ("Role:", role),
        ("Gender:", gender),
        ("Salary:", f"Ksh {salary:,.2f}"),
        ("Deductions:", f"Ksh {deductions:,.2f}"),
        ("Net Pay:", f"Ksh {net_pay:,.2f}"),
        ("Payroll Date:", payroll_date),
    ]

    # ✅ Use Grid Layout for better spacing
    for i, (label, value) in enumerate(details, start=1):
        CTkLabel(report_frame, text=label, font=('Arial', 14, 'bold'), text_color="white", width=200).grid(row=i, column=0, padx=10, pady=5, sticky="w")
        CTkLabel(report_frame, text=value, font=('Arial', 14), text_color="#FFD700").grid(row=i, column=1, padx=10, pady=5, sticky="w")

    # 📊 Attendance Summary
    attendance_label = CTkLabel(report_frame, text="📊 Attendance Summary", font=('Arial', 16, 'bold'), text_color="cyan")
    attendance_label.grid(row=len(details) + 1, column=0, columnspan=2, pady=10)

    attendance_summary = [
        ("Total Days Tracked:", total_days),
        ("Days Present:", total_present),
        ("Days Absent:", total_absent),
    ]

    for i, (label, value) in enumerate(attendance_summary, start=len(details) + 2):
        text_color = "#00FF7F" if label == "Days Present:" else "#FF3B3F"
        CTkLabel(report_frame, text=label, font=('Arial', 14, 'bold'), text_color="white", width=200).grid(row=i, column=0, padx=10, pady=5, sticky="w")
        CTkLabel(report_frame, text=value, font=('Arial', 14), text_color=text_color).grid(row=i, column=1, padx=10, pady=5, sticky="w")

    # 🚪 Close Button (Fixed at the Bottom)
    close_button = CTkButton(
        report_window, text="Close", font=('Arial', 14, 'bold'), corner_radius=10, 
        command=report_window.destroy, fg_color="#FF3B3F", hover_color="#D32F2F"
    )
    close_button.pack(pady=10, side="bottom")


def get_selected_employee_id():
    """Retrieve the selected employee ID from the treeview."""
    selected_item = tree.selection()  # Get selected row(s)

    if not selected_item:
        messagebox.showerror('Error', 'Please select an employee!')
        return None

    return tree.item(selected_item[0], 'values')[0]  # ✅ Extract Employee ID



# Set theme & scaling
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1.2)

# Initialize Window
window = ctk.CTk()
window.geometry('1200x670+100+100')
window.title('Employee Management System')
window.configure(fg_color='#161C30')

# Configure Grid Layout
window.columnconfigure(0, weight=1)  # Left Frame expands
window.columnconfigure(1, weight=2)  # Right Frame gets more space
window.rowconfigure(1, weight=1)  # Main Content expands
window.rowconfigure(2, weight=0)  # Footer fixed at bottom

# 🌟 HEADER (Top Bar)
header_frame = ctk.CTkFrame(window, height=80, fg_color="#1E2749")  # Dark Blue
header_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

header_label = ctk.CTkLabel(header_frame, text="Employee Management System", 
font=("Arial", 20, "bold"), text_color="cyan")
header_label.pack(pady=6)


# 🌟 Left Frame (Employee Input Fields) - Increased Width
leftFrame = CTkFrame(window, fg_color='#1E2749', corner_radius=15, width=450)  # Increased width
leftFrame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
leftFrame.grid_columnconfigure(1, weight=1)  # Allow entries to stretch

# 🎯 Fields List
fields = [
    ("Id", 0),
    ("Name", 1),
    ("Phone", 2),
    ("Role", 3),
    ("Gender", 4),
    ("Salary", 5),
    ("Deductions", 6),
    ("NetPay", 7)
]

entries = {}

# 🔁 Loop Through Fields
for field, row in fields:
    label = CTkLabel(leftFrame, text=field, font=('Arial', 14, 'bold'), text_color='white')
    label.grid(row=row, column=0, padx=20, pady=6, sticky="w")

    if field == "Role":
        role_options = ['Web Developer', 'Business Analyst', 'Network Engineer', 'Data Analyst', 'IT Consultant', 'Technical Writer', 'UI/UX Developer']
        entry = CTkComboBox(leftFrame, values=role_options, width=220, state='readonly')  # Increased width
        entry.set(role_options[0])
    elif field == "Gender":
        gender_options = ['Male', 'Female']
        entry = CTkComboBox(leftFrame, values=gender_options, width=220, state='readonly')  # Increased width
        entry.set(gender_options[0])
    else:
        entry = CTkEntry(leftFrame, font=('Arial', 13, 'bold'), width=220)  # Increased width

    entry.grid(row=row, column=1, padx=15, pady=8, sticky="w")  # Adjusted padding
    entries[field] = entry

# 🌟 Right Frame (Table and Search) - Reduced Width
rightFrame = CTkFrame(window, fg_color='#161C30', corner_radius=15, width=600)  # Reduced width
rightFrame.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)
rightFrame.columnconfigure(0, weight=1)
rightFrame.rowconfigure(1, weight=1)

# 🔍 Search Section
search_options = ['Id', 'Name', 'Phone', 'Role', 'Gender', 'Salary', 'Deductions', 'NetPay']
searchBox = CTkComboBox(rightFrame, values=search_options, state='readonly', width=160)  # Slightly reduced width
searchBox.grid(row=0, column=0, padx=4, pady=8, sticky="w")
searchBox.set('Search By')

searchEntry = CTkEntry(rightFrame, width=160)  # Reduced width
searchEntry.grid(row=0, column=1, padx=4, pady=8)
searchEntry.bind("<Return>", search_employee)  # 🔍 Enable search on Enter key

searchButton = CTkButton(rightFrame, text='Search', width=90, command=search_employee)  # Reduced width
searchButton.grid(row=0, column=2, padx=4, pady=8)

showallButton = CTkButton(rightFrame, text='Show All', width=90, command=show_all)  # Reduced width
showallButton.grid(row=0, column=3, padx=4, pady=8)

# 📋 Table (Treeview)
tree = ttk.Treeview(rightFrame, height=8, columns=('Id', 'Name', 'Phone', 'Role', 'Gender', 'Salary', 'Deductions', 'NetPay'), show='headings')
tree.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=8, pady=8)

# 🎚 Scrollbars (Vertical + Horizontal)
x_scrollbar = ttk.Scrollbar(rightFrame, orient=HORIZONTAL, command=tree.xview)
x_scrollbar.grid(row=2, column=0, columnspan=4, sticky="ew")  # Horizontal scrollbar

y_scrollbar = ttk.Scrollbar(rightFrame, orient=VERTICAL, command=tree.yview)
y_scrollbar.grid(row=1, column=4, sticky="ns")  # Vertical scrollbar

tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

# 🏷 Define Column Headings & Width
columns = ['Id', 'Name', 'Phone', 'Role', 'Gender', 'Salary', 'Deductions', 'NetPay']
column_widths = [90, 140, 110, 180, 90, 130, 130, 130]  # Slightly reduced column widths

style = ttk.Style()
style.configure('Treeview.Heading', font=('Arial', 12, 'bold'))
style.configure('Treeview', font=('Arial', 10, 'bold'), rowheight=24, background='#1E2749', foreground='white')

for col, width in zip(columns, column_widths):
    tree.heading(col, text=col)
    tree.column(col, width=width, anchor="center")

# Ensure rightFrame expands properly
rightFrame.columnconfigure(0, weight=1)
rightFrame.rowconfigure(1, weight=1)



# 🌟 Configure Grid Layout
window.columnconfigure(0, weight=1)  # Left Frame expands
window.columnconfigure(1, weight=2)  # Right Frame gets more space
window.rowconfigure(1, weight=1)  # Main content (left & right frame) expands
window.rowconfigure(2, weight=0)  # Buttons
window.rowconfigure(3, weight=0)  # Extra Buttons
window.rowconfigure(4, weight=0)  # Footer

# 🌟 Button Frame (Row 2)
buttonFrame = CTkFrame(window, fg_color='#161C30')
buttonFrame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5, padx=10)

# 🌟 Configure columns for 3 groups of buttons
for i in range(6):  
    buttonFrame.columnconfigure(i, weight=1)

# 🌟 Row 1: Employee Management
newButton = CTkButton(buttonFrame, text='New Employee', font=('Arial', 15, 'bold'), corner_radius=20,
                      fg_color="#0078D7", text_color="white", hover_color="#005A9E", command=lambda: clear(True))
newButton.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

addButton = CTkButton(buttonFrame, text='Add Employee', font=('Arial', 15, 'bold'), corner_radius=20,
                      fg_color="#28A745", text_color="white", hover_color="#1E7E34", command=add_employee)
addButton.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

updateButton = CTkButton(buttonFrame, text='Update Employee', font=('Arial', 15, 'bold'), corner_radius=20,
                         fg_color="#FF9800", text_color="white", hover_color="#E68900", command=update_employee)
updateButton.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

payrollButton = CTkButton(buttonFrame, text='Generate Payroll', font=('Arial', 15, 'bold'), corner_radius=20,
                          fg_color="#6F42C1", text_color="white", hover_color="#5A32A3", command=generate_payroll)
payrollButton.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

viewPayrollButton = CTkButton(buttonFrame, text='View Payrolls', font=('Arial', 15, 'bold'), corner_radius=20,
                              fg_color="#6F42C1", text_color="white", hover_color="#5A32A3", command=view_all_payrolls)
viewPayrollButton.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

reportButton = CTkButton(buttonFrame, text='View Report', font=('Arial', 15, 'bold'), corner_radius=20,
fg_color="#17A2B8", text_color="white", hover_color="#138496", command=lambda: view_report(get_selected_employee_id()))
reportButton.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

# 🌟 Row 2: Extra Actions (Row 3)
extraButtonFrame = CTkFrame(window, fg_color='#161C30')
extraButtonFrame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5, padx=10)

for i in range(3):
    extraButtonFrame.columnconfigure(i, weight=1)

attendance_calendar_button = CTkButton(extraButtonFrame, text='View Attendance', font=('Arial', 15, 'bold'),
 corner_radius=20, fg_color="#FFC107", text_colorhover_color="#D39E00",
 command=lambda: view_attendance_calendar(get_selected_employee_id()))
attendance_calendar_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

deleteButton = CTkButton(extraButtonFrame, text='Delete Employee', font=('Arial', 15, 'bold'), corner_radius=20,
                         fg_color="#DC3545", text_color="white", hover_color="#B02A37", command=delete_employee)
deleteButton.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

deleteallButton = CTkButton(extraButtonFrame, text='Delete All', font=('Arial', 15, 'bold'), corner_radius=20,
                            fg_color="#DC3545", text_color="white", hover_color="#B02A37", command=delete_all)
deleteallButton.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

# 🌟 Footer (Row 4)
footerFrame = CTkFrame(window, fg_color='#101827', height=40)  # Set fixed height
footerFrame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0))

footerLabel = CTkLabel(footerFrame, text="© 2025 Employee Management System | All Rights Reserved",
                       font=("Arial", 12, "bold"), text_color="white")
footerLabel.pack(pady=5)


treeview_data()

window.bind('<ButtonRelease>', selection)

# Run Application
window.mainloop()
