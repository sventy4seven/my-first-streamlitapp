import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import time

# ⚠️ DER KORRIGIERTE ABSOLUTE PFAD
# Passen Sie diesen Pfad gegebenenfalls an Ihre lokale Struktur an.
DATEI_PFAD = 'data/liga.csv'
# ----------------------------------------------------------------------


# --- 1. DATENLADUNG UND BEREINIGUNG ---

@st.cache_data
def load_and_clean_data(path):
    """Lädt die CSV, weist Spaltennamen zu, bereinigt Datentypen und filtert Nulleinträge."""
    
    try:
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

# --- 2. FUNKTIONEN FÜR DIE TABELLENBERECHNUNG (Unverändert) ---

def prepare_tables(df, saison_start_jahr, punkt_regel='2er'):
    """Berechnet die aktuelle Saisontabelle und die ewige Tabelle."""
    
    df_current_saison = df[df['Saison_Start'] == saison_start_jahr].copy()
    
    if df_current_saison.empty:
        return pd.DataFrame(), pd.DataFrame(), saison_start_jahr + 1, "Punkte (N/A)"

    saison_ende = df_current_saison['Saison_Ende'].iloc[0]
    df_ewig_final = df[df['Saison_Start'] <= saison_start_jahr].copy()
    df_ewig_final = df_ewig_final.sort_values(['Verein', 'Saison_Start', 'Rang'], ascending=[True, True, True])
    df_ewig_final = df_ewig_final.drop_duplicates(subset=['Verein'], keep='last').copy()
    
    if punkt_regel == '2er':
        punkte_ewig_col = 'Punkte_2er_Regel_Ewig'
        punkt_titel = "Punkte (2-Punkte-Regel)"
    else:
        punkte_ewig_col = 'Punkte_3er_Regel_Ewig'
        punkt_titel = "Punkte (3-Punkte-Regel)"

    df_ewig_table = df_ewig_final.copy()
    df_ewig_table[punkte_ewig_col] = df_ewig_table[punkte_ewig_col].fillna(0)
    
    df_ewig_table = df_ewig_table.sort_values(
        by=[punkte_ewig_col, 'Tordifferenz_Ewig', 'Tore_Ewig'],
        ascending=[False, False, False]
    ).reset_index(drop=True)
    
    df_ewig_table['Rang'] = df_ewig_table.index + 1
    
    df_current_disp = df_current_saison[[
        'Rang', 'Verein', 'Spiele_Saison', 'Punkte_Aktuell', 'Tordifferenz_Saison', 
        'Tore_Saison', 'Gegentore_Saison', 'Siege_Saison', 'Unentschieden_Saison', 'Niederlagen_Saison'
    ]].copy()
    df_current_disp.columns = ['Rang', 'Verein', 'Spiele', 'Punkte', 'Tordifferenz', 'Tore', 'Gegentore', 'Siege', 'Unentschieden', 'Niederlagen']
    
    df_ewig_disp = df_ewig_table[[
        'Rang', 'Verein', 'Spiele_Ewig', punkte_ewig_col, 'Tordifferenz_Ewig', 
        'Tore_Ewig', 'Gegentore_Ewig', 'Siege_Ewig', 'Unentschieden_Ewig', 'Niederlagen_Ewig'
    ]].copy()
    df_ewig_disp.columns = ['Rang', 'Verein', 'Spiele', 'Punkte', 'Tordifferenz', 'Tore', 'Gegentore', 'Siege', 'Unentschieden', 'Niederlagen']
    
    return df_current_disp, df_ewig_disp, saison_ende, punkt_titel

