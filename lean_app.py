import streamlit as st
st.set_page_config(page_title="YMCA LEAN App", layout="centered")

import pymysql
from datetime import date

# ==============================
# DB CONNECTION (SAFE)
# ==============================
def get_connection():
    try:
        return pymysql.connect(
            host="localhost",  # change later
            user="root",
            password="ymca",
            database="checkin"
        )
    except:
        return None

# ==============================
# HELPERS
# ==============================
def canonical_key(raw):
    raw = (raw or "").strip().lower()
    raw = raw.replace("_", "|")
    return "|".join([p.strip() for p in raw.split("|")])

st.title("YMCA LEAN Program")

# ------------------------------
# Session Info
# ------------------------------
st.sidebar.header("Session Setup")

location = st.sidebar.text_input("Location")
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

    if conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
    else:
        st.warning("⚠️ Database not connected (running in demo mode)")
        cursor = None

    ukey = canonical_key(qr_input)

    # ------------------------------
    # FETCH CLIENT
    # ------------------------------
    if conn:
        cursor.execute("""
            SELECT UniqueKey, FirstName, LastName, DOB
            FROM clients
            WHERE UniqueKey = %s
        """, (ukey,))
        client = cursor.fetchone()
    else:
        client = {
            "UniqueKey": ukey,
            "FirstName": "Demo",
            "LastName": "User",
            "DOB": None
        }

    if not client:
        st.error("Client not found")
    else:
        dob = client["DOB"]
        age = None

        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        st.success(f"Client: {client['FirstName']} {client['LastName']} | Age: {age}")

        # ------------------------------
        # PREVIOUS RECORD
        # ------------------------------
        if conn:
            cursor.execute("""
                SELECT SessionDate, Weight, BodyFatPercent, WaistCircumference,
                       Systolic, Diastolic
                FROM lean_assessments
                WHERE UniqueKey = %s
                ORDER BY SessionDate DESC
                LIMIT 1
            """, (client["UniqueKey"],))

            last = cursor.fetchone()
        else:
            last = None

        if last:
            st.info(f"""
Previous:
Date: {last['SessionDate']}
BP: {last['Systolic']}/{last['Diastolic']}
Weight: {last['Weight']} lbs
Waist: {last['WaistCircumference']} in
""")

        st.subheader("Enter Measurements")

        # ✅ SPLIT HEIGHT
        col1, col2 = st.columns(2)
        with col1:
            height_ft = st.number_input("Height (ft)", min_value=0, step=1)
        with col2:
            height_in = st.number_input("Height (inches)", min_value=0, step=1)

        # Combine height (optional: store as total inches)
        height = height_ft * 12 + height_in

        systolic = st.number_input("Systolic BP", step=1)
        diastolic = st.number_input("Diastolic BP", step=1)
        weight = st.number_input("Weight (lbs)")
        bodyfat = st.number_input("Body Fat (%)")
        waist = st.number_input("Waist (inches)")

        notes = st.text_input("Notes (optional)")

        # ------------------------------
        # SAVE
        # ------------------------------
        if st.button("Submit"):

            if conn:
                cursor.execute("""
                    INSERT INTO lean_assessments
                    (UniqueKey, CohortName, CoachName, SessionNumber,
                     AssessmentType, SessionDate,
                     Age, Height, Systolic, Diastolic,
                     Weight, BodyFatPercent, WaistCircumference,
                     Location, Notes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
                    waist,
                    location,
                    notes
                ))

                conn.commit()
                st.success("✅ Saved to database")

            else:
                st.success("✅ Saved (demo mode - DB not connected)")

    # ------------------------------
    # CLOSE CONNECTION
    # ------------------------------
    if conn:
        cursor.close()
        conn.close()
