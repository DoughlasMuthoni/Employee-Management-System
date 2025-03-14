import pymysql
import bcrypt

# Database Connection
def get_db_connection():
    """Connect to the MySQL database."""
    return pymysql.connect(
        host='localhost',
        user='root',
        password='mwalatvc',
        port=3306,
        database='employee_data'
    )

# Hash Password
def hash_password(password):
    """Encrypts the password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Verify Password
def verify_password(input_password, stored_hash):
    """Checks if the entered password matches the stored hash."""
    return bcrypt.checkpw(input_password.encode('utf-8'), stored_hash.encode('utf-8'))

# Create Admin User
def create_admin():
    """Creates an admin user if one doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if Admin already exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Admin'")
    if cursor.fetchone()[0] > 0:
        print("✅ Admin already exists!")
        conn.close()
        return

    # Admin Details
    admin_id = "EMP001"
    admin_name = "Admin User"
    admin_phone = "0712345678"
    admin_role = "Admin"
    admin_password = "admin123"
    admin_password_hash = hash_password(admin_password)

    # Insert Admin User
    cursor.execute("""
        INSERT INTO users (employee_id, name, phone, role, password_hash)
        VALUES (%s, %s, %s, %s, %s)
    """, (admin_id, admin_name, admin_phone, admin_role, admin_password_hash))

    conn.commit()
    conn.close()
    print("✅ Admin user created successfully!")

# Admin Login Function
def admin_login(username, password):
    """Verifies admin credentials and returns success or failure."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch Admin Details
    cursor.execute("SELECT password_hash FROM users WHERE employee_id = %s AND role = 'Admin'", (username,))
    admin_data = cursor.fetchone()

    conn.close()

    if admin_data:
        stored_hash = admin_data[0]
        if verify_password(password, stored_hash):
            return True  # ✅ Login successful
        else:
            return False  # ❌ Incorrect password
    else:
        return False  # ❌ Admin not found

# Run the function to create an admin
if __name__ == "__main__":
    create_admin()

    # Example Admin Login Test
    username_input = input("Enter Admin Employee ID: ")
    password_input = input("Enter Admin Password: ")

    if admin_login(username_input, password_input):
        print("✅ Login Successful! Welcome Admin.")
    else:
        print("❌ Login Failed! Invalid Credentials.")
