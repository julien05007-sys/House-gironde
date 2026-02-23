import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time

# --- CONFIGURATION DE L'INTERFACE ---
st.set_page_config(page_title="MDB GIRONDE ULTIME", layout="wide")

# --- BASE DE DONNÉES DVF & SECTEURS ---
DVF_REF = {
    "Bordeaux Centre": {"m2": 5200, "cp": "33000"},
    "Bordeaux Bastide": {"m2": 3800, "cp": "33100"},
    "Cenon": {"m2": 2900, "cp": "33150"},
    "Lormont": {"m2": 2600, "cp": "33310"},
    "Floirac": {"m2": 2800, "cp": "33270"},
    "Pessac": {"m2": 3950, "cp": "33600"},
    "Mérignac": {"m2": 4100, "cp": "33700"},
    "Bègles": {"m2": 3600, "cp": "33130"},
    "Villenave": {"m2": 3300, "cp": "33140"},
    "Libourne": {"m2": 2100, "cp": "33500"}
}

# --- LOGIQUE DE GÉNÉRATION DE LIENS RÉELS ---
def generate_lbc_link(secteur, cp, prix_max, bati_min, piscine):
    # Génère un lien LeBonCoin avec les filtres réels
    base_url = "https://www.leboncoin.fr/recherche?"
    piscine_query = "+piscine" if piscine else ""
    return f"{base_url}category=2&locations={secteur}_{cp}&price=min-{prix_max}&square={bati_min}-max&text=maison{piscine_query}"

def generate_c21_link(cp):
    return f"https://www.century21.fr/annonces/achat/cp-{cp}/"

# --- FONCTION DE SIMULATION DE RÉCUPÉRATION (MULTISOURCES) ---
@st.cache_data(ttl=600) 
def fetch_annonces_multisources(ville, rayon, piscine):
    # Simulation d'agrégation (LeBonCoin, Century21, etc.)
    data = [
        {"source": "LeBonCoin", "titre": "Maison avec piscine", "secteur": "Cenon", "prix": 310000, "bati": 90, "terrain": 600, "piscine": True, "date_poste": "2026-02-15", "lien": "https://www.leboncoin.fr/immobilier/245678.htm"},
        {"source": "Century21", "titre": "Pavillon Plain-pied", "secteur": "Cenon", "prix": 265000, "bati": 85, "terrain": 400, "piscine": False, "date_poste": "2025-12-10", "lien": "https://www.century21.fr/annonce/12345"},
        {"source": "Orpi", "titre": "Échoppe à rénover", "secteur": "Bordeaux Bastide", "prix": 290000, "bati": 75, "terrain": 50, "piscine": False, "date_poste": "2026-02-20", "lien": "https://www.orpi.com/annonce/6789"},
        {"source": "LeBonCoin", "titre": "Grande villa", "secteur": "Pessac", "prix": 520000, "bati": 140, "terrain": 1200, "piscine": True, "date_poste": "2026-02-22", "lien": "https://www.leboncoin.fr/immobilier/999.htm"}
    ]
    df = pd.DataFrame(data)
    
    # Filtrage par Piscine
    if piscine:
        df = df[df['piscine'] == True]
    
    # Filtrage par Ville (Simplifié car simulation de rayon)
    if ville != "Toute la Gironde":
        df = df[df['secteur'] == ville]
        
    return df

# --- INTERFACE ---
st.title("🦅 MDB GIRONDE : Sourcing Multi-Sources")

with st.sidebar:
    st.header("🔍 Paramètres de Recherche")
    ville_search = st.selectbox("Ville de départ", ["Toute la Gironde"] + list(DVF_REF.keys()))
    rayon = st.slider("Rayon autour (km)", 0, 50, 10)
    prix_max = st.number_input("Budget Max (€)", value=500000)
    bati_min = st.number_input("Surface Bâti Min (m2)", value=70)
    opt_piscine = st.checkbox("Option Piscine 🏊‍♂️")
    
    st.divider()
    if st.button("🔄 Lancer la recherche / Rafraîchir"):
        st.cache_data.clear()
        st.success("Recherche en cours...")

    st.divider()
    st.subheader("🛠️ Outils de Sourcing Direct")
    cp_target = DVF_REF.get(ville_search, {"cp": "33000"})["cp"]
    lbc_url = generate_lbc_link(ville_search, cp_target, prix_max, bati_min, opt_piscine)
    c21_url = generate_c21_link(cp_target)
    
    st.link_button("👉 Ouvrir LeBonCoin", lbc_url)
    st.link_button("👉 Ouvrir Century21", c21_url)

# --- TRAITEMENT ET AFFICHAGE ---
df = fetch_annonces_multisources(ville_search, rayon, opt_piscine)

# Calculs Métier
df['Prix_m2'] = (df['prix'] / df['bati']).round(0)
def calc_opp(row):
    ref = DVF_REF.get(row['secteur'], {"m2": 3000})['m2']
    diff = ((ref - row['Prix_m2']) / ref) * 100
    return round(diff, 1)

df['Opportunité_%'] = df.apply(calc_opp, axis=1)
df['Vraie_Date'] = pd.to_datetime(df['date_poste'])
df['Ancienneté'] = df['Vraie_Date'].apply(lambda x: "⚠️ REPOSTE (+90j)" if (datetime.now() - x).days > 90 else "✨ Nouveau")

# --- TABLEAU FINAL ---
st.subheader(f"📊 Résultats pour {ville_search} (+{rayon}km)")

# Affichage des cartes d'opportunités
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Meilleure Marge", f"{df['Opportunité_%'].max()}%")
with col2:
    st.metric("Prix m2 Moyen", f"{int(df['Prix_m2'].mean())}€")
with col3:
    st.metric("Biens trouvés", len(df))

# Tableau avec liens cliquables
st.dataframe(
    df,
    column_order=("Ancienneté", "Opportunité_%", "source", "titre", "prix", "Prix_m2", "secteur", "bati", "terrain", "piscine", "lien"),
    use_container_width=True
)

# --- CALCULATEUR DE MARGE AVEC OPTION PISCINE ---
st.divider()
st.subheader("💸 Calculateur de Marge Nette (Spécial Piscine)")
c_a, c_b = st.columns(2)

with c_a:
    p_achat = st.number_input("Prix d'achat", value=250000)
    travaux = st.number_input("Travaux (Rénovation + Chauffage)", value=40000)
    piscine_add = st.checkbox("Ajouter une Piscine ?")
    cout_piscine = 25000 if piscine_add else 0
    
with c_b:
    revente_base = st.number_input("Revente estimée (DVF Médian)", value=350000)
    bonus_piscine = 35000 if (piscine_add or opt_piscine) else 0
    revente_totale = revente_base + bonus_piscine
    
    # Calcul MDB (Frais notaire réduits + TVA sur marge)
    notaire = p_achat * 0.02
    tva_marge = ((revente_totale - p_achat) / 1.2) * 0.20
    marge_net = revente_totale - (p_achat + notaire + travaux + cout_piscine + tva_marge)
    
    st.metric("Marge Nette Estimée", f"{int(marge_net)} €", delta=f"{bonus_piscine}€ via Piscine")

st.info("💡 **Astuce MDB Cenon/Gironde :** Une piscine sur la rive droite (Cenon/Lormont) est un luxe rare qui permet de revendre le bien 15% au-dessus du prix m2 moyen DVF.")
