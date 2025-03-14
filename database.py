import pymysql
from tkinter import messagebox


# ✅ Global connection and cursor
conn = None
mycursor = None

def connect_database():
    """Establishes a connection to the MySQL database and ensures necessary tables exist."""
    global conn, mycursor
    try:
        # ✅ Connect to MySQL (XAMPP)
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='mwalatvc',
            port=3306,
            database='employee_data'
        )
        mycursor = conn.cursor()

        # ✅ Create table if not exists
        mycursor.execute('''
        CREATE TABLE IF NOT EXISTS data (
            Id VARCHAR(30) PRIMARY KEY, 
            Name VARCHAR(50), 
            Phone VARCHAR(15), 
            Role VARCHAR(50), 
            Gender VARCHAR(20), 
            Salary VARCHAR(13)
        )
        ''')
        conn.commit()

        # ✅ Check and add missing columns if they don't exist
        required_columns = {
            "Deductions": "DECIMAL(10,2)",
            "NetPay": "DECIMAL(10,2)",
            "PayrollDate": "DATE"
        }

        for column, col_type in required_columns.items():
            mycursor.execute(f"SHOW COLUMNS FROM data LIKE '{column}'")
            if not mycursor.fetchone():  # ✅ If column does NOT exist, add it
                mycursor.execute(f"ALTER TABLE data ADD COLUMN {column} {col_type}")
                conn.commit()

        print("✅ Database Connected Successfully!")  # ✅ Print instead of popup

    except pymysql.MySQLError as e:
        print(f"❌ Database Connection Error: {e}")  # ✅ Debugging
        messagebox.showerror('Error', f'Could not connect to database: {e}')
        conn = None  # ✅ Ensure connection is None if failed
        mycursor = None  # ✅ Prevent invalid cursor usage

