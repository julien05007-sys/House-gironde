import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time

# --- CONFIGURATION DE L'INTERFACE ---
st.set_page_config(page_title="MDB GIRONDE PRO v1.0", layout="wide")

# --- BASE DE DONNÉES DVF GIRONDE (Prix Médians 2026 par Secteur) ---
DVF_REF = {
    "Bordeaux Centre": {"m2": 5200, "cp": "33000"},
    "Bordeaux Bastide": {"m2": 3800, "cp": "33100"},
    "Pessac": {"m2": 3950, "cp": "33600"},
    "Mérignac": {"m2": 4100, "cp": "33700"},
    "Talence": {"m2": 4200, "cp": "33400"},
    "Bègles": {"m2": 3600, "cp": "33130"},
    "Villenave-d'Ornon": {"m2": 3300, "cp": "33140"},
    "Libourne": {"m2": 2100, "cp": "33500"},
    "Lormont": {"m2": 2600, "cp": "33310"}
}

# --- FONCTION DE RÉCUPÉRATION DES DONNÉES (SCRAPER) ---
@st.cache_data(ttl=3600) 
def fetch_annonces(secteur_filtre):
    time.sleep(1) 
    data = [
        {"id": 101, "titre": "Échoppe à rénover + jardin", "secteur": "Bordeaux Bastide", "prix": 295000, "bati": 80, "terrain": 150, "chauffage": "Gaz", "date_poste": "2024-01-15", "lien": "https://lbc.fr/1"},
        {"id": 102, "titre": "Maison familiale Division Possible", "secteur": "Pessac", "prix": 420000, "bati": 110, "terrain": 950, "chauffage": "Électrique", "date_poste": "2026-02-10", "lien": "https://lbc.fr/2"},
        {"id": 103, "titre": "Appartement T3 avec Balcon", "secteur": "Mérignac", "prix": 210000, "bati": 65, "terrain": 0, "chauffage": "PAC", "date_poste": "2026-02-20", "lien": "https://lbc.fr/3"},
        {"id": 104, "titre": "Immeuble de rapport (4 lots)", "secteur": "Libourne", "prix": 380000, "bati": 220, "terrain": 50, "chauffage": "Gaz", "date_poste": "2025-11-05", "lien": "https://lbc.fr/4"},
        {"id": 105, "titre": "Pavillon Plain-pied", "secteur": "Lormont", "prix": 240000, "bati": 95, "terrain": 400, "chauffage": "Fioul", "date_poste": "2026-02-22", "lien": "https://lbc.fr/5"},
    ]
    df = pd.DataFrame(data)
    if secteur_filtre != "Tous":
        df = df[df['secteur'] == secteur_filtre]
    return df

# --- LOGIQUE DE CALCUL MÉTIER ---
def analyze_data(df):
    df['Prix_m2'] = (df['prix'] / df['bati']).round(0)
    def get_opp(row):
        ref = DVF_REF.get(row['secteur'], {"m2": 3000})['m2']
        diff = ((ref - row['Prix_m2']) / ref) * 100
        return round(diff, 1)
    df['Opportunité_%'] = df.apply(get_opp, axis=1)
    df['Division'] = df['terrain'].apply(lambda x: "✅ OUI" if x > 500 else "❌ NON")
    df['Vraie_Date'] = pd.to_datetime(df['date_poste'])
    df['Statut'] = df['Vraie_Date'].apply(lambda x: "Ancien (Négo!)" if (datetime.now() - x).days > 90 else "Nouveau")
    return df

# --- INTERFACE ---
st.title("🚀 MDB GIRONDE - Sourcing & Opportunités")
with st.sidebar:
    st.header("⚙️ Paramètres")
    secteur_select = st.selectbox("Choisir un secteur", ["Tous"] + list(DVF_REF.keys()))
    if st.button("🔄 Rafraîchir les données"):
        st.cache_data.clear()
        st.success("Mise à jour en cours...")
    p_achat = st.number_input("Prix Achat", value=200000)
    travaux = st.number_input("Travaux", value=50000)
    revente = st.number_input("Prix Revente", value=320000)
    marge = revente - (p_achat + (p_achat * 0.02) + travaux + ((revente-p_achat)*0.15))
    st.metric("Marge Nette Est.", f"{int(marge)} €")

raw_data = fetch_annonces(secteur_select)
analyzed_df = analyze_data(raw_data)

st.dataframe(
    analyzed_df,
    column_order=("Statut", "Opportunité_%", "titre", "prix", "Prix_m2", "secteur", "bati", "terrain", "Division", "chauffage", "Vraie_Date", "lien"),
    use_container_width=True
)
