import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt
from supabase import create_client, Client

# Sidinställningar
st.set_page_config(page_title="GymTracker", page_icon="🏋️")
st.title("GymTracker 🏋️")

# Initiera Supabase-klienten (körs bara en gång tack vare @st.cache_resource)
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# Funktion för att hämta all data från Supabase
def fetch_data():
    response = supabase.table("workout_log").select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    else:
        # Returnera en tom DataFrame med rätt kolumner om databasen är tom
        return pd.DataFrame(columns=["Datum", "Övning", "Set", "Vikt (kg)", "Reps"])

# Läs in datan när appen startar
df = fetch_data()

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
                    # Skicka datan till Supabase istället för CSV
                    supabase.table("workout_log").insert(nya_rader).execute()
                    st.success(f"Sparade {len(nya_rader)} sets av {vald_ovning} den {valt_datum.strftime('%Y-%m-%d')}!")
                    st.rerun() # Laddar om sidan så att passet syns direkt i arkivet
                else:
                    st.warning("Inga fullständiga sets (både vikt och reps) ifyllda.")

# Läs in datan igen för att grafer och arkiv ska vara uppdaterade
df_uppdaterad = fetch_data()

with flik_grafer:
    st.subheader("Kalkylerat 1RM per övning")
    if not df_uppdaterad.empty:
        df_set1 = df_uppdaterad[df_uppdaterad["Set"] == 1].copy()
        
        if not df_set1.empty:
            df_set1["1RM"] = df_set1.apply(
                lambda rad: rad["Vikt (kg)"] if rad["Reps"] == 1 else rad["Vikt (kg)"] * (1 + rad["Reps"] / 30.0), 
                axis=1
            ).round(1)
            
            df_plot = df_set1.drop_duplicates(subset=["Datum", "Övning"], keep="last")
            unika_ovningar = df_plot["Övning"].unique()
            
            for ovning in unika_ovningar:
                st.markdown(f"### {ovning}")
                
                df_ovning = df_plot[df_plot["Övning"] == ovning].copy()
                
                min_y = float(df_ovning["1RM"].min() - 10)
                max_y = float(df_ovning["1RM"].max() + 10)
                
                base = alt.Chart(df_ovning).encode(
                    x=alt.X('Datum:T', title='Datum'),
                    y=alt.Y('1RM:Q', scale=alt.Scale(domain=[max(0, min_y), max_y]), title='1RM (kg)')
                )
                
                line = base.mark_line(point=True)
                
                text = base.mark_text(
                    align='left',
                    baseline='bottom',
                    dx=5,
                    dy=-5
                ).encode(
                    text=alt.Text('1RM:Q', format='.1f')
                )
                
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
            
            def format_set(rad):
                vikt = int(rad["Vikt (kg)"]) if rad["Vikt (kg)"] == int(rad["Vikt (kg)"]) else rad["Vikt (kg)"]
                reps = int(rad["Reps"])
                return f"{reps} x {vikt}"
            
            df_ovning["Resultat"] = df_ovning.apply(format_set, axis=1)
            
            df_pivot = df_ovning.pivot(index="Datum", columns="Set", values="Resultat")
            
            df_pivot.columns = [f"Set {col}" for col in df_pivot.columns]
            
            df_pivot = df_pivot.reset_index().sort_values(by="Datum", ascending=False)
            df_pivot = df_pivot.fillna("-")
            
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            
        # --- RADERA FUNKTION (Uppdaterad för Supabase) ---
        st.divider()
        st.subheader("🗑️ Hantera felaktiga inmatningar")
        st.write("Välj ett pass nedan för att radera hela loggen (alla sets) för den övningen på det valda datumet.")
        
        del_ovning = st.selectbox("1. Välj övning att radera från", ["-- Välj --"] + list(unika_ovningar_arkiv))
        if del_ovning != "-- Välj --":
            datum_for_ovning = df_uppdaterad[df_uppdaterad["Övning"] == del_ovning]["Datum"].unique()
            del_datum = st.selectbox("2. Välj datum att radera", ["-- Välj --"] + list(datum_for_ovning))
            
            if del_datum != "-- Välj --":
                if st.button(f"Radera {del_ovning} ({del_datum})", type="primary"):
                    # Radera inlägget direkt i Supabase
                    supabase.table("workout_log").delete().eq("Övning", del_ovning).eq("Datum", del_datum).execute()
                    st.rerun()
    else:
        st.info("Ditt arkiv är tomt än så länge.")
