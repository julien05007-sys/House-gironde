import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="MDB GIRONDE - IMPORT & ANALYSE", layout="wide")

# --- DONNÉES DE RÉFÉRENCE (DVF & GÉO) ---
MARKET_DATA = {
    "Bordeaux Centre": {"cp": "33000", "Maison": 5500, "Appartement": 4800, "tendance": +1.2, "lat": 44.8378, "lon": -0.5792},
    "Bordeaux Bastide": {"cp": "33100", "Maison": 4100, "Appartement": 3700, "tendance": +2.5, "lat": 44.8415, "lon": -0.5500},
    "Cenon": {"cp": "33150", "Maison": 3100, "Appartement": 2600, "tendance": +3.1, "lat": 44.8567, "lon": -0.5283},
    "Lormont": {"cp": "33310", "Maison": 2700, "Appartement": 2300, "tendance": +1.5, "lat": 44.8774, "lon": -0.5222},
    "Floirac": {"cp": "33270", "Maison": 2900, "Appartement": 2500, "tendance": +2.0, "lat": 44.8364, "lon": -0.5204},
    "Pessac": {"cp": "33600", "Maison": 4200, "Appartement": 3800, "tendance": -0.5, "lat": 44.8061, "lon": -0.6353},
    "Mérignac": {"cp": "33700", "Maison": 4300, "Appartement": 3900, "tendance": +0.8, "lat": 44.8386, "lon": -0.6586},
    "Libourne": {"cp": "33500", "Maison": 2300, "Appartement": 1900, "tendance": +4.5, "lat": 44.9140, "lon": -0.2440}
}

# --- FONCTION DE CALCUL MDB ---
def process_row(row, marche_type):
    try:
        # Nettoyage des noms de colonnes pour l'import Excel
        prix = row.get('prix') or row.get('Prix') or row.get('Valeur') or 0
        bati = row.get('bati') or row.get('surface') or row.get('m2') or row.get('Surface') or 1
        secteur = row.get('secteur') or row.get('ville') or row.get('Ville') or "Cenon"
        terrain = row.get('terrain') or row.get('surface_terrain') or 0
        balcon = row.get('balcon') or False
        piscine = row.get('piscine') or False
        
        # 1. Prix au m2
        p_m2 = prix / bati
        
        # 2. Comparaison DVF & Profit
        ref_m2 = MARKET_DATA.get(secteur, {"Maison": 3000, "Appartement": 2500})[marche_type]
        bonus = (15000 if balcon else 0) + (35000 if piscine else 0)
        revente = (ref_m2 * bati) + bonus
        profit = revente - (prix * 1.02 + 45000 + (revente - prix)*0.15)
        
        # 3. Division
        div = "✅ OUI" if (terrain > 500 and terrain > bati*3) else "❌ NON"
        
        return pd.Series([int(p_m2), int(profit), div])
    except:
        return pd.Series([0, 0, "N/A"])

# --- SIDEBAR (IMPORT & FILTRES) ---
st.sidebar.title("🦅 MDB GIRONDE PILOT")

st.sidebar.subheader("📂 Importer vos données Excel/CSV")
uploaded_file = st.sidebar.file_uploader("Glissez un fichier (Yanport, Castorus, etc.)", type=["xlsx", "csv"])

marche_type = st.sidebar.radio("Marché visé", ["Maison", "Appartement"])
secteur_selected = st.sidebar.selectbox("📍 Choix du Secteur", ["Tous les secteurs"] + list(MARKET_DATA.keys()))

st.sidebar.divider()
budget_max = st.sidebar.number_input("Budget Achat Max (€)", value=600000)
prix_m2_max = st.sidebar.slider("Prix m2 Max autorisé (€)", 1000, 8000, 5000)

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def get_base_data():
    return pd.DataFrame([
        {"source": "LBC", "titre": "Echoppe", "secteur": "Bordeaux Bastide", "prix": 260000, "bati": 75, "terrain": 50, "date": "2026-02-20", "lien": "https://www.leboncoin.fr"},
        {"source": "Orpi", "titre": "Maison divisible", "secteur": "Pessac", "prix": 395000, "bati": 110, "terrain": 980, "date": "2023-09-15", "lien": "https://www.orpi.com"}
    ])

df = get_base_data()

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            imported_df = pd.read_csv(uploaded_file)
        else:
            imported_df = pd.read_excel(uploaded_file)
        st.sidebar.success("✅ Fichier importé avec succès !")
        df = pd.concat([df, imported_df], ignore_index=True)
    except Exception as e:
        st.sidebar.error(f"Erreur d'import : {e}")

# --- ANALYSE ---
if not df.empty:
    df[['Prix_m2', 'Profit_Est', 'Division']] = df.apply(lambda row: process_row(row, marche_type), axis=1)

# Filtres actifs
if secteur_selected != "Tous les secteurs":
    df = df[df['secteur'] == secteur_selected]
df = df[(df['prix'] <= budget_max) & (df['Prix_m2'] <= prix_m2_max)]

# --- DASHBOARD ---
st.title("🚀 Analyseur d'Opportunités MDB")

tab1, tab2, tab3 = st.tabs(["📊 Résultats de Chasse", "🗺️ Marché & Carto", "🤝 Négociateur & PDF"])

with tab1:
    st.subheader(f"{len(df)} biens analysés (Données internes + Imports)")
    st.dataframe(df, use_container_width=True)

with tab2:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Carte de la Gironde")
        m_df = pd.DataFrame([{"Ville": k, "Lat": v['lat'], "Lon": v['lon'], "m2": v[marche_type], "Trend": v['tendance']} for k, v in MARKET_DATA.items()])
        fig = px.scatter_mapbox(m_df, lat="Lat", lon="Lon", color="Trend", size="m2", hover_name="Ville", zoom=9, mapbox_style="carto-positron")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Tendances 6 mois")
        st.line_chart(m_df.set_index("Ville")["Trend"])

with tab3:
    st.subheader("Générateur d'Offre PDF")
    c1, c2 = st.columns(2)
    with c1:
        v_offre = st.selectbox("Secteur de l'Offre", list(MARKET_DATA.keys()))
        p_ann = st.number_input("Prix Annonce (€)", value=300000)
        s_hab = st.number_input("Surface (m2)", value=80)
        t_est = st.number_input("Travaux (€)", value=50000)
    with c2:
        ref_dvf = MARKET_DATA[v_offre][marche_type]
        revente_p = ref_dvf * s_hab
        offre_max = (revente_p - (revente_p * 0.20) - t_est) / 1.05
        st.metric("PRIX D'OFFRE CONSEILLÉ", f"{int(offre_max)} €")
        
        if st.button("Générer PDF d'Offre"):
            # Fonction PDF simplifiée pour éviter les erreurs de flux
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            pdf.cell(200, 10, txt=f"OFFRE D'ACHAT - {v_offre}", ln=True, align='C')
            pdf.cell(200, 10, txt=f"Montant : {int(offre_max)} euros", ln=True)
            st.download_button("📥 Télécharger PDF", pdf.output(dest='S').encode('latin-1'), f"offre_{v_offre}.pdf")

st.info("💡 Conseil : Exportez vos recherches LeBonCoin ou Yanport en Excel et glissez-les dans la barre latérale pour une analyse instantanée.")
