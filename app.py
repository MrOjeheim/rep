import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Sidinställningar
st.set_page_config(page_title="GymTracker", page_icon="🏋️")
st.title("GymTracker 🏋️")

FILE_NAME = "workout_log.csv"

# 1. Skapa filen om den inte finns
if not os.path.exists(FILE_NAME):
    pd.DataFrame(columns=["Datum", "Övning", "Set", "Vikt (kg)", "Reps"]).to_csv(FILE_NAME, index=False)

df = pd.read_csv(FILE_NAME)

if not df.empty:
    sparade_ovningar = df["Övning"].unique().tolist()
else:
    sparade_ovningar = ["Bänkpress", "Knäböj", "Marklyft"]

# --- Skapa flikar för att hålla appen städad ---
flik_logga, flik_grafer, flik_arkiv = st.tabs(["📝 Logga pass", "📈 Utveckling", "🗄️ Arkiv"])

with flik_logga:
    # Välj datum (Förinställt på idag)
    valt_datum = st.date_input("Datum för passet", datetime.today())
    
    # Välj eller lägg till ny övning
    val = st.selectbox("Välj övning", ["-- Lägg till ny övning --"] + sparade_ovningar)
    
    if val == "-- Lägg till ny övning --":
        vald_ovning = st.text_input("Namn på ny övning:")
    else:
        vald_ovning = val

    if vald_ovning:
        antal_sets = st.number_input("Hur många sets gjorde du?", min_value=1, max_value=15, value=3, step=1)
        
        with st.form("set_form"):
            st.write(f"Fyll i resultat för **{vald_ovning}**")
            
            set_data = []
            for i in range(1, int(antal_sets) + 1):
                kolumner = st.columns(2)
                with kolumner[0]:
                    # value=None gör att rutan är helt blank när du startar
                    vikt = st.number_input(f"Set {i} - Vikt (kg)", min_value=0.0, step=2.5, value=None, key=f"vikt_{i}")
                with kolumner[1]:
                    reps = st.number_input(f"Set {i} - Reps", min_value=0, step=1, value=None, key=f"reps_{i}")
                
                set_data.append({"Set": i, "Vikt (kg)": vikt, "Reps": reps})
                
            spara = st.form_submit_button("Spara Passet")
            
            if spara:
                nya_rader = []
                for data in set_data:
                    # Kontrollera att varken vikt eller reps är tomt
                    if data["Reps"] is not None and data["Reps"] > 0 and data["Vikt (kg)"] is not None: 
                        nya_rader.append({
                            "Datum": valt_datum.strftime("%Y-%m-%d"),
                            "Övning": vald_ovning,
                            "Set": data["Set"],
                            "Vikt (kg)": data["Vikt (kg)"],
                            "Reps": data["Reps"]
                        })
                
                if nya_rader:
                    ny_df = pd.DataFrame(nya_rader)
                    skriv_rubrik = not os.path.exists(FILE_NAME) or os.stat(FILE_NAME).st_size == 0
                    ny_df.to_csv(FILE_NAME, mode='a', header=skriv_rubrik, index=False)
                    st.success(f"Sparade {len(nya_rader)} sets av {vald_ovning} den {valt_datum.strftime('%Y-%m-%d')}!")
                else:
                    st.warning("Inga fullständiga sets (både vikt och reps) ifyllda.")

# Läs in igen för att grafer och arkiv ska uppdateras blixtsnabbt
df_uppdaterad = pd.read_csv(FILE_NAME)

with flik_grafer:
    st.subheader("Kalkylerat 1RM per övning")
    if not df_uppdaterad.empty:
        # Filtrera ut Set 1 för att beräkna maxkapaciteten
        df_set1 = df_uppdaterad[df_uppdaterad["Set"] == 1].copy()
        
        if not df_set1.empty:
            df_set1["1RM"] = df_set1.apply(
                lambda rad: rad["Vikt (kg)"] if rad["Reps"] == 1 else rad["Vikt (kg)"] * (1 + rad["Reps"] / 30.0), 
                axis=1
            )
            df_plot = df_set1.drop_duplicates(subset=["Datum", "Övning"], keep="last")
            
            # Skapa en separat graf för varje enskild övning
            unika_ovningar = df_plot["Övning"].unique()
            
            for ovning in unika_ovningar:
                st.markdown(f"### {ovning}")
                # Sätt Datum som X-axel för grafen
                df_ovning = df_plot[df_plot["Övning"] == ovning].set_index("Datum")
                st.line_chart(df_ovning[["1RM"]])
        else:
            st.info("Inga Set 1 hittades att bygga grafer på ännu.")
    else:
        st.info("Grafer dyker upp när du loggar första passet.")

with flik_arkiv:
    st.subheader("All din träningshistorik")
    if not df_uppdaterad.empty:
        # Sortera datan så att de nyaste passen hamnar högst upp
        df_sorterad = df_uppdaterad.sort_values(by=["Datum", "Övning", "Set"], ascending=[False, True, True])
        st.dataframe(df_sorterad, use_container_width=True)
    else:
        st.info("Ditt arkiv är tomt än så länge.")
