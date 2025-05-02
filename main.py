# 📦 Importing required libraries
import streamlit as st  # 🎈 UI library to create web apps easily
import sqlite3  # 🗃️ For storing encrypted data in a local database
import hashlib  # 🔐 For hashing passkeys
import os  # 📁 For file handling
from cryptography.fernet import Fernet  # 🔒 For symmetric encryption

# 📁 File to store the secret key
KEY_FILE = "simple_secret.key"

# 🔑 Load or generate encryption key
def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()  # Generate a new key if it doesn't exist
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key

# 🔒 Initialize cipher using the secret key
cipher = Fernet(load_key())

# 🏗️ Initialize database
def init_db():
    conn = sqlite3.connect("simple_data.db")
    c = conn.cursor()
    # 📄 Create Vault table to store secrets
    c.execute('''CREATE TABLE IF NOT EXISTS Vault
                 (label TEXT PRIMARY KEY, encrypted_text TEXT, passkey TEXT)''')
    conn.commit()
    conn.close()

init_db()  # ⚙️ Initialize DB at app startup

# 🔐 Hash the passkey using SHA-256
def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

# 🔏 Encrypt the text using Fernet
def encrypt(text):
    return cipher.encrypt(text.encode()).decode()

# 🔓 Decrypt the text using Fernet
def decrypt(encrypted_text):
    return cipher.decrypt(encrypted_text.encode()).decode()

# 🖥️ Streamlit UI starts here
st.title("🔐 Secure Data Encryption App")

# 🧭 Sidebar menu
menu = ["Store Secret", "Retrieve Secret"]
choice = st.sidebar.selectbox("📂 Select an option", menu)

# 📝 Option 1: Store Secret
if choice == "Store Secret":
    st.header("💾 Store Your Secret")

    label = st.text_input("🏷️ Label (unique ID): ")
    secret = st.text_area("✉️ Your Secret text")
    passkey = st.text_input("🔑 Passkey (to protect it):", type="password")

    if st.button("🔐 Encrypt and Save"):
        if label and secret and passkey:
            conn = sqlite3.connect("simple_data.db")
            c = conn.cursor()

            encrypted = encrypt(secret)  # 🔒 Encrypt the secret
            hashed_key = hash_passkey(passkey)  # 🧂 Hash the passkey

            try:
                # 🗄️ Insert into DB
                c.execute("INSERT INTO Vault (label, encrypted_text, passkey) VALUES (?, ?, ?)",
                          (label, encrypted, hashed_key))
                conn.commit()
                st.success("✅ Secret stored successfully!")
            except sqlite3.IntegrityError:
                st.error("❗ Label already exists. Please choose a different label.")
            finally:
                conn.close()
        else:
            st.warning("⚠️ Please fill in all fields.")

# 🔍 Option 2: Retrieve Secret
elif choice == "Retrieve Secret":
    st.header("🔍 Retrieve Your Secret")

    label = st.text_input("🏷️ Enter Label for your secret")
    passkey = st.text_input("🔑 Enter Passkey", type="password")

    if st.button("🔓 Decrypt"):
        conn = sqlite3.connect("simple_data.db")
        c = conn.cursor()
        # 📡 Fetch encrypted text and hashed key by label
        c.execute("SELECT encrypted_text, passkey FROM Vault WHERE label=?", (label,))
        result = c.fetchone()
        conn.close()

        if result:
            encrypted_text, stored_hash = result
            # 🧪 Validate passkey
            if hash_passkey(passkey) == stored_hash:
                decrypted = decrypt(encrypted_text)  # 🔓 Decrypt the text
                st.success("🎉 Here is your secret")
                st.code(decrypted)
            else:
                st.error("❌ Incorrect passkey.")
        else:
            st.warning("🚫 No such label found.")
