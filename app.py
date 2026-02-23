import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="MDB GIRONDE - SYSTÈME FINAL", layout="wide")

# --- DONNÉES DE RÉFÉRENCE ---
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

# --- FONCTION EXPORT PDF (CORRIGÉE) ---
def create_pdf(ville, type_b, surface, offre, arguments):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "RAPPORT D'OFFRE D'ACHAT - MDB GIRONDE", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Secteur : {ville} | Type : {type_b}", ln=True)
    pdf.cell(0, 10, f"Surface habitable : {surface} m2", ln=True)
    pdf.cell(0, 10, f"Date : {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"MONTANT DE L'OFFRE : {offre} euros", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 10, f"Arguments de negociation :\n{arguments}")
    return bytes(pdf.output()) # Fix pour AttributeError

# --- GÉNÉRATEUR DE VRAIS LIENS DE RECHERCHE ---
def get_real_links(secteur, marche, prix_max, m2_min, piscine, balcon):
    # Gestion du CP (Gironde entière si "Tous les secteurs")
    cp = MARKET_DATA.get(secteur, {"cp": "d_33"})["cp"]
    if cp == "d_33": loc_lbc = "d_33"
    else: loc_lbc = f"c_{cp}"
    
    # Mots clés
    query = marche.lower()
    if piscine: query += " piscine"
    if balcon: query += " balcon"
    query = query.replace(" ", "%20")
    
    links = {
        "LeBonCoin": f"https://www.leboncoin.fr/recherche?category=2&locations={loc_lbc}&price=min-{prix_max}&square={m2_min}-max&text={query}",
        "Century21": f"https://www.century21.fr/annonces/achat/{'v-' + cp if cp != 'd_33' else ''}/",
        "Orpi": f"https://www.orpi.com/recherche/achat/{marche.lower()}/{cp if cp != 'd_33' else 'gironde'}/",
        "Laforet": f"https://www.laforet.com/acheter/rechercher?location={cp if cp != 'd_33' else '33'}",
        "Guy Hoquet": f"https://www.guy-hoquet.com/achat/{marche.lower()}/{cp if cp != 'd_33' else 'gironde'}"
    }
    return links

# --- SIDEBAR ---
st.sidebar.title("🦅 MDB GIRONDE PILOT")
marche_type = st.sidebar.radio("Marché visé", ["Maison", "Appartement"])
secteur_selected = st.sidebar.selectbox("📍 Choix du Secteur", ["Tous les secteurs"] + list(MARKET_DATA.keys()))

st.sidebar.divider()
budget_max = st.sidebar.number_input("Budget Achat Max (€)", value=500000)
m2_hab_min = st.sidebar.number_input("Surface Habitable Min (m2)", value=70)
prix_m2_max = st.sidebar.slider("Prix m2 Max autorisé (€)", 1500, 8000, 4500)

st.sidebar.divider()
f_piscine = st.sidebar.checkbox("Option Piscine 🏊‍♂️")
f_balcon = st.sidebar.checkbox("Option Balcon / Terrasse ☕")

# --- SOURCING (Simulation d'annonces avec calculs réels) ---
@st.cache_data(ttl=600)
def fetch_annonces():
    # Données simulées (À remplacer par un vrai scraper si besoin)
    data = [
        {"source": "LBC", "titre": "Maison avec Balcon", "secteur": "Cenon", "prix": 245000, "bati": 85, "terrain": 450, "piscine": False, "balcon": True, "chauffage": "Gaz", "date_1ere": "2024-01-10", "lien": "https://www.leboncoin.fr"},
        {"source": "C21", "titre": "Appartement T3 centre", "secteur": "Bordeaux Centre", "prix": 310000, "bati": 65, "terrain": 0, "piscine": False, "balcon": True, "chauffage": "Elec", "date_1ere": "2026-02-10", "lien": "https://www.century21.fr"},
        {"source": "Orpi", "titre": "Maison divisible", "secteur": "Pessac", "prix": 395000, "bati": 110, "terrain": 980, "piscine": True, "balcon": False, "chauffage": "Fioul", "date_1ere": "2023-09-15", "lien": "https://www.orpi.com"},
        {"source": "Laforet", "titre": "Echoppe à rénover", "secteur": "Bordeaux Bastide", "prix": 260000, "bati": 75, "terrain": 50, "piscine": False, "balcon": True, "chauffage": "Gaz", "date_1ere": "2026-02-20", "lien": "https://www.laforet.com"}
    ]
    return pd.DataFrame(data)

df = fetch_annonces()

# --- CALCULS MÉTIERS ---
def process_data(row):
    # 1. Ancienneté
    d1 = pd.to_datetime(row['date_1ere'])
    jours = (datetime.now() - d1).days
    statut = "⚠️ REPOSTE" if jours > 90 else "✨ NOUVEAU"
    
    # 2. Prix m2 & Profit
    p_m2 = row['prix'] / row['bati']
    ref_m2 = MARKET_DATA[row['secteur']][marche_type]
    bonus = (15000 if row['balcon'] else 0) + (30000 if row['piscine'] else 0)
    revente = (ref_m2 * row['bati']) + bonus
    profit = revente - (row['prix'] * 1.02 + 45000 + (revente - row['prix'])*0.15)
    
    # 3. Division
    div = "✅ OUI" if (row['terrain'] > 500 and row['terrain'] > row['bati']*2.5) else "❌ NON"
    
    return pd.Series([int(p_m2), int(profit), div, statut, jours])

df[['Prix_m2', 'Profit_Est', 'Division', 'Statut', 'Jours']] = df.apply(process_data, axis=1)

# Appliquer filtres de la sidebar
if secteur_selected != "Tous les secteurs":
    df = df[df['secteur'] == secteur_selected]
df = df[(df['prix'] <= budget_max) & (df['Prix_m2'] <= prix_m2_max) & (df['bati'] >= m2_hab_min)]
if f_piscine: df = df[df['piscine'] == True]
if f_balcon: df = df[df['balcon'] == True]

# --- DASHBOARD ---
st.title(f"🚀 Sourcing MDB : {secteur_selected}")

tab1, tab2, tab3 = st.tabs(["📋 Opportunités", "🗺️ Analyse Marché", "🤝 Négociateur & Liens"])

with tab1:
    st.subheader(f"Résultats ({len(df)} biens)")
    st.dataframe(df[['Statut', 'Jours', 'Profit_Est', 'source', 'titre', 'prix', 'Prix_m2', 'secteur', 'bati', 'terrain', 'Division', 'chauffage', 'balcon', 'piscine', 'lien']], use_container_width=True)

with tab2:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Carte des Secteurs")
        m_df = pd.DataFrame([{"Ville": k, "Lat": v['lat'], "Lon": v['lon'], "m2": v[marche_type], "Trend": v['tendance']} for k, v in MARKET_DATA.items()])
        fig = px.scatter_mapbox(m_df, lat="Lat", lon="Lon", color="Trend", size="m2", hover_name="Ville", zoom=9, mapbox_style="carto-positron")
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        st.subheader("Tendances (6 mois)")
        st.line_chart(m_df.set_index("Ville")["Trend"])

with tab3:
    st.subheader("🔗 Liens de Sourcing Réels")
    links = get_real_links(secteur_selected, marche_type, budget_max, m2_hab_min, f_piscine, f_balcon)
    cols = st.columns(len(links))
    for i, (name, url) in enumerate(links.items()):
        cols[i].link_button(f"🔍 {name}", url)

    st.divider()
    st.subheader("📄 Générateur d'Offre PDF")
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
        st.metric("PRIX D'OFFRE CIBLE", f"{int(offre_max)} €")
        
        args = f"Secteur : {v_offre}. Prix DVF : {ref_dvf}e/m2. Travaux : {t_est}e. Tendance : {MARKET_DATA[v_offre]['tendance']}%."
        if st.button("Générer PDF"):
            pdf_data = create_pdf(v_offre, marche_type, s_hab, int(offre_max), args)
            st.download_button("📥 Télécharger l'Offre", pdf_data, f"offre_{v_offre}.pdf", "application/pdf")

st.info("Données DVF actualisées / Calculateur de marge MDB / Détection de division.")
