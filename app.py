import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="MDB GIRONDE - DASHBOARD COMPLET", layout="wide")

# --- DATA RÉFÉRENCE DVF & MARCHÉ ---
MARKET_DATA = {
    "Bordeaux Centre": {"m2": 5200, "cp": "33000", "tendance": +1.2},
    "Bordeaux Bastide": {"m2": 3900, "cp": "33100", "tendance": +2.5},
    "Cenon": {"m2": 3000, "cp": "33150", "tendance": +3.1},
    "Lormont": {"m2": 2700, "cp": "33310", "tendance": +1.5},
    "Floirac": {"m2": 2900, "cp": "33270", "tendance": +2.0},
    "Pessac": {"m2": 4100, "cp": "33600", "tendance": -0.5},
    "Mérignac": {"m2": 4200, "cp": "33700", "tendance": +0.8},
    "Bègles": {"m2": 3700, "cp": "33130", "tendance": +1.0},
    "Villenave": {"m2": 3400, "cp": "33140", "tendance": +0.5},
    "Libourne": {"m2": 2200, "cp": "33500", "tendance": +4.5}
}

# --- FONCTION EXPORT PDF ---
def create_pdf(ville, type_b, surface, offre, arguments):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="RAPPORT D'OFFRE D'ACHAT - MDB GIRONDE", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, txt=f"Secteur : {ville}", ln=True)
    pdf.cell(200, 10, txt=f"Type de bien : {type_b} de {surface} m2", ln=True)
    pdf.cell(200, 10, txt=f"Date : {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt=f"MONTANT DE L'OFFRE : {offre} euros", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 10, txt=f"Arguments de negociation :\n{arguments}")
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- SIMULATION DE SOURCING (TABLEAU D'ANNONCES) ---
@st.cache_data(ttl=600)
def get_all_annonces(secteur_choisi, type_b):
    # Simule une base de données d'annonces
    data = [
        {"source": "LBC", "titre": "Maison avec Balcon", "secteur": "Cenon", "prix": 245000, "bati": 85, "terrain": 400, "piscine": False, "balcon": True, "date": "2026-02-10"},
        {"source": "C21", "titre": "Appartement T3 centre", "secteur": "Bordeaux Centre", "prix": 310000, "bati": 65, "terrain": 0, "piscine": False, "balcon": False, "date": "2026-01-20"},
        {"source": "Orpi", "titre": "Maison divisible", "secteur": "Pessac", "prix": 390000, "bati": 110, "terrain": 900, "piscine": True, "balcon": False, "date": "2025-12-15"},
        {"source": "LBC", "titre": "Investissement Bastide", "secteur": "Bordeaux Bastide", "prix": 215000, "bati": 55, "terrain": 0, "piscine": False, "balcon": True, "date": "2026-02-22"},
        {"source": "LBC", "titre": "Maison Libourne", "secteur": "Libourne", "prix": 165000, "bati": 80, "terrain": 350, "piscine": False, "balcon": False, "date": "2026-02-18"}
    ]
    df = pd.DataFrame(data)
    if secteur_choisi != "Tous les secteurs":
        df = df[df['secteur'] == secteur_choisi]
    return df

# --- INTERFACE LATÉRALE ---
st.sidebar.title("🦅 MDB Gironde Pilot")
marche_type = st.sidebar.radio("Marché visé", ["Maison", "Appartement"])
secteurs_dispos = ["Tous les secteurs"] + list(MARKET_DATA.keys())
secteur_selected = st.sidebar.selectbox("📍 Choix du Secteur", secteurs_dispos)

st.sidebar.divider()
st.sidebar.subheader("💎 Options de recherche")
f_piscine = st.sidebar.checkbox("Piscine")
f_balcon = st.sidebar.checkbox("Balcon")

# --- TABLEAU DE SOURCING (L'ANNONCEUR) ---
st.title(f"🔍 Chasse Immobilière : {secteur_selected}")
df_annonces = get_all_annonces(secteur_selected, marche_type)

# Filtres Piscine / Balcon
if f_piscine: df_annonces = df_annonces[df_annonces['piscine'] == True]
if f_balcon: df_annonces = df_annonces[df_annonces['balcon'] == True]

# Calcul de rentabilité pour le tableau
def calc_quick_profit(row):
    ref_m2 = MARKET_DATA.get(row['secteur'], {"m2": 3000})['m2']
    bonus = (15000 if row['balcon'] else 0) + (30000 if row['piscine'] else 0)
    revente = (ref_m2 * row['bati']) + bonus
    profit = revente - (row['prix'] * 1.15) # Estimation rapide frais + travaux
    return int(profit)

df_annonces['Profit_Estimé'] = df_annonces.apply(calc_quick_profit, axis=1)
df_annonces['Prix_m2'] = (df_annonces['prix'] / df_annonces['bati']).astype(int)

st.subheader("📋 Opportunités Détectées (Classées par Profit)")
st.dataframe(df_annonces.sort_values("Profit_Estimé", ascending=False), use_container_width=True)

# --- NÉGOCIATEUR PRO ---
st.divider()
st.header("🤝 Module de Négociation & Offre PDF")

col_n1, col_n2 = st.columns(2)

with col_n1:
    st.subheader("📊 Calcul de l'offre")
    target_secteur = st.selectbox("Secteur pour l'offre", list(MARKET_DATA.keys()))
    target_prix = st.number_input("Prix Affiché (€)", value=300000)
    target_bati = st.number_input("m2 Bâtiment", value=80)
    target_travaux = st.number_input("Estimation Travaux (€)", value=40000)
    marge_voulue = st.slider("Marge Nette Visée (%)", 10, 30, 20)

with col_n2:
    st.subheader("💡 Résultat de l'analyse")
    ref_m2 = MARKET_DATA[target_secteur]['m2']
    revente_finale = ref_m2 * target_bati
    
    # Calcul Offre Max (PAM)
    offre_max = (revente_finale - (revente_finale * (marge_voulue/100)) - target_travaux) / 1.05
    st.metric("PRIX D'OFFRE CIBLE", f"{int(offre_max)} €", f"-{int(target_prix - offre_max)}€")
    
    # Argumentaire
    txt_args = f"Le prix m2 reel est de {ref_m2}e. Les travaux sont de {target_travaux}e. Le marche est a {MARKET_DATA[target_secteur]['tendance']}%."
    
    # Bouton PDF
    pdf_data = create_pdf(target_secteur, marche_type, target_bati, int(offre_max), txt_args)
    st.download_button(label="📥 Télécharger le Rapport d'Offre (PDF)", 
                       data=pdf_data, 
                       file_name=f"offre_{target_secteur}.pdf", 
                       mime="application/pdf")

# --- CARTE & TENDANCE ---
st.divider()
st.subheader("📈 Tendances Gironde (6 mois)")
map_df = pd.DataFrame([{"Ville": k, "m2": v['m2'], "Tendance": v['tendance']} for k, v in MARKET_DATA.items()])
st.line_chart(map_df.set_index("Ville")["Tendance"])
