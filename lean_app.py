import streamlit as st
st.set_page_config(page_title="YMCA LEAN App", layout="centered")
import pymysql
from datetime import date

# ==============================
# DB CONNECTION
# ==============================
def get_connection():
    return pymysql.connect(
        host="localhost", # change later
        user="root",
        password="ymca",
        database="checkin"
    )

def canonical_key(raw):
    raw = (raw or "").strip().lower()
    raw = raw.replace("_", "|")
    return "|".join([p.strip() for p in raw.split("|")])

st.title("YMCA LEAN Program")

# ------------------------------
# Session Info
# ------------------------------
st.sidebar.header("Session Setup")

cohort = st.sidebar.text_input("Cohort Name")
coach = st.sidebar.text_input("Coach Name")
session_number = st.sidebar.number_input("Session Number", step=1)
assessment_type = st.sidebar.selectbox("Assessment Type", ["Baseline", "End"])
session_date = st.sidebar.date_input("Session Date")

# ------------------------------
# QR Input
# ------------------------------
qr_input = st.text_input("Scan / Enter QR Code")

if qr_input:

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    ukey = canonical_key(qr_input)

    cursor.execute("""
        SELECT UniqueKey, FirstName, LastName, DOB
        FROM clients
        WHERE UniqueKey = %s
    """, (ukey,))

    client = cursor.fetchone()

    if not client:
        st.error("Client not found")
    else:
        dob = client["DOB"]
        age = None
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        st.success(f"Client: {client['FirstName']} {client['LastName']} | Age: {age}")

        # Previous record
        cursor.execute("""
            SELECT SessionDate, Weight, BodyFatPercent, WaistCircumference,
                   Systolic, Diastolic
            FROM lean_assessments
            WHERE UniqueKey = %s
            ORDER BY SessionDate DESC
            LIMIT 1
        """, (client["UniqueKey"],))

        last = cursor.fetchone()

        if last:
            st.info(f"""
Previous:
Date: {last['SessionDate']}
BP: {last['Systolic']}/{last['Diastolic']}
Weight: {last['Weight']} lbs
Waist: {last['WaistCircumference']} in
""")

        st.subheader("Enter Measurements")

        height = st.text_input("Height (ft/in or inches)")
        systolic = st.number_input("Systolic BP", step=1)
        diastolic = st.number_input("Diastolic BP", step=1)
        weight = st.number_input("Weight (lbs)")
        bodyfat = st.number_input("Body Fat (%)")
        waist = st.number_input("Waist (inches)")

        if st.button("Submit"):

            cursor.execute("""
                INSERT INTO lean_assessments
                (UniqueKey, CohortName, CoachName, SessionNumber,
                 AssessmentType, SessionDate,
                 Age, Height, Systolic, Diastolic,
                 Weight, BodyFatPercent, WaistCircumference)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                client["UniqueKey"],
                cohort,
                coach,
                session_number,
                assessment_type,
                session_date,
                age,
                height,
                systolic,
                diastolic,
                weight,
                bodyfat,
                waist
            ))

            conn.commit()
            st.success("Saved successfully")

    cursor.close()
    conn.close()
