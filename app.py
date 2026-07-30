import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Gör så appen ser lite snyggare ut på mobilen
st.set_page_config(page_title="GymTracker", page_icon="🏋️")
st.title("GymTracker 🏋️")

FILE_NAME = "workout_log.csv"

# 1. Skapa filen med den nya strukturen om den inte finns
if not os.path.exists(FILE_NAME):
    pd.DataFrame(columns=["Datum", "Övning", "Set", "Vikt (kg)", "Reps"]).to_csv(FILE_NAME, index=False)

# Läs in befintlig data
df = pd.read_csv(FILE_NAME)

# Hämta unika övningar från din historik (så du slipper skriva dem varje gång)
if not df.empty:
    sparade_ovningar = df["Övning"].unique().tolist()
else:
    sparade_ovningar = ["Bänkpress", "Knäböj", "Marklyft"]

# 2. Välj eller lägg till ny övning
st.subheader("Registrera")
val = st.selectbox("Välj övning", ["-- Lägg till ny övning --"] + sparade_ovningar)

if val == "-- Lägg till ny övning --":
    vald_ovning = st.text_input("Namn på ny övning:")
else:
    vald_ovning = val

# 3. Mata in sets och reps dynamiskt
if vald_ovning:
    antal_sets = st.number_input("Hur många sets gjorde du?", min_value=1, max_value=15, value=3, step=1)
    
    with st.form("set_form"):
        st.write(f"Fyll i resultat för **{vald_ovning}**")
        
        set_data = []
        # Skapa inmatningsfält för det antal sets du valt
        for i in range(1, int(antal_sets) + 1):
            kolumner = st.columns(2)
            with kolumner[0]:
                vikt = st.number_input(f"Set {i} - Vikt (kg)", min_value=0.0, step=2.5, key=f"vikt_{i}")
            with kolumner[1]:
                reps = st.number_input(f"Set {i} - Reps", min_value=0, step=1, key=f"reps_{i}")
            
            set_data.append({"Set": i, "Vikt (kg)": vikt, "Reps": reps})
            
        spara = st.form_submit_button("Spara Passet")
        
        # När du trycker på spara
        if spara:
            dagens_datum = datetime.now().strftime("%Y-%m-%d")
            nya_rader = []
            
            for data in set_data:
                # Spara bara set där du faktiskt skrivit in reps
                if data["Reps"] > 0: 
                    nya_rader.append({
                        "Datum": dagens_datum,
                        "Övning": vald_ovning,
                        "Set": data["Set"],
                        "Vikt (kg)": data["Vikt (kg)"],
                        "Reps": data["Reps"]
                    })
            
            if nya_rader:
                ny_df = pd.DataFrame(nya_rader)
                # Om filen är helt tom, skriv med rubriker, annars lägg bara till datan
                skriv_rubrik = inte os.path.exists(FILE_NAME) or os.stat(FILE_NAME).st_size == 0
                ny_df.to_csv(FILE_NAME, mode='a', header=skriv_rubrik, index=False)
                st.success(f"Sparade {len(nya_rader)} sets av {vald_ovning}!")
            else:
                st.warning("Inga reps ifyllda, inget sparades.")

# 4. Visa historik
st.divider()
st.subheader("Dagens logg")

# Läs in filen på nytt för att historiken ska uppdateras direkt när du klickar spara
df_uppdaterad = pd.read_csv(FILE_NAME)
dagens_datum = datetime.now().strftime("%Y-%m-%d")

if not df_uppdaterad.empty:
    dagens_pass = df_uppdaterad[df_uppdaterad["Datum"] == dagens_datum]
    if not dagens_pass.empty:
        # Visar tabellen snyggt anpassad för skärmens bredd
        st.dataframe(dagens_pass, use_container_width=True)
    else:
        st.info("Inget loggat idag ännu.")