def insert(Id, Name, Phone, Role, Gender, Salary, Deductions=0.0):
    try:
        # Ensure the database is connected
        if conn is None or mycursor is None:
            messagebox.showerror('Error', 'Database is not connected!')
            return

        # Convert Salary & Deductions to float for calculations
        Salary = float(Salary)
        Deductions = float(Deductions)  # ✅ Default to 0.0 if not provided
        NetPay = Salary - Deductions  # ✅ Automatically calculate NetPay

        # SQL Query
        sql = '''
            INSERT INTO data (Id, Name, Phone, Role, Gender, Salary, Deductions, NetPay) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        values = (Id, Name, Phone, Role, Gender, Salary, Deductions, NetPay)

        # Execute & Commit
        mycursor.execute(sql, values)
        conn.commit()

        messagebox.showinfo('Success', 'Employee added successfully!')

    except pymysql.MySQLError as e:
        messagebox.showerror('Error', f'Failed to insert data: {e}')

def Id_exists(Id):
    mycursor.execute('SELECT COUNT(*) FROM data WHERE Id=%s', Id)

    result = mycursor.fetchone()
    return result[0] > 0

def fetch_employees():
    mycursor.execute('SELECT * from data')
    result = mycursor.fetchall()
    return result

def update_employee_data(employee_id, name, phone, role, gender, salary, deductions, netpay):
    try:
        sql = '''UPDATE data 
                 SET Name=%s, Phone=%s, Role=%s, Gender=%s, Salary=%s, Deductions=%s, NetPay=%s 
                 WHERE Id=%s'''
        values = (name, phone, role, gender, salary, deductions, netpay, employee_id)

        mycursor.execute(sql, values)
        conn.commit()
        
    except pymysql.MySQLError as e:
        messagebox.showerror('Error', f'Failed to update data: {e}')





def delete(Id):
    mycursor.execute('DELETE FROM data WHERE Id=%s', Id)
    conn.commit()
def search(option, value):
    # Allowed columns (make sure they match exactly with your database)
    allowed_columns = {'Id', 'Name', 'Phone', 'Role', 'Gender', 'Salary', 'Deductions', 'NetPay'}

    # Convert option to match correct casing
    option = option.title()  # Adjust this based on your actual column naming

    if option not in allowed_columns:
        return []  # Return an empty list if the column is not valid

    sql = f'SELECT * FROM data WHERE `{option}` = %s'  # Add backticks to prevent errors
    mycursor.execute(sql, (value,))  # Pass parameter as a tuple
    result = mycursor.fetchall()
    return result
def deleteall_records():
    mycursor.execute('TRUNCATE TABLE data')
    conn.commit()

# Payroll function to fetch salary and deductions from data table
def calculate_payroll(employee_id):
    mycursor.execute('''
        SELECT Name, Phone, Role, Gender, Salary, 
               COALESCE(Deductions, 0), PayrollDate  -- ✅ Remove CURDATE()
        FROM data WHERE Id = %s
    ''', (employee_id,))
    
    payroll_data = mycursor.fetchone()

    if not payroll_data:
        return None  # ✅ Return None if employee does not exist

    return {
        "name": payroll_data[0],
        "phone": payroll_data[1],
        "role": payroll_data[2],
        "gender": payroll_data[3],
        "salary": float(payroll_data[4]),  # ✅ Ensure float conversion
        "deductions": float(payroll_data[5]),  # ✅ Handle NULL values with COALESCE
        "payroll_date": payroll_data[6]  # ✅ Return None if PayrollDate is NULL
    }


def payroll_exists(employee_id):
    mycursor.execute("SELECT PayrollDate FROM data WHERE Id = %s AND PayrollDate IS NOT NULL", (employee_id,))
    return mycursor.fetchone() is not None  # ✅ Returns True if PayrollDate exists


from datetime import datetime

def update_netpay(employee_id, net_pay, payroll_date):
    mycursor.execute(
        "UPDATE data SET NetPay=%s, PayrollDate=%s WHERE Id=%s",
        (net_pay, payroll_date, employee_id)
    )
    conn.commit()


def generate_report(employee_id):
    try:
        mycursor.execute('''
            SELECT Id, Name, Phone, Role, Gender, Salary, 
                   COALESCE(Deductions, 0), 
                   (Salary - COALESCE(Deductions, 0)) AS NetPay, 
                   COALESCE(PayrollDate, CURDATE()) 
            FROM data WHERE Id = %s
        ''', (employee_id,))
        
        report_data = mycursor.fetchone()  # Fetch only one employee record

        if not report_data:
            return None  # If no data is found, return None

        # ✅ Return employee details as a dictionary
        return {
            "id": report_data[0],
            "name": report_data[1],
            "phone": report_data[2],
            "role": report_data[3],
            "gender": report_data[4],
            "salary": float(report_data[5]),  # Ensure salary is float
            "deductions": float(report_data[6]),  # Ensure deductions are float
            "net_pay": float(report_data[7]),  # Calculate NetPay dynamically
            "payroll_date": report_data[8]  # Get Payroll Date
        }

    except pymysql.MySQLError as e:
        messagebox.showerror('Database Error', f"Failed to fetch report: {e}")
        return None  # Return None if an error occurs


def modify_attendance(employee_id, status):
    """Updates the attendance status for the given employee ID or inserts if missing."""
    global mycursor, conn  # ✅ Ensure access to global cursor & connection

    try:
        query = """
        INSERT INTO attendance (employee_id, date, status) 
        VALUES (%s, CURDATE(), %s) 
        ON DUPLICATE KEY UPDATE Status = %s
        """
        mycursor.execute(query, (employee_id, status, status))
        conn.commit()  # ✅ Save changes
    except pymysql.MySQLError as e:
        messagebox.showerror('Database Error', f"Failed to update attendance: {e}")


def get_monthly_attendance(employee_id):
    """Fetches attendance records for the current month for a given employee."""
    if not conn or not mycursor:
        messagebox.showerror('Database Error', 'Database connection is not established!')
        return []
    
    try:
        query = """
        SELECT date, status FROM attendance
        WHERE employee_id = %s 
        AND MONTH(date) = MONTH(CURDATE()) 
        AND YEAR(date) = YEAR(CURDATE())
        ORDER BY date
        """
        mycursor.execute(query, (employee_id,))
        return mycursor.fetchall()  # ✅ Returns list of (date, status)
    except pymysql.MySQLError as e:
        messagebox.showerror('Database Error', f"Failed to fetch attendance: {e}")
        return []




# Run function to test connection
connect_database()
