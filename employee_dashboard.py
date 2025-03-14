from customtkinter import *
from tkinter import messagebox, Toplevel
import pymysql
from customtkinter import CTk, CTkLabel, CTkFrame, CTkButton

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from tkinter import filedialog
from datetime import date
from tkinter import END, Text  
from tkcalendar import Calendar
from datetime import datetime
# Database Connection
def get_db_connection():
    return pymysql.connect(host='localhost', user='root', password='mwalatvc', port=3306, database='employee_data')

# Employee Dashboard Window
class EmployeeDashboard(CTk):
    def __init__(self, employee_id):
        super().__init__()
        self.employee_id = employee_id
        self.title("Employee Dashboard")
        self.geometry("600x650+100+100")
        self.configure(bg="#1E1E2F")  # Dark background

        # Header Label
        self.header = CTkLabel(self, text="👨‍💼 Employee Dashboard", font=("Arial", 22, "bold"), text_color="#00A3E0")
        self.header.pack(pady=10)

        # Scrollable Main Frame
        self.scroll_frame = CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Personal Details Frame
        self.details_frame = CTkFrame(self.scroll_frame, fg_color="#2A2D3E", corner_radius=15)
        self.details_frame.pack(fill="x", padx=15, pady=10)

        self.details_label = CTkLabel(self.details_frame, text="📋 Personal Details", font=("Arial", 16, "bold"), text_color="cyan")
        self.details_label.pack(pady=5)
        self.details_text = CTkLabel(self.details_frame, text="", font=("Arial", 14), text_color="white")
        self.details_text.pack(pady=10, padx=10)

        # Attendance Button
        self.attendance_button = CTkButton(self.scroll_frame, text="✅ Mark Attendance", command=self.mark_attendance, fg_color="#28A745", hover_color="#218838", text_color="white")
        self.attendance_button.pack(pady=10, padx=20, fill="x")

        # View Attendance Calendar Button
        self.calendar_button = CTkButton(
            self.scroll_frame, text="📅 View Attendance Calendar", command=self.view_attendance_calendar,
            fg_color="#17A2B8", hover_color="#138496", text_color="white"
        )
        self.calendar_button.pack(pady=10, padx=20, fill="x")

        # Payroll Details Frame
        self.payroll_frame = CTkFrame(self.scroll_frame, fg_color="#2A2D3E", corner_radius=15)
        self.payroll_frame.pack(fill="x", padx=15, pady=10)

        self.payroll_label = CTkLabel(self.payroll_frame, text="💰 Payroll Details", font=("Arial", 16, "bold"), text_color="cyan")
        self.payroll_label.pack(pady=5)
        self.payroll_text = CTkLabel(self.payroll_frame, text="", font=("Arial", 14), text_color="white")
        self.payroll_text.pack(pady=10, padx=10)

        # View Report Button
        self.report_button = CTkButton(self.scroll_frame, text="📊 View Report", command=self.view_report, fg_color="#FFC107", hover_color="#E0A800", text_color="black")
        self.report_button.pack(pady=10, padx=20, fill="x")

        # View Payroll Button
        self.payroll_button = CTkButton(self.scroll_frame, text="💵 View Payroll", command=self.view_payroll, fg_color="#007BFF", hover_color="#0056b3", text_color="white")
        self.payroll_button.pack(pady=10, padx=20, fill="x")

        # Footer (Fixed at the Bottom)
        self.footer = CTkLabel(self, text="© 2025 Employee Management System | All Rights Reserved", font=("Arial", 12), text_color="red")
        self.footer.pack(side="bottom", pady=10)

        # Fetch and Display Employee Details
        self.load_employee_data()

    
    def load_employee_data(self):
        conn = get_db_connection()
        cursor = conn.cursor()
    
    # Fetch personal details and payroll details from 'data' table
        cursor.execute("SELECT id, name, phone, role, gender, salary, deductions, NetPay FROM data WHERE id = %s", (self.employee_id,))
        employee = cursor.fetchone()
        
        if employee:
            emp_id, name, phone, role, gender, salary, deductions, net_pay = employee
        
        self.details_text.configure(
            text=(
                f"ID:  {emp_id}\n\n"
                f"Name:  {name}\n\n"
                f"Phone:  {phone}\n\n"
                f"Role:  {role}\n\n"
                f"Gender:  {gender}\n\n"
                f"Salary: Ksh {salary}\n\n"
                f"Deductions:  Ksh {deductions:,.2f}\n\n"
                f"Net Pay:  Ksh {net_pay:,.2f}"
            ),
            font=("Arial", 14),
            text_color="white"
        )
        
        self.payroll_text.configure(
            text=(
                f"Salary:  Ksh {salary:,.2f}\n\n"             
            ),
            font=("Arial", 14)
        )
        # Apply colors
        self.payroll_text.configure(
            text_color="yellow" if "Salary" in self.payroll_text.cget("text") else "white"
        )
        
        # Additional colored labels
        self.deductions_label = CTkLabel(self.payroll_frame, text=f"Deductions: Ksh {deductions:,.2f}", font=("Arial", 14), text_color="red")
        self.deductions_label.pack(pady=2)
        
        self.netpay_label = CTkLabel(self.payroll_frame, text=f"Net Pay: Ksh {net_pay:,.2f}", font=("Arial", 14, "bold"), text_color="green")
        self.netpay_label.pack(pady=2)
    
        conn.close()

    def mark_attendance(self):
        """Allows employees to mark attendance as 'Present' or 'Absent' once per day."""

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the employee has already marked attendance for today
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE employee_id = %s AND date = CURDATE()", (self.employee_id,))
        already_marked = cursor.fetchone()[0]

        if already_marked > 0:
            messagebox.showwarning("Warning", "You have already marked attendance for today!")
            conn.close()
            return

        # Create Attendance Selection Window
        attendance_window = Toplevel(self)
        attendance_window.title("Mark Attendance")
        attendance_window.geometry("350x200")
        attendance_window.configure(bg="#1E2749")  # Match theme

        # Title Label
        CTkLabel(attendance_window, text="Mark Attendance", font=("Arial", 16, "bold"), text_color="white").pack(pady=10)

        # Attendance Options
        attendance_status = StringVar(value="Present")
        options = ["Present", "Absent"]

        status_dropdown = CTkComboBox(attendance_window, values=options, variable=attendance_status, state="readonly", width=150)
        status_dropdown.pack(pady=5)

    # ✅ Submit Attendance Function
        def submit_attendance():
            status = attendance_status.get()

            try:
                cursor.execute(
                    "INSERT INTO attendance (employee_id, date, status) VALUES (%s, CURDATE(), %s)",
                    (self.employee_id, status)
                )
                conn.commit()
                messagebox.showinfo("Success", f"Attendance marked as {status}!")
            except pymysql.MySQLError as e:
                messagebox.showerror("Database Error", f"Failed to mark attendance: {e}")

            conn.close()
            attendance_window.destroy()  # Close window after marking attendance

        # 🚀 Submit Button
        CTkButton(attendance_window, text="Submit", command=submit_attendance).pack(pady=10)

        # 🚪 Cancel Button
        CTkButton(attendance_window, text="Cancel", command=attendance_window.destroy).pack()

    def view_attendance_calendar(self):
        """Opens a modern window to display attendance in a calendar format."""

        employee_id = self.employee_id  # ✅ Get the employee's ID directly

        if not employee_id:
            messagebox.showerror("Error", "Employee ID is missing!")
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM data WHERE id = %s", (employee_id,))
        if cursor.fetchone()[0] == 0:
            messagebox.showerror("Error", "Employee ID does not exist!")
            conn.close()
            return

       # 🌟 Calendar Window (White Background)
        calendar_window = CTkToplevel(self)
        calendar_window.title(f"Attendance Calendar - Employee ID: {employee_id}")
        calendar_window.geometry("500x450")  # Bigger window
        calendar_window.resizable(False, False)
        calendar_window.configure(fg_color="white")  # White background

        # ✅ Attach to Main Window
        calendar_window.transient(self)  # Keep it above the main window
        calendar_window.grab_set()  # Block interactions with the main window until closed
        calendar_window.focus_force()  # Force focus



        # 🏷 Title Label
        title_label = CTkLabel(
            calendar_window, text=f"Attendance Calendar - ID: {employee_id}",
            font=("Arial", 18, "bold"), text_color="cyan", bg_color="white"
        )
        title_label.pack(pady=15)

        # 📆 Enlarged Calendar Widget
        cal = Calendar(
            calendar_window, selectmode="day",
            year=datetime.now().year, month=datetime.now().month,
            font=("Arial", 12),  # Larger text
            borderwidth=2, relief="solid",
            background="white", foreground="black", headersbackground="#f0f0f0",
            normalbackground="white", weekendbackground="#f9f9f9",
            selectbackground="#007BFF", selectforeground="white",
        )
        cal.pack(pady=9, padx=18, expand=True, fill="both")  # Fully expand

        # 🗓 Fetch Attendance Records
        cursor.execute("SELECT date, status FROM attendance WHERE employee_id = %s", (employee_id,))
        attendance_data = cursor.fetchall()
        conn.close()

        # 🎨 Highlight Attendance in the Calendar
        for date_obj, status in attendance_data:  
            if isinstance(date_obj, datetime):  
                date_obj = date_obj.date()  # Ensure it's a date object

            if status == "Present":
                cal.calevent_create(date_obj, "Present", "present_tag")
            elif status == "Absent":
                cal.calevent_create(date_obj, "Absent", "absent_tag")

        # Apply colors to tags
        cal.tag_config("present_tag", background="green", foreground="white")  # ✅ Green for Present
        cal.tag_config("absent_tag", background="red", foreground="white")      # ❌ Red for Absent



        # 🚪 Close Button (Rounded)
        close_button = CTkButton(
            calendar_window, text="Close", command=calendar_window.destroy,
            font=("Arial", 14, "bold"), fg_color="#FF3B3F", hover_color="#D32F2F",
            text_color="white", corner_radius=10
        )
        close_button.pack(pady=15)


    def download_report_as_pdf(self, emp_id, name, phone, role, gender, salary, deductions, net_pay, payroll_date, total_days, total_present, total_absent):
        """Generates and saves the employee report as a PDF file."""
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Report As"
        )

        if not file_path:
            return  # User canceled

        pdf = canvas.Canvas(file_path, pagesize=letter)
        pdf.setTitle(f"Employee Report - {name}")

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(200, 750, f"Employee Report - {name}")

        pdf.setFont("Helvetica", 12)
        y_position = 720  

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

        for label, value in details:
            pdf.drawString(100, y_position, f"{label} {value}")
            y_position -= 20  

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(100, y_position - 20, "📊 Attendance Summary")
        pdf.setFont("Helvetica", 12)

        attendance_summary = [
            ("Total Days Tracked:", total_days),
            ("Days Present:", total_present),
            ("Days Absent:", total_absent),
        ]

        y_position -= 40  

        for label, value in attendance_summary:
            pdf.drawString(100, y_position, f"{label} {value}")
            y_position -= 20

        pdf.save()
        messagebox.showinfo("Success", "Report downloaded successfully!")

    def view_report(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, role, gender, salary, deductions, NetPay, PayrollDate FROM data WHERE id = %s", (self.employee_id,))
        report_data = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM attendance WHERE employee_id = %s", (self.employee_id,))
        total_days = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE employee_id = %s AND status = 'Present'", (self.employee_id,))
        total_present = cursor.fetchone()[0]
        total_absent = total_days - total_present

        conn.close()

        if not report_data:
            messagebox.showerror("Error", "No report found for this employee!")
            return

        emp_id, name, phone, role, gender, salary, deductions, net_pay, payroll_date = report_data

       # 🔹 Styled Report Window
        report_window = CTkToplevel(self)
        report_window.title(f"Employee Report - {name}")
        report_window.geometry("500x600")
        report_window.resizable(False, False)
        report_window.configure(bg="#1E2749")  # Dark Blue Theme

        # ✅ Attach to Main Window
        report_window.transient(self)  # Keep it above the main window
        report_window.grab_set()  # Block interactions with the main window until closed
        report_window.focus_force()  # Force focus


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

        # ✅ Grid Layout for Better Spacing
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

        # 📥 Download PDF Button
        download_button = CTkButton(
            report_window, text="📥 Download PDF", font=('Arial', 14, 'bold'),
            command=lambda: self.download_report_as_pdf(emp_id, name, phone, role, gender, salary, deductions, net_pay, payroll_date, total_days, total_present, total_absent),
            fg_color="#007BFF", hover_color="#0056b3", text_color="white"
        )
        download_button.pack(pady=10, side="bottom")

        # 🚪 Close Button (Fixed at Bottom)
        close_button = CTkButton(
            report_window, text="Close", font=('Arial', 14, 'bold'), corner_radius=10, 
            command=report_window.destroy, fg_color="#FF3B3F", hover_color="#D32F2F"
        )
        close_button.pack(pady=10, side="bottom")

    def download_payroll_as_pdf(self, emp_id, name, phone, role, gender, salary, deductions, net_pay, payroll_date):
        """Generates and saves the payroll details as a PDF file."""
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Payroll As"
        )

        if not file_path:
            return  # User canceled

        pdf = canvas.Canvas(file_path, pagesize=letter)
        pdf.setTitle(f"Payroll Details - {name}")

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(200, 750, f"Payroll Details - {name}")

        pdf.setFont("Helvetica", 12)
        y_position = 720  

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

        for label, value in details:
            pdf.drawString(100, y_position, f"{label} {value}")
            y_position -= 20  

        pdf.save()
        messagebox.showinfo("Success", "Payroll downloaded successfully!")

    def view_payroll(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, role, gender, salary, deductions, NetPay, PayrollDate FROM data WHERE id = %s", (self.employee_id,))
        payroll_data = cursor.fetchone()

        conn.close()

        if not payroll_data:
            messagebox.showerror("Error", "Payroll details not found!")
            return

        emp_id, name, phone, role, gender, salary, deductions, net_pay, payroll_date = payroll_data

        payroll_window = Toplevel(self)
        payroll_window.title("Payroll Details")
        payroll_window.geometry("400x500")
        payroll_window.resizable(False, False)
        payroll_window.configure(bg="#161C30")

        CTkLabel(payroll_window, text="📄 Payroll Details", font=("Arial", 16, "bold"), text_color="cyan").pack(pady=5)
        CTkLabel(payroll_window, text=f"Employee ID: {emp_id}", font=("Arial", 14), text_color="white").pack(pady=3)
        CTkLabel(payroll_window, text=f"Name: {name}", font=("Arial", 14), text_color="white").pack(pady=3)
        CTkLabel(payroll_window, text=f"Phone: {phone}", font=("Arial", 14), text_color="white").pack(pady=3)
        CTkLabel(payroll_window, text=f"Role: {role}", font=("Arial", 14), text_color="white").pack(pady=3)
        CTkLabel(payroll_window, text=f"Gender: {gender}", font=("Arial", 14), text_color="white").pack(pady=3)
        CTkLabel(payroll_window, text=f"Salary: Ksh {salary:,.2f}", font=("Arial", 14), text_color="yellow").pack(pady=3)
        CTkLabel(payroll_window, text=f"Deductions: Ksh {deductions:,.2f}", font=("Arial", 14), text_color="red").pack(pady=3)
        CTkLabel(payroll_window, text=f"Net Pay: Ksh {net_pay:,.2f}", font=("Arial", 14, "bold"), text_color="green").pack(pady=3)

        # 📥 Download Payroll PDF Button
        CTkButton(
            payroll_window, text="📥 Download PDF", font=('Arial', 14, 'bold'),
            command=lambda: self.download_payroll_as_pdf(emp_id, name, phone, role, gender, salary, deductions, net_pay, payroll_date),
            fg_color="#007BFF", hover_color="#0056b3", text_color="white"
        ).pack(pady=10)

        CTkButton(payroll_window, text="Close", command=payroll_window.destroy).pack(pady=10)

# Example Usage (Replace 'EMP001' with actual employee ID)
if __name__ == "__main__":
    app = EmployeeDashboard("EMP001")
    app.mainloop()
