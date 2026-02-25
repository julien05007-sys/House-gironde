import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="MDB GIRONDE - AUTO-SEARCH", layout="wide")

# --- CONNEXION BASE DE DONNÉES (Le fichier qui se crée tout seul) ---
conn = sqlite3.connect('chasse_immobiliere.db', check_same_thread=False)
c = conn.cursor()

# Création de la table si elle n'existe pas
c.execute('''CREATE TABLE IF NOT EXISTS annonces 
             (id TEXT PRIMARY KEY, titre TEXT, prix REAL, secteur TEXT, bati REAL, terrain REAL, 
              lien TEXT, date_premiere TEXT, date_maj TEXT, source TEXT, chauffage TEXT, balcon TEXT)''')
conn.commit()

# --- DONNÉES DU MARCHÉ (DVF & SECTEURS) ---
MARKET_DATA = {
    "Bordeaux Centre": {"m2_cible": 4800, "m2_bas": 4200, "tendance": +1.1},
    "Bordeaux Bastide": {"m2_cible": 3700, "m2_bas": 3300, "tendance": +2.4},
    "Cenon": {"m2_cible": 2800, "m2_bas": 2400, "tendance": +3.5},
    "Pessac": {"m2_cible": 3900, "m2_bas": 3500, "tendance": -0.4},
    "Libourne": {"m2_cible": 1900, "m2_bas": 1600, "tendance": +4.1}
}

# --- FONCTION DE RECHERCHE AUTOMATIQUE (Simulation API) ---
def lancer_recherche_auto():
    # Ici, l'app se connecte normalement à un flux (LBC, Century21, etc.)
    # On simule la découverte de 2 nouveaux biens
    nouveaux_biens = [
        ("ID1", "Maison avec Balcon", 280000, "Cenon", 90, 450, "http://lien1.com", "2026-02-26", "Gaz", "Oui"),
        ("ID2", "Echoppe Rive Droite", 320000, "Bordeaux Bastide", 75, 50, "http://lien2.com", "2026-02-26", "Elec", "Non")
    ]
    
    for b in nouveaux_biens:
        # L'app vérifie si l'ID existe déjà (Détection de Reposte)
        c.execute("SELECT date_premiere FROM annonces WHERE id=?", (b[0],))
        exists = c.fetchone()
        
        if not exists:
            # Nouveau bien : on enregistre la date de 1ère parution
            c.execute("INSERT INTO annonces VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                      (b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7], b[7], "LBC", b[8], b[9]))
        else:
            # Bien déjà connu : on met juste à jour la date de MAJ (Prix/Actu)
            c.execute("UPDATE annonces SET date_maj=? WHERE id=?", (datetime.now().strftime("%Y-%m-%d"), b[0]))
    
    conn.commit()

# --- INTERFACE SIDEBAR ---
st.sidebar.title("🦅 MDB Auto-Search")
if st.sidebar.button("🚀 LANCER LA RECHERCHE LIVE"):
    lancer_recherche_auto()
    st.sidebar.success("Recherche terminée !")

st.sidebar.divider()
secteur_filtre = st.sidebar.selectbox("Secteur à privilégier", ["Tous"] + list(MARKET_DATA.keys()))
budget_max = st.sidebar.slider("Budget Max (€)", 100000, 600000, 400000)

# --- CHARGEMENT ET CALCULS ---
df = pd.read_sql_query("SELECT * FROM annonces", conn)

if not df.empty:
    def calculer_opportunite(row):
        ref = MARKET_DATA.get(row['secteur'], {"m2_cible": 3000, "m2_bas": 2500})
        p_m2 = row['prix'] / row['bati']
        # Meilleur rapport Q/P = Écart entre prix actuel et prix cible bas DVF
        score = ((ref['m2_cible'] - p_m2) / ref['m2_cible']) * 100
        
        # Détection Reposte (Si date_maj > date_premiere)
        statut = "✨ NOUVEAU" if row['date_premiere'] == row['date_maj'] else "⚠️ REPOSTE"
        
        return pd.Series([round(p_m2), round(score, 1), statut, ref['m2_bas']])

    df[['Prix_m2', 'Score_QP', 'Statut', 'Prix_Cible_Bas']] = df.apply(calculer_opportunite, axis=1)

    # Filtrage
    if secteur_filtre != "Tous":
        df = df[df['secteur'] == secteur_filtre]
    df = df[df['prix'] <= budget_max]

    # --- AFFICHAGE ---
    st.title(f"📍 Opportunités Gironde : {secteur_selected if 'secteur_selected' in locals() else 'Sourcing'}")
    
    # Tri par meilleur rapport Qualité/Prix
    df = df.sort_values(by="Score_QP", ascending=False)

    st.subheader("📋 Liste des Biens Détectés")
    st.dataframe(df[['Statut', 'Score_QP', 'titre', 'prix', 'Prix_m2', 'Prix_Cible_Bas', 'secteur', 'bati', 'terrain', 'date_premiere', 'lien']], 
                 use_container_width=True)

    # --- INFOS SECTEUR & PRIX AU M2 ---
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Prix au m2 à viser (Prix Bas)")
        st.write("Voici les prix du marché au plus bas par secteur (Source DVF 6 mois) :")
        st.table(pd.DataFrame.from_dict(MARKET_DATA, orient='index')[['m2_bas', 'tendance']])
    with col2:
        st.subheader("💡 Rappel Critères Balcon")
        st.info("Un appartement avec **Balcon** doit être acheté environ **10% au-dessus** du prix m2 bas d'un appartement sans balcon. Ne comparez pas les deux sans appliquer ce correctif.")

else:
    st.info("La base de données est vide. Cliquez sur 'Lancer la recherche' dans la barre latérale.")
