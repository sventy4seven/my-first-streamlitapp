import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import time
import os

# --- KORRIGIERTER UND PLATTFORMUNABHÄNGIGER DATEIPFAD ---
# Stellt sicher, dass die App die Datei im 'data'-Ordner findet, 
# egal ob auf Windows, Linux oder Streamlit Cloud.
DATEI_PFAD = os.path.join(os.path.dirname(__file__), "data", "liga.csv")
# ----------------------------------------------------------------------


# --- 1. DATENLADUNG UND BEREINIGUNG ---

@st.cache_data
def load_and_clean_data(path):
    """Lädt die CSV, weist Spaltennamen zu, bereinigt Datentypen und filtert Nulleinträge."""
    
    try:
        # Achtung: Wird jetzt mit dem korrekten Pfad aufgerufen
        df = pd.read_csv(path, delimiter=';') 
    except Exception as e:
        st.error(f"Fehler beim Laden der CSV-Datei: {e}")
        return pd.DataFrame()
        
    expected_columns = [
        'Saison_Start', 'Saison_Ende', 'Rang', 'Verein', 
        'Spiele_Saison', 
        'Punkte_Aktuell_2er', 
        'Tordifferenz_Saison', 
        'Tore_Saison', 'Gegentore_Saison', 'Siege_Saison', 
        'Unentschieden_Saison', 'Niederlagen_Saison', 
        'Punkte_3er_Regel_Saison', 
        'Punkte_2er_Regel_Saison', 
        'Stadt', 
        'Breitengrad_Str', 'Längengrad_Str',
        'Spiele_Ewig', 
        'Punkte_Aktuell_Ewig', 
        'Tordifferenz_Ewig', 
        'Tore_Ewig', 'Gegentore_Ewig',
        'Siege_Ewig', 'Unentschieden_Ewig', 'Niederlagen_Ewig', 
        'Punkte_3er_Regel_Ewig', 
        'Punkte_2er_Regel_Ewig' 
    ]
    current_col_count = len(df.columns)
    
    if current_col_count == len(expected_columns):
        df.columns = expected_columns
    elif current_col_count > len(expected_columns):
        df.columns = expected_columns + [f'Unnamed_{i}' for i in range(current_col_count - len(expected_columns))]
        df = df.drop(columns=[col for col in df.columns if col.startswith('Unnamed_')], errors='ignore')
    else:
        st.error("Fehler: Falsche Spaltenanzahl.")
        return pd.DataFrame()

    # Typenkonvertierung und Bereinigung
    df['Saison_Start'] = pd.to_numeric(df['Saison_Start'], errors='coerce').astype('Int64')
    df['Saison_Ende'] = pd.to_numeric(df['Saison_Ende'], errors='coerce').astype('Int64')

    def clean_points(s):
        if not pd.api.types.is_string_dtype(s):
             s = s.astype(str)
        return pd.to_numeric(s
                             .str.replace('∘N', '', regex=False)
                             .str.replace('∘O', '', regex=False)
                             .str.replace('Punkte_', '', regex=False),
                             errors='coerce')
                             
    def clean_geo(s):
        if not pd.api.types.is_string_dtype(s):
             s = s.astype(str)
        return pd.to_numeric(s
                             .str.replace('∘N', '', regex=False)
                             .str.replace('∘O', '', regex=False)
                             .str.replace('°N', '', regex=False) 
                             .str.replace('°O', '', regex=False), 
                             errors='coerce')

    df['Punkte_3er_Regel_Ewig'] = clean_points(df['Punkte_3er_Regel_Ewig'])
    df['Punkte_2er_Regel_Ewig'] = clean_points(df['Punkte_2er_Regel_Ewig'])
    df['Punkte_Aktuell'] = clean_points(df['Punkte_Aktuell_2er']) 
    df['Saison'] = df['Saison_Start'].astype(str) + '/' + df['Saison_Ende'].astype(str)
    
    # Bereinigung der Koordinaten
    df['Breitengrad'] = clean_geo(df['Breitengrad_Str'])
    df['Längengrad'] = clean_geo(df['Längengrad_Str'])
    
    # Vereinsnamen vereinheitlichen
    df['Verein'] = df['Verein'].str.replace('VFB Stuttgart', 'VfB Stuttgart', regex=False).str.strip()


    # FINALE REINIGUNG
    df_clean = df.dropna(subset=['Rang', 'Punkte_Aktuell', 'Spiele_Saison'], how='all').copy()
    
    return df_clean

# --- 2. FUNKTIONEN FÜR DIE TABELLENBERECHNUNG ---

def prepare_tables(df, saison_start_jahr, punkt_regel='2er'):
    """Berechnet die aktuelle Saisontabelle und die ewige Tabelle."""
    
    df_current_saison = df[df['Saison_Start'] == saison_start_jahr].copy()
    
    if df_current_saison.empty:
        return pd.DataFrame(), pd.DataFrame(), saison_start_jahr + 1, "Punkte (N/A)"

    saison_ende = df_current_saison['Saison_Ende'].iloc[0]
    df_ewig_final = df[df['Saison_Start'] <= saison_start_jahr].copy()
    df_