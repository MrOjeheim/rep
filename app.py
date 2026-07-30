import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.title("GymTracker 🏋️")

# Skapa en enkel CSV-fil som databas
FILE_NAME = "workout_log.csv"

if not os.path.exists(FILE_NAME):
    pd.DataFrame(columns=["Datum", "Övning", "Vikt (kg)", "Reps", "Sets"]).to_csv(FILE_NAME, index=False)

# Gränssnitt för inmatning
with st.form("inmatning"):
    ovning = st.text_input("Övning", value="Bänkpress")
    vikt = st.number_input("Vikt (kg)", min_value=0.0, step=2.5)
    reps = st.number_input("Reps", min_value=1, step=1)
    sets = st.number_input("Sets", min_value=1, step=1)
    spara = st.form_submit_button("Spara")

    if spara:
        ny_data = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ovning, vikt, reps, sets]], 
                               columns=["Datum", "Övning", "Vikt (kg)", "Reps", "Sets"])
        ny_data.to_csv(FILE_NAME, mode='a', header=False, index=False)
        st.success("Sparat!")

# Visa din historik
st.subheader("Tidigare pass")
df = pd.read_csv(FILE_NAME)
st.dataframe(df.tail(10))