def plot_tables(df_current, df_ewig, punkt_titel, saison_str):
    """Erstellt den Plotly Subplot mit zwei Tabellen nebeneinander."""
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'table'}, {'type': 'table'}]],
        subplot_titles=[
            f'**Bundesliga Saison {saison_str}**',
            f'**Ewige Tabelle (kumuliert bis {saison_str}) – {punkt_titel}**'
        ]
    )
    
    def create_plotly_table(df):
        header = dict(
            values=['**' + col + '**' for col in df.columns],
            fill_color='lightgray',
            align='center',
            line_color='darkslategray',
            line_width=1,
            height=30,
            font=dict(color='black', size=12)
        )
        cells = dict(
            values=[df[col] for col in df.columns],
            fill_color=[['white', 'lightcyan'] * (len(df) // 2 + 1)][0][:len(df)],
            align='center',
            line_color='darkslategray',
            line_width=1,
            height=25,
            font=dict(color='black', size=11)
        )
        return go.Table(header=header, cells=cells)

    fig.add_trace(create_plotly_table(df_current), row=1, col=1)
    fig.add_trace(create_plotly_table(df_ewig), row=1, col=2)

    fig.update_layout(
        title_text="**Bundesliga Analyse: Saison vs. Ewige Tabelle**",
        height=850, 
        margin=dict(l=20, r=20, t=80, b=20)
    )

    return fig

# --- 3. FUNKTIONEN FÜR DIE KARTE (BEREINIGT) ---

@st.cache_data
def get_all_championship_locations(df):
    """
    Berechnet die Basis-Daten aller Meisterschaften, gruppiert nach Geo-Koordinaten.
    Diese Daten sind unabhängig vom Slider-Wert und werden nur einmal berechnet.
    """
    # 1. Alle Meister (Rang 1) filtern
    df_champions = df[df['Rang'] == 1].copy()
    
    # 2. Geo-Key erstellen
    df_champions['Geo_Key'] = df_champions['Breitengrad'].round(4).astype(str) + ',' + df_champions['Längengrad'].round(4).astype(str)

    # 3. Aggregieren pro Standort
    # Aggregiert alle Saisons und Vereine, die an einem Geo_Key gewonnen haben
    bubble_base_data = df_champions.groupby('Geo_Key').agg(
        {
            'Breitengrad': 'first',
            'Längengrad': 'first',
            'Saison_Start': lambda x: sorted(x.tolist()), # Liste aller Meisterschaftsjahre
            'Verein': lambda x: sorted(x.unique())
        }
    ).reset_index()
    
    return bubble_base_data

def plot_map_with_history(df_main, df_bubble_base, saison_start_jahr):
    """
    Erstellt die Landkarte mit den aktuellen Vereinen und den historischen
    Meisterschafts-Bubbles (Größe und Transparenz nach Dominanz).
    """
    
    # 1. Aktuelle Vereine für die gewählte Saison filtern
    df_current_map = df_main[df_main['Saison_Start'] == saison_start_jahr].copy()
    
    # 2. Dynamische Kumulation der Bubbles bis zur gewählten Saison
    bubble_data_final = []
    
    for _, row in df_bubble_base.iterrows():
        # Zähle, wie viele Meisterschaften an diesem Standort BIS zum aktuellen Jahr stattfanden
        championships_count = sum(1 for year in row['Saison_Start'] if year <= saison_start_jahr)
        
        if championships_count > 0:
            bubble_data_final.append({
                'Breitengrad': row['Breitengrad'],
                'Längengrad': row['Längengrad'],
                'Meisterschaften_Kumuliert': championships_count,
                'Verein_Text': ' / '.join(row['Verein'])
            })
            
    df_bubbles_final = pd.DataFrame(bubble_data_final)

    # --- Plotly Mapbox Konfiguration ---
    fig = go.Figure()

    BASE_MARKER_SIZE = 8
    
    # 1. Meisterschafts-Bubbles (Historische Dominanz)
    if not df_bubbles_final.empty:
        # Die Größe der Bubble skaliert mit der Anzahl der Meisterschaften
        bubble_size_factor = 2 
        
        fig.add_trace(go.Scattermapbox(
            lat=df_bubbles_final['Breitengrad'],
            lon=df_bubbles_final['Längengrad'],
            mode='markers',
            marker=dict(
                size=df_bubbles_final['Meisterschaften_Kumuliert'] * bubble_size_factor + 5, # Minimumgröße + Skalierung
                color='#FFCC00', # Gold/Gelb
                opacity=0.4, 
                symbol='circle',
            ),
            hoverinfo='text',
            text=df_bubbles_final.apply(
                lambda row: f"<b>{row['Verein_Text']}</b><br>Meisterschaften: {row['Meisterschaften_Kumuliert']}", 
                axis=1
            ),
            name='Meisterschaften (Kumuliert)'
        ))

    # 2. Aktuelle Vereins-Punkte (Aktuelle Saison)
    if not df_current_map.empty:
        
        def rank_color(rank):
            if rank == 1:
                return '#990000' # Dunkelrot für Meister
            elif rank >= 16:
                return '#FF4444' # Hellrot für Abstiegsplätze
            else:
                return '#003366' # Blau
        
        marker_colors = df_current_map['Rang'].apply(rank_color).tolist()
        
        fig.add_trace(go.Scattermapbox(
            lat=df_current_map['Breitengrad'],
            lon=df_current_map['Längengrad'],
            mode='markers',
            marker=dict(
                size=BASE_MARKER_SIZE,
                color=marker_colors,
                opacity=1,
                symbol='circle',
            ),
            hoverinfo='text',
            text=df_current_map.apply(
                lambda row: f"<b>{row['Verein']}</b><br>Rang: {row['Rang']}<br>Punkte: {row['Punkte_Aktuell']}", 
                axis=1
            ),
            name=f'Vereine Saison {saison_start_jahr}'
        ))
        
    # Standard-Einstellungen für die Karte
    fig.update_layout(
        title_text=f"Bundesliga-Vereine und Meisterschafts-Dominanz bis Saison {saison_start_jahr}",
        autosize=True,
        hovermode='closest',
        showlegend=True,
        mapbox=dict(
            style="carto-positron", 
            center=dict(lat=51.1657, lon=10.4515), 
            zoom=5
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=700
    )
    
    return fig

# Die Funktion plot_vereinsvergleich wurde beibehalten (nicht gezeigt, da sie nicht geändert wurde)
def plot_vereinsvergleich(df, vereine_liste, start_jahr, end_jahr, punkt_regel):
     # ... (Ihre Implementierung von plot_vereinsvergleich hier einfügen)
     punkte_col = f'Punkte_{punkt_regel}_Regel_Ewig' 
     all_seasons = pd.DataFrame(
         {'Saison_Start': range(1963, end_jahr + 1)}
     )
     fig = go.Figure()
     colors = ['#003366', '#FFCC00', '#006633', '#CC0000', '#666666', '#9900CC', '#00CCFF']
     
     for i, verein in enumerate(vereine_liste):
         df_verein = df[
             (df['Verein'] == verein)
         ].copy()
         df_verein_agg = df_verein.sort_values(by='Saison_Start', ascending=True).drop_duplicates(subset=['Saison_Start'], keep='last')
         df_full_timeline = all_seasons.merge(
             df_verein_agg[['Saison_Start', punkte_col]], 
             on='Saison_Start', 
             how='left'
         )
         df_full_timeline[punkte_col] = df_full_timeline[punkte_col].fillna(method='ffill') 
         df_full_timeline[punkte_col] = df_full_timeline[punkte_col].fillna(0)
         
         df_plot_final = df_full_timeline[
             (df_full_timeline['Saison_Start'] >= start_jahr) &
             (df_full_timeline['Saison_Start'] <= end_jahr)
         ]

         fig.add_trace(go.Scatter(
             x=df_plot_final['Saison_Start'],
             y=df_plot_final[punkte_col],
             mode='lines+markers',
             name=verein,
             line=dict(color=colors[i % len(colors)], width=3),
             hovertemplate = f"<b>{verein}</b><br>Saison: %{{x}}<br>Ewige Punkte: %{{y:.0f}}<extra></extra>"
         ))

     regeltitel = '2-Punkte-Regel' if punkt_regel == '2er' else '3-Punkte-Regel'
     fig.update_layout(
         title=f'Kumulierter Punkteverlauf der Vereine ({regeltitel})',
         xaxis_title='Saison (Startjahr)',
         yaxis_title='Ewige Punkte (Kumuliert)',
         hovermode="x unified",
         height=600,
         margin=dict(t=50, b=50),
         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
     )
     return fig
# --- 4. STREAMLIT-LAYOUT ---

st.set_page_config(layout="wide", page_title="Bundesliga Analyse")

df = load_and_clean_data(DATEI_PFAD) 

if df.empty:
    st.error("Daten konnten nicht geladen werden oder sind leer.")
    st.stop()

st.title("⚽ Bundesliga Analyse: Saison, Ewige Tabelle und Historische Landkarte")

# VORBEREITUNG FÜR MAPPE (Wird nur einmal ausgeführt)
df_bubble_base = get_all_championship_locations(df)

min_jahr = int(df['Saison_Start'].min())
max_jahr = int(df['Saison_Start'].max())
saison_options = sorted(df['Saison_Start'].unique())


# --- STREAMLIT TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Tabellen", "📈 Vereins-Entwicklung", "🗺️ Historische Landkarte"])


# --- TAB 1 & 2 (Unverändert) ---
with tab1:
    st.sidebar.header("Kontrollen (Tabellen)")

    selected_saison_start = st.sidebar.select_slider(
        'Wählen Sie die Saison (Startjahr):',
        options=saison_options,
        value=saison_options[-1] if saison_options else min_jahr,
        key='tab1_saison' 
    )

    selected_punkt_regel = st.sidebar.radio(
        "Ewige Tabelle: Punkte-Regel",
        ('2er', '3er'),
        index=0,
        key='tab1_regel' 
    )

    df_aktuell, df_ewig_tab, saison_ende, punkt_titel = prepare_tables(
        df, selected_saison_start, selected_punkt_regel
    )

    if df_aktuell.empty or df_ewig_tab.empty:
        st.warning("Keine vollständigen Daten für die gewählte Saison gefunden.")
    else:
        saison_str = f"{selected_saison_start}/{str(saison_ende)[-2:]}"
        fig_final = plot_tables(df_aktuell, df_ewig_tab, punkt_titel, saison_str)
        st.plotly_chart(fig_final, use_container_width=True)

with tab2:
    st.header("Entwicklung der Ewigen Punkte im Zeitverlauf")

    df_ewig_end = prepare_tables(df, max_jahr, '3er')[1] 
    top_5_vereine = df_ewig_end['Verein'].head(5).tolist()
    alle_vereine = sorted(df['Verein'].unique())

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.info(f"Top 5 (3er-Regel, Stand {max_jahr}/{max_jahr+1}):")
        st.markdown('\n'.join([f'- {v}' for v in top_5_vereine]))
    
    with col_b:
        default_selection = list(set(top_5_vereine + ['VfB Stuttgart', 'Werder Bremen', 'Borussia Neunkirchen']))
        zusatz_vereine = st.multiselect(
            "Wählen Sie Vereine für den Vergleich:",
            options=alle_vereine,
            default=[v for v in default_selection if v in alle_vereine],
            max_selections=7
        )
        final_vereins_liste = zusatz_vereine
        
    if not final_vereins_liste:
        st.warning("Bitte wählen Sie mindestens einen Verein aus.")
    else:
        st.subheader("Zeitsteuerung")
        start_jahr_slider, end_jahr_slider = st.slider(
            'Saison-Bereich (Startjahr):',
            min_value=min_jahr,
            max_value=max_jahr,
            value=(min_jahr, max_jahr),
            key='saison_range_slider'
        )
        regelung_vergleich = st.radio(
            "Punkte-Regel für den Vergleich:",
            ('2er', '3er'),
            index=1, 
            key='regelung_vergleich'
        )

        fig_vergleich = plot_vereinsvergleich(
            df, 
            final_vereins_liste, 
            start_jahr_slider, 
            end_jahr_slider, 
            regelung_vergleich
        )
        st.plotly_chart(fig_vergleich, use_container_width=True)


# --- TAB 3: HISTORISCHE LANDKARTE ---
with tab3:
    st.header("🗺️ Bundesliga-Landkarte und historische Dominanz")

    # Nur noch der Schieberegler
    map_saison = st.slider(
        'Saison (Startjahr) zur Anzeige der aktuellen Vereine und kumulierten Meisterschaften:',
        min_value=min_jahr,
        max_value=max_jahr,
        value=max_jahr,
        step=1,
        key='map_slider_final'
    )
    
    # Plotten der Karte
    fig_map = plot_map_with_history(df, df_bubble_base, map_saison)
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("---")
    st.markdown("""
        **Erläuterung der Karte:**
        * **Kleine Punkte (Fest):** Zeigen die 18 Vereine, die in der **eingestellten Saison** (Slider) in der 1. Bundesliga spielten.
        * **Große, transparente Bubbles (Gelb/Gold):** Zeigen die **kumulierte Anzahl an Meisterschaften (Rang 1)** an diesem Standort **bis zur eingestellten Saison**. Die Blase wächst mit jeder weiteren Meisterschaft in dieser Region (z.B. München: FC Bayern + 1860).
    """)