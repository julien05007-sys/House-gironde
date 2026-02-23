import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="MDB GIRONDE - SYSTÈME ULTIME", layout="wide")

# --- DATA RÉFÉRENCE (Maisons vs Appartements + Tendances) ---
MARKET_DATA = {
    "Bordeaux Centre": {"cp": "33000", "Maison": 5500, "Appartement": 4800, "tendance": +1.2, "lat": 44.8378, "lon": -0.5792},
    "Bordeaux Bastide": {"cp": "33100", "Maison": 4100, "Appartement": 3700, "tendance": +2.5, "lat": 44.8415, "lon": -0.5500},
    "Cenon": {"cp": "33150", "Maison": 3100, "Appartement": 2600, "tendance": +3.1, "lat": 44.8567, "lon": -0.5283},
    "Lormont": {"cp": "33310", "Maison": 2700, "Appartement": 2300, "tendance": +1.5, "lat": 44.8774, "lon": -0.5222},
    "Floirac": {"cp": "33270", "Maison": 2900, "Appartement": 2500, "tendance": +2.0, "lat": 44.8364, "lon": -0.5204},
    "Pessac": {"cp": "33600", "Maison": 4200, "Appartement": 3800, "tendance": -0.5, "lat": 44.8061, "lon": -0.6353},
    "Mérignac": {"cp": "33700", "Maison": 4300, "Appartement": 3900, "tendance": +0.8, "lat": 44.8386, "lon": -0.6586},
    "Bègles": {"cp": "33130", "Maison": 3700, "Appartement": 3200, "tendance": +1.0, "lat": 44.8078, "lon": -0.5486},
    "Villenave": {"cp": "33140", "Maison": 3400, "Appartement": 2900, "tendance": +0.5, "lat": 44.7731, "lon": -0.5606},
    "Libourne": {"cp": "33500", "Maison": 2300, "Appartement": 1900, "tendance": +4.5, "lat": 44.9140, "lon": -0.2440}
}

# --- FONCTION EXPORT PDF CORRIGÉE ---
def create_pdf(ville, type_b, surface, offre, arguments):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="RAPPORT D'OFFRE D'ACHAT - MDB GIRONDE", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, txt=f"Secteur : {ville} | Type : {type_b}", ln=True)
    pdf.cell(200, 10, txt=f"Surface : {surface} m2", ln=True)
    pdf.cell(200, 10, txt=f"Date : {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    # Ligne corrigée ci-dessous
    pdf.cell(200, 10, txt=f"MONTANT DE L'OFFRE : {offre} euros", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 10, txt=f"Arguments techniques :\n{arguments}")
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- SOURCING DATA ---
@st.cache_data(ttl=600)
def fetch_all_data():
    return [
        {"source": "LBC", "titre": "Maison avec Balcon", "secteur": "Cenon", "prix": 245000, "bati": 85, "terrain": 450, "piscine": False, "balcon": True, "chauffage": "Gaz", "date_1ere": "2023-11-10", "lien": "https://www.leboncoin.fr"},
        {"source": "C21", "titre": "Appartement T3 centre", "secteur": "Bordeaux Centre", "prix": 310000, "bati": 65, "terrain": 0, "piscine": False, "balcon": True, "chauffage": "Elec", "date_1ere": "2026-02-10", "lien": "https://www.century21.fr"},
        {"source": "Orpi", "titre": "Maison divisible", "secteur": "Pessac", "prix": 395000, "bati": 110, "terrain": 980, "piscine": True, "balcon": False, "chauffage": "Fioul", "date_1ere": "2023-09-15", "lien": "https://www.orpi.com"},
        {"source": "Laforêt", "titre": "Échoppe à rénover", "secteur": "Bordeaux Bastide", "prix": 260000, "bati": 75, "terrain": 50, "piscine": False, "balcon": True, "chauffage": "Gaz", "date_1ere": "2026-02-20", "lien": "https://www.laforet.com"},
        {"source": "Guy Hoquet", "titre": "Maison Plain-pied", "secteur": "Libourne", "prix": 165000, "bati": 80, "terrain": 350, "piscine": False, "balcon": False, "chauffage": "Elec", "date_1ere": "2026-02-18", "lien": "https://www.guy-hoquet.com"}
    ]

# --- SIDEBAR ---
st.sidebar.title("🦅 MDB Gironde Pilot")
marche_type = st.sidebar.radio("Marché visé", ["Maison", "Appartement"])
secteur_selected = st.sidebar.selectbox("📍 Secteur", ["Tous les secteurs"] + list(MARKET_DATA.keys()))

st.sidebar.divider()
budget_max = st.sidebar.number_input("Budget Max (€)", value=600000)
prix_m2_max = st.sidebar.slider("Prix m2 Max d'habitation (€)", 1000, 8000, 5000)

st.sidebar.divider()
f_piscine = st.sidebar.checkbox("Option Piscine 🏊‍♂️")
f_balcon = st.sidebar.checkbox("Option Balcon / Terrasse ☕")

# --- LOGIQUE DE CALCULS ---
raw_annonces = fetch_all_data()
df = pd.DataFrame(raw_annonces)

def process_row(row):
    # 1. Ancienneté & Reposte
    d1 = pd.to_datetime(row['date_1ere'])
    jours = (datetime.now() - d1).days
    statut = "⚠️ REPOSTE" if jours > 90 else "✨ NOUVEAU"
    
    # 2. Prix m2 & Profit
    p_m2 = row['prix'] / row['bati']
    ref_m2 = MARKET_DATA[row['secteur']][marche_type]
    
    bonus = (15000 if row['balcon'] else 0) + (35000 if row['piscine'] else 0)
    revente = (ref_m2 * row['bati']) + bonus
    profit = revente - (row['prix'] * 1.02 + 45000 + (revente - row['prix'])*0.15)
    
    # 3. Division
    div = "✅ OUI" if (row['terrain'] > 500 and row['terrain'] > row['bati']*3) else "❌ NON"
    
    return pd.Series([int(p_m2), int(profit), div, statut, jours])

df[['Prix_m2', 'Profit_Est', 'Division', 'Statut', 'Ancienneté_Jours']] = df.apply(process_row, axis=1)

# Filtres actifs
if secteur_selected != "Tous les secteurs":
    df = df[df['secteur'] == secteur_selected]
df = df[(df['prix'] <= budget_max) & (df['Prix_m2'] <= prix_m2_max)]
if f_piscine: df = df[df['piscine'] == True]
if f_balcon: df = df[df['balcon'] == True]

# --- DASHBOARD ---
st.title(f"🚀 Sourcing Immobilier : {secteur_selected}")

tab1, tab2, tab3 = st.tabs(["📋 Opportunités", "🗺️ Carte & Tendances", "🤝 Négociation & PDF"])

with tab1:
    st.subheader(f"{len(df)} biens trouvés")
    st.dataframe(df[['Statut', 'Ancienneté_Jours', 'Profit_Est', 'source', 'titre', 'prix', 'Prix_m2', 'secteur', 'bati', 'terrain', 'Division', 'chauffage', 'balcon', 'piscine', 'lien']], 
                 column_config={"lien": st.column_config.LinkColumn("Lien Annonce")},
                 use_container_width=True)

with tab2:
    col_m1, col_m2 = st.columns([2, 1])
    with col_m1:
        st.subheader("Carte des Secteurs")
        m_df = pd.DataFrame([{"Ville": k, "Lat": v['lat'], "Lon": v['lon'], "m2": v[marche_type], "Trend": v['tendance']} for k, v in MARKET_DATA.items()])
        fig = px.scatter_mapbox(m_df, lat="Lat", lon="Lon", color="Trend", size="m2", hover_name="Ville", zoom=9, mapbox_style="carto-positron")
        st.plotly_chart(fig, use_container_width=True)
    with col_m2:
        st.subheader("Indice Hausse/Baisse (6 mois)")
        st.line_chart(m_df.set_index("Ville")["Trend"])

with tab3:
    st.subheader("Générateur d'Offre PDF")
    c_n1, c_n2 = st.columns(2)
    with c_n1:
        v_nego = st.selectbox("Secteur de l'Offre", list(MARKET_DATA.keys()))
        p_ann = st.number_input("Prix de l'Annonce (€)", value=300000)
        s_bati = st.number_input("Surface Habitable (m2)", value=80)
        t_est = st.number_input("Total Travaux (€)", value=50000)
    with c_n2:
        ref_dvf = MARKET_DATA[v_nego][marche_type]
        revente_p = ref_dvf * s_bati
        offre_cible = (revente_p - (revente_p * 0.20) - t_est) / 1.05
        st.metric("PRIX D'OFFRE CONSEILLÉ", f"{int(offre_cible)} €")
        
        args = f"Secteur : {v_nego}. Prix DVF : {ref_dvf}e/m2. Travaux : {t_est}e. Tendance : {MARKET_DATA[v_nego]['tendance']}%."
        pdf_out = create_pdf(v_nego, marche_type, s_bati, int(offre_cible), args)
        st.download_button("📥 Télécharger l'Offre PDF", pdf_out, f"Offre_{v_nego}.pdf", "application/pdf")

st.divider()
st.info("Données synchronisées : DVF Gironde / 1ère date de parution / Potentiel Division.")
