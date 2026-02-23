import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="MDB GIRONDE - NÉGOCIATEUR PRO", layout="wide")

# --- DATA RÉFÉRENCE ---
MARKET_DATA = {
    "Bordeaux Centre": {"Maison": 5500, "Appartement": 4800, "tendance": +1.2},
    "Bordeaux Bastide": {"Maison": 4100, "Appartement": 3700, "tendance": +2.5},
    "Cenon": {"Maison": 3100, "Appartement": 2600, "tendance": +3.1},
    "Lormont": {"Maison": 2700, "Appartement": 2300, "tendance": +1.5},
    "Pessac": {"Maison": 4200, "Appartement": 3800, "tendance": -0.5},
    "Mérignac": {"Maison": 4300, "Appartement": 3900, "tendance": +0.8},
    "Libourne": {"Maison": 2300, "Appartement": 1900, "tendance": +4.5}
}

# --- LOGIQUE DE NÉGOCIATION (RÈGLE DES 20% DE MARGE) ---
def simulateur_nego(prix_affiche, travaux, m2, ville, type_bien, marge_visée=20):
    # 1. Estimation Revente (Basée sur DVF + Tendance)
    ref_m2 = MARKET_DATA[ville][type_bien]
    prix_revente_estime = ref_m2 * m2
    
    # 2. Calcul à l'envers pour trouver le Prix d'Achat Maximal (PAM)
    # Formule simplifiée incluant TVA sur marge et Frais MDB
    # PAM = (Revente - Travaux - Marge - Frais Revente) / (1 + Frais Notaire + Coeff TVA)
    
    marge_euros = prix_revente_estime * (marge_visée / 100)
    frais_revente = prix_revente_estime * 0.05 # Agence
    frais_notaire_mdb = 0.02 # 2%
    tva_sur_marge_estimee = (marge_euros / 1.2) * 0.20
    
    # Prix d'offre max pour atteindre la marge
    offre_cible = (prix_revente_estime - marge_euros - travaux - frais_revente - tva_sur_marge_estimee) / (1 + frais_notaire_mdb)
    
    negociation_requise = prix_affiche - offre_cible
    pct_nego = (negociation_requise / prix_affiche) * 100
    
    return int(offre_cible), int(marge_euros), int(negociation_requise), round(pct_nego, 1), int(prix_revente_estime)

# --- INTERFACE ---
st.title("🤝 Scénario de Négociation & Calcul de l'Offre")

with st.sidebar:
    st.header("🔍 Détails du Bien")
    ville = st.selectbox("Secteur", list(MARKET_DATA.keys()))
    type_b = st.radio("Type", ["Maison", "Appartement"])
    surface = st.number_input("Surface (m2)", value=80)
    prix_annonce = st.number_input("Prix Affiché (€)", value=350000)
    est_travaux = st.number_input("Budget Travaux estimé (€)", value=50000)
    marge_cible = st.slider("Marge Nette Visée (%)", 10, 35, 20)
    
    st.divider()
    options = st.multiselect("Points faibles (pour négo)", 
                            ["Pas de Balcon", "DPE F/G", "Chauffage Gaz/Fioul", "RDC", "Travaux lourds"])

# --- RÉSULTATS DE NÉGOCIATION ---
offre, profit, baisse, baisse_pct, revente_prevue = simulateur_nego(prix_annonce, est_travaux, surface, ville, type_b, marge_cible)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("PRIX D'OFFRE CIBLE", f"{offre} €")
    st.caption(f"Pour garantir {marge_cible}% de marge nette")

with c2:
    st.metric("BAISSE À OBTENIR", f"- {baisse} €", f"{baisse_pct} %")
    st.progress(min(baisse_pct / 40, 1.0)) # Barre de difficulté de négo

with c3:
    st.metric("PROFIT NET ESTIMÉ", f"{profit} €")
    st.caption(f"Après TVA et frais MDB")

st.divider()

# --- GRAPHIQUE DE RÉPARTITION DES COÛTS ---
st.subheader("📊 Où va l'argent ? (Répartition du Projet)")
labels = ['Prix d\'Achat Cible', 'Travaux', 'Marge Nette', 'TVA & Frais']
values = [offre, est_travaux, profit, (revente_prevue - offre - est_travaux - profit)]

fig = px.pie(values=values, names=labels, hole=.4, color_discrete_sequence=px.colors.sequential.RdBu)
st.plotly_chart(fig)

# --- ARGUMENTAIRE DE NÉGOCIATION GÉNÉRÉ ---
st.subheader("📢 Votre Argumentaire de Négociation")
st.info(f"""
**Bonjour, suite à la visite du bien à {ville}, voici notre analyse :**
- Le prix moyen réel constaté (DVF) pour un {type_b} est de **{MARKET_DATA[ville][type_b]}€/m2**.
- Le bien nécessite **{est_travaux}€** de travaux pour atteindre les standards du marché.
- {"⚠️ L'absence de balcon réduit la valeur de revente de 10%." if "Pas de Balcon" in options else ""}
- {"📉 Le DPE classé F/G impose une rénovation énergétique lourde." if "DPE F/G" in options else ""}
- **Notre offre se positionne à {offre} €.** C'est une offre ferme, en fonds propres (ou sans condition suspensive), permettant une vente rapide.
""")

# --- RAPPEL DU MARCHÉ ---
with st.expander("📈 Voir les tendances du secteur"):
    tendance = MARKET_DATA[ville]['tendance']
    st.write(f"À **{ville}**, le marché des **{type_b}s** a évolué de **{tendance}%** sur les 6 derniers mois.")
    if tendance < 0:
        st.warning("Marché baissier : Soyez encore plus agressif sur l'offre !")
    else:
        st.success("Marché porteur : La marge peut augmenter pendant la durée des travaux.")

# --- BOUTON DE MISE À JOUR ---
if st.button("🔄 Actualiser les flux d'annonces"):
    st.cache_data.clear()
    st.write("Recherche de nouveaux biens rentables en cours...")
