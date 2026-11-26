
from database import create_tables, create_user, get_connection

create_tables()

conn = get_connection()

admin_exists = conn.execute(
    "SELECT id FROM users WHERE role = 'Admin'"
).fetchone()

conn.close()

if admin_exists:
    print("An Admin account already exists.")
else:
    username = input("Enter Admin username: ")
    password = input("Enter Admin password: ")

    try:
        create_user(username, password, "Admin")
        print("Admin account created successfully!")
    except ValueError as e:
        print(e)
