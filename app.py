import streamlit as st
import pandas as pd
import os
from datetime import datetime
import altair as alt  # Ny import för att kunna bygga anpassade grafer!

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

# --- Skapa flikar ---
flik_logga, flik_grafer, flik_arkiv = st.tabs(["📝 Logga pass", "📈 Utveckling", "🗄️ Arkiv"])

with flik_logga:
    valt_datum = st.date_input("Datum för passet", datetime.today())
    
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
                    vikt = st.number_input(f"Set {i} - Vikt (kg)", min_value=0.0, step=2.5, value=None, key=f"vikt_{i}")
                with kolumner[1]:
                    reps = st.number_input(f"Set {i} - Reps", min_value=0, step=1, value=None, key=f"reps_{i}")
                
                set_data.append({"Set": i, "Vikt (kg)": vikt, "Reps": reps})
                
            spara = st.form_submit_button("Spara Passet")
            
            if spara:
                nya_rader = []
                for data in set_data:
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

# Läs in igen för grafer och arkiv
df_uppdaterad = pd.read_csv(FILE_NAME)

with flik_grafer:
    st.subheader("Kalkylerat 1RM per övning")
    if not df_uppdaterad.empty:
        df_set1 = df_uppdaterad[df_uppdaterad["Set"] == 1].copy()
        
        if not df_set1.empty:
            df_set1["1RM"] = df_set1.apply(
                lambda rad: rad["Vikt (kg)"] if rad["Reps"] == 1 else rad["Vikt (kg)"] * (1 + rad["Reps"] / 30.0), 
                axis=1
            ).round(1) # Avrundar till en decimal för snyggare etiketter
            
            df_plot = df_set1.drop_duplicates(subset=["Datum", "Övning"], keep="last")
            unika_ovningar = df_plot["Övning"].unique()
            
            for ovning in unika_ovningar:
                st.markdown(f"### {ovning}")
                
                df_ovning = df_plot[df_plot["Övning"] == ovning].copy()
                
                # Sätt y-axeln till +- 10 kg från minsta/största värdet
                min_y = float(df_ovning["1RM"].min() - 10)
                max_y = float(df_ovning["1RM"].max() + 10)
                
                # Bygg grafen med Altair
                base = alt.Chart(df_ovning).encode(
                    x=alt.X('Datum:T', title='Datum'),
                    y=alt.Y('1RM:Q', scale=alt.Scale(domain=[max(0, min_y), max_y]), title='1RM (kg)')
                )
                
                # Skapa linjen och punkterna
                line = base.mark_line(point=True)
                
                # Lägg till textetiketterna vid varje punkt
                text = base.mark_text(
                    align='left',
                    baseline='bottom',
                    dx=5,  # Förskjutning i x-led så texten hamnar bredvid
                    dy=-5  # Förskjutning i y-led
                ).encode(
                    text=alt.Text('1RM:Q', format='.1f')
                )
                
                # Slå ihop och rita ut
                chart = (line + text).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Inga Set 1 hittades att bygga grafer på ännu.")
    else:
        st.info("Grafer dyker upp när du loggar första passet.")

with flik_arkiv:
    st.subheader("Träningshistorik")
    if not df_uppdaterad.empty:
        unika_ovningar_arkiv = df_uppdaterad["Övning"].unique()
        
        for ovning in unika_ovningar_arkiv:
            st.markdown(f"### {ovning}")
            
            df_ovning = df_uppdaterad[df_uppdaterad["Övning"] == ovning].copy()
            df_ovning = df_ovning.drop_duplicates(subset=["Datum", "Set"], keep="last")
            
            # Funktion för att bygga ihop reps och vikt till "9 x 70"
            def format_set(rad):
                # Tar bort .0 från vikten om det är ett heltal (t.ex. 70 istället för 70.0)
                vikt = int(rad["Vikt (kg)"]) if rad["Vikt (kg)"] == int(rad["Vikt (kg)"]) else rad["Vikt (kg)"]
                reps = int(rad["Reps"])
                return f"{reps} x {vikt}"
            
            df_ovning["Resultat"] = df_ovning.apply(format_set, axis=1)
            
            # Pivotera datan med den nya sammanslagna texten
            df_pivot = df_ovning.pivot(index="Datum", columns="Set", values="Resultat")
            
            # Formatera om kolumnnamnen till "Set 1", "Set 2" osv.
            df_pivot.columns = [f"Set {col}" for col in df_pivot.columns]
            
            df_pivot = df_pivot.reset_index().sort_values(by="Datum", ascending=False)
            df_pivot = df_pivot.fillna("-")
            
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            
        # --- RADERA FUNKTION ---
        st.divider()
        st.subheader("🗑️ Hantera felaktiga inmatningar")
        st.write("Välj ett pass nedan för att radera hela loggen (alla sets) för den övningen på det valda datumet.")
        
        del_ovning = st.selectbox("1. Välj övning att radera från", ["-- Välj --"] + list(unika_ovningar_arkiv))
        if del_ovning != "-- Välj --":
            datum_for_ovning = df_uppdaterad[df_uppdaterad["Övning"] == del_ovning]["Datum"].unique()
            del_datum = st.selectbox("2. Välj datum att radera", ["-- Välj --"] + list(datum_for_ovning))
            
            if del_datum != "-- Välj --":
                if st.button(f"Radera {del_ovning} ({del_datum})", type="primary"):
                    df_rensad = df_uppdaterad[~((df_uppdaterad["Övning"] == del_ovning) & (df_uppdaterad["Datum"] == del_datum))]
                    df_rensad.to_csv(FILE_NAME, index=False)
                    st.rerun()
    else:
        st.info("Ditt arkiv är tomt än så länge.")
