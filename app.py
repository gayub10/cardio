import streamlit as st
import sqlite3
import numpy as np
import pickle as pkl
from sklearn.preprocessing import StandardScaler

# Load the saved model
model = pkl.load(open("model_wcc.pkl", "rb"))

st.set_page_config(page_title="Healthy Heart App", page_icon="⚕️", layout="centered", initial_sidebar_state="expanded")

# Function to create database connection
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        st.write("Database connected successfully.")
    except sqlite3.Error as e:
        st.error(f"Error connecting to database: {e}")
    return conn

# Function to create table if it doesn't exist
def create_table(conn):
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, password TEXT, age INT, sex TEXT, cp TEXT, trestbps INT, chol INT, thalach INT, exang TEXT, oldpeak REAL, slope TEXT, ca INT, thal TEXT)''')
        conn.commit()
        st.write("Table created or verified successfully.")
    except sqlite3.Error as e:
        st.error(f"Error creating table: {e}")

# Predicting the class
def predict_disease(x): 
    return model.predict([x])

# Preprocessing user Input
def preprocess(age, sex, cp, trestbps, chol, thalach, exang, oldpeak, slope, ca, thal):   
    # Pre-processing user input   
    sex = 1 if sex == "male" else 0
    cp = {"Typical angina": 0, "Atypical angina": 1, "Non-anginal pain": 2, "Asymptomatic": 3}[cp]
    exang = 1 if exang == "Yes" else 0
    slope = {"Upsloping: better heart rate with excercise(uncommon)": 0, 
             "Flatsloping: minimal change(typical healthy heart)": 1, 
             "Downsloping: signs of unhealthy heart": 2}[slope]
    thal = {"fixed defect: used to be defect but ok now": 6, 
            "reversable defect: no proper blood movement when excercising": 7, 
            "normal": 2.31}[thal]

    col_names = np.array(['age', 'sex', 'trestbps', 'chol', 'thalach', 'oldpeak', 'cp_1', 'cp_2','cp_3', 
                          'exang_1', 'slope_1','slope_2', 'ca_1', 'ca_2', 'ca_3', 'ca_4', 'thal_1', 'thal_2','thal_3'])
    cp, exang, slope, ca, thal = f"cp_{cp}", f"exang_{exang}", f"slope_{slope}", f"ca_{ca}", f"thal_{thal}"
    
    x = np.zeros(len(col_names))
    for feature in [cp, exang, slope, ca, thal]:
        index = np.where(col_names == feature)[0]
        if index.size > 0:
            x[index[0]] = 1

    x[:6] = [age, sex, trestbps, chol, thalach, oldpeak]

    # Feature scaling
    scalar = StandardScaler()
    x[:6] = scalar.fit_transform(x[:6].reshape(1, -1))

    return x

# Front end elements of the web page 
html_temp = """ 
    <div style ="background-color: #f9f9f9; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);"> 
    <h1 style ="color: #333333; text-align: center;">Healthy Heart App</h1> 
    </div> 
    """
      
# Display the front end aspect
st.markdown(html_temp, unsafe_allow_html=True) 
st.subheader('by Batch B Team 10')

# Initialize session state for sign-in status
if 'signed_in' not in st.session_state:
    st.session_state.signed_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# Create a database connection
conn = create_connection("user_data.db")
if conn is not None:
    # Create users table if it doesn't exist
    create_table(conn)
else:
    st.error("Error! Cannot create the database connection.")
    st.stop()

# Sign-in page
def sign_in():
    st.write("## Sign In")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign In"):
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        data = c.fetchone()
        if data:
            st.session_state.signed_in = True
            st.session_state.username = username
            st.success("Successfully signed in!")
            st.write(f"User data: {data}")
            return True
        else:
            st.error("Invalid username or password.")
            return False
    return False

# Function to insert user data into the database
def insert_data(username, password, age, sex, cp, trestbps, chol, thalach, exang, oldpeak, slope, ca, thal):
    try:
        conn.execute("INSERT INTO users (username, password, age, sex, cp, trestbps, chol, thalach, exang, oldpeak, slope, ca, thal) \
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (username, password, age, sex, cp, trestbps, chol, thalach, exang, oldpeak, slope, ca, thal))
        conn.commit()
        st.write("User data inserted successfully.")
        return True
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose a different username.")
        return False

# Sign-up page
def sign_up():
    st.write("## Sign Up")
    username = st.text_input("New Username")
    password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if password != confirm_password:
        st.warning("Passwords do not match.")
        return False
    
    if st.button("Sign Up"):
        if insert_data(username, password, 0, "", "", 0, 0, 0, "", 0.0, "", 0, ""):
            st.success("Successfully signed up!")
            return True
        else:
            return False

# Sign-in or sign-up logic
if not st.session_state.signed_in:
    choice = st.sidebar.selectbox("Login/Signup", ["Sign In", "Sign Up"])
    if choice == "Sign Up":
        if not sign_up():
            st.stop()
    else:
        if not sign_in():
            st.stop()

# Creating boxes for user inputs
st.write("### Enter your details to check your heart health")

col1, col2 = st.columns(2)
with col1:
    age = st.selectbox("Age", range(1, 121, 1))
    sex = st.radio("Select Gender: ", ('male', 'female'))
    cp = st.selectbox('Chest Pain Type', ("Typical angina", "Atypical angina", "Non-anginal pain", "Asymptomatic"))
    trestbps = st.selectbox('Resting Blood Sugar', range(1, 500, 1))
    chol = st.selectbox('Serum Cholestoral in mg/dl', range(1, 1000, 1))

with col2:
    thalach = st.selectbox('Maximum Heart Rate Achieved', range(1, 300, 1))
    exang = st.selectbox('Exercise Induced Angina', ["Yes", "No"])
    oldpeak = st.number_input('Oldpeak')
    slope = st.selectbox('Heart Rate Slope', ("Upsloping: better heart rate with excercise(uncommon)", "Flatsloping: minimal change(typical healthy heart)", "Downsloping: signs of unhealthy heart"))
    ca = st.selectbox('Number of Major Vessels Colored by Flourosopy', range(0, 5, 1))
    thal = st.selectbox('Thalium Stress Result', ["fixed defect: used to be defect but ok now", "reversable defect: no proper blood movement when excercising", "normal"])

# Pre-processing the actual user input
user_processed_input = preprocess(age, sex, cp, trestbps, chol, thalach, exang, oldpeak, slope, ca, thal)
pred = predict_disease(user_processed_input)

if st.button("Predict"):    
    if pred[0] == 0:
        st.success('You have a lower risk of getting a heart disease!')
    else:
        st.error('Warning! You have a high risk of getting a heart attack!')

    # Insert user data into the database
    insert_data(st.session_state.username, "", age, sex, cp, trestbps, chol, thalach, exang, oldpeak, slope, ca, thal)
    
st.sidebar.subheader("About App")
st.sidebar.info("This web app helps you to find out whether you are at a risk of developing a heart disease.")
st.sidebar.info("Enter the required fields and click on the 'Predict' button to check whether you have a healthy heart")
st.sidebar.info("Don't forget to rate this app")

feedback = st.sidebar.slider('How much would you rate this app?', min_value=0, max_value=5, step=1)

if feedback:
    st.header("Thank you for rating the app!")
    st.info("Caution: This is just a prediction and not a substitute for professional medical advice. Kindly see a doctor if you have any concerns.")

# Closing database connection
conn.close()
