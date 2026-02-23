import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from fpdf import FPDF
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="MDB GIRONDE - SYSTÈME INTÉGRAL", layout="wide")

# --- DATA RÉFÉRENCE (Maisons vs Appartements + Tendances + Géo) ---
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

# --- FONCTION EXPORT PDF ---
def create_pdf(ville, type_b, surface, offre, arguments):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="RAPPORT D'OFFRE D'ACHAT - MDB GIRONDE", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, txt=f"Secteur : {ville} | Type : {type_b}", ln=True)
    pdf.cell(200, 10, txt=f"Surface : {surface} m2 | Date : {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt=f"MONTANT DE L'OFFRE : {of
