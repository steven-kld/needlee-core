from atoms import run_query
import bcrypt, random, string, os

def check_creds(email, password):
    msg = 'OK'
    display_name = ''
    id = None
    result = run_query(
        """
        SELECT hashed_password, salt, display_name, id 
        FROM organizations
        WHERE email = %s
        """,
        (email,),
        fetch_one=True
    )

    if result is None:
        msg = "Organization not found"
    else:
        stored_hash = bytes(result["hashed_password"])
        stored_salt = bytes(result["salt"])
        if not verify_password(stored_hash, stored_salt, password):
            msg = "Incorrect password"
        else:
            display_name = result["display_name"]
            id = result["id"]

    return msg, display_name, id


def set_password(password, email):
    hashed_password, salt = hash_password(password)
    return run_query(
        """
        UPDATE organizations 
        SET hashed_password = %s, salt = %s
        WHERE email = %s
        """,
        (hashed_password, salt, email),
        fetch_one=False
    )

def verify_password(stored_hash, stored_salt, password_to_check):
    return stored_hash == bcrypt.hashpw(password_to_check.encode('utf-8'), stored_salt)

def generate_password(length=17):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password, salt



# def insert_new_organization(email, display_name):
#     if check_organization_email_exists(email):
#         return False, False

#     password = generate_password()
#     hashed_password, salt = hash_password(password)

#     if verify_password(hashed_password, salt, password):
#         cur, conn = connect_db()

#         cur.execute("""
#             INSERT INTO organization (email, hashed_password, salt, display_name)
#             VALUES (%s, %s, %s, %s)
#             RETURNING id;
#         """, (email, hashed_password, salt, display_name))

#         organization_id = cur.fetchone()[0]

#         conn.commit()
#         cur.close()
#         conn.close()
#         return organization_id, password

# def get_organization_by_id(id):
#     cur, conn = connect_db()
#     cur.execute("SELECT email, data FROM organization WHERE id = %s", (id,))
#     result = cur.fetchone()
    
#     if result is None:
#         print("Error: No organization found with the provided id.")
#         return False

#     email = result[0]
#     data = result[1]

#     cur.close()
#     conn.close()
#     return email, data

# def get_organization_by_email(email):
#     cur, conn = connect_db()
#     cur.execute("SELECT id, data FROM organization WHERE email = %s", (email,))
#     result = cur.fetchone()
    
#     if result is None:
#         print("Error: No organization found with the provided email.")
#         return False

#     id = result[0]
#     data = result[1]

#     cur.close()
#     conn.close()
#     return id, data

# def check_organization_id_exists(id):
#     cur, conn = connect_db()
#     cur.execute("SELECT 1 FROM organization WHERE id = %s", (id,))
#     id_exists = cur.fetchone() is not None
#     cur.close()
#     conn.close()
#     return id_exists

# def check_organization_email_exists(email):
#     cur, conn = connect_db()
#     cur.execute("SELECT 1 FROM organization WHERE email = %s", (email,))
#     email_exists = cur.fetchone() is not None
#     cur.close()
#     conn.close()
#     return email_exists



# def update_password(email, old_password, new_password):
#     cur, conn = connect_db()

#     cur.execute("SELECT hashed_password, salt FROM organization WHERE email = %s", (email,))
#     result = cur.fetchone()
    
#     if result is None:
#         print("Error: No user found with the provided email.")
#         return False

#     stored_hash = bytes(result[0])
#     stored_salt = bytes(result[1])
    
#     if verify_password(stored_hash, stored_salt, old_password):
#         hashed_new_password, new_salt = hash_password(new_password)
        
#         cur.execute("""
#             UPDATE organization
#             SET hashed_password = %s, salt = %s
#             WHERE email = %s
#         """, (hashed_new_password, new_salt, email))
        
#         conn.commit()
#         print("Password successfully updated.")
#     else:
#         print("Error: The current password is incorrect.")
    
#     cur.close()
#     conn.close()

# def update_email(email, password, new_email):
#     if check_organization_email_exists(new_email):
#         print("Email doesn't exist")
#         return False
#     cur, conn = connect_db()

#     cur.execute("SELECT hashed_password, salt, id FROM organization WHERE email = %s", (email,))
#     result = cur.fetchone()
    
#     if result is None:
#         print("Error: No user found with the provided email.")
#         return False

#     stored_hash = bytes(result[0])
#     stored_salt = bytes(result[1])
#     id = result[2]

#     if verify_password(stored_hash, stored_salt, password):
#         cur.execute("""
#             UPDATE organization
#             SET email = %s
#             WHERE id = %s
#         """, (new_email, id))
        
#         conn.commit()
#         print("Email successfully updated.")
#     else:
#         print("Error: The current password is incorrect.")
    
#     cur.close()
#     conn.close()