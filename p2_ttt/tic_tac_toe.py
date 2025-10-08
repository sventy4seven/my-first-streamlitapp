import streamlit as st

# =========================================================================
# 1. SPIELLOGIK (ANGEPASSTE FUNKTIONEN AUS DEINEM CODE)
# =========================================================================

# Zug machen (Unverändert, operiert auf dem übergebenen Brett)
def mache_zug(brett, aktueller_spieler, zeile, spalte):
    if brett[zeile][spalte] == ' ':
        brett[zeile][spalte] = aktueller_spieler
        return True
    return False

# Gewinn überprüfen (Unverändert)
def pruefe_gewonnen(brett, aktueller_spieler):
    # Zeilen prüfen
    for zeile in range(3):
        if brett[zeile][0] == brett[zeile][1] == brett[zeile][2] == aktueller_spieler:
            return True
    # Spalten prüfen
    for spalte in range(3):
        if brett[0][spalte] == brett[1][spalte] == brett[2][spalte] == aktueller_spieler:
            return True
    # Diagonalen prüfen
    if (brett[0][0] == brett[1][1] == brett[2][2] == aktueller_spieler) or \
       (brett[0][2] == brett[1][1] == brett[2][0] == aktueller_spieler):
            return True
    return False

# Prüfe auf Unentschieden (Unverändert)
def pruefe_unentschieden(brett):
    for zeile in brett:
        if ' ' in zeile:
            return False
    return True

# Funktion zum Zurücksetzen des Spiels
def starte_neues_spiel():
    st.session_state.clear()
    # Der Zustand wird beim nächsten Rerun neu initialisiert

# =========================================================================
# 2. HAUPT-LOGIK & ZUSTANDSVERWALTUNG FÜR STREAMLIT
# =========================================================================

# Zustand initialisieren, falls das Spiel neu geladen wird
if 'board' not in st.session_state:
    st.session_state.board = [[' ', ' ', ' '], [' ', ' ', ' '], [' ', ' ', ' ']]
    st.session_state.player = 'X'
    st.session_state.game_active = True
    st.session_state.result = "Das Spiel läuft..."

# Diese Funktion wird beim Klick auf einen Button ausgeführt
def handle_click(r, c):
    # Nur handeln, wenn das Spiel aktiv ist
    if st.session_state.game_active:
        if mache_zug(st.session_state.board, st.session_state.player, r, c):

            # Nach dem Zug den Gewinn prüfen
            if pruefe_gewonnen(st.session_state.board, st.session_state.player):
                st.session_state.game_active = False
                st.session_state.result = f'🎉 Spieler {st.session_state.player} hat gewonnen!'
            
            # Unentschieden prüfen
            elif pruefe_unentschieden(st.session_state.board):
                st.session_state.game_active = False
                st.session_state.result = '🤝 Unentschieden! Kein Spieler hat gewonnen.'
            
            # Spieler wechseln
            else:
                st.session_state.player = 'O' if st.session_state.player == 'X' else 'X'
            
            # Streamlit neu laden, um den neuen Zustand anzuzeigen
            # st.rerun() # Ist oft nicht nötig, da Button-Klicks ohnehin ein Rerun auslösen

# =========================================================================
# 3. STREAMLIT UI (RENDER-LOGIK)
# =========================================================================

st.title("Tic-Tac-Toe App")

# Anzeige des aktuellen Status
if st.session_state.game_active:
    st.info(f"Aktueller Spieler: **{st.session_state.player}**")
else:
    st.success(st.session_state.result)
    st.button('Neues Spiel starten', on_click=starte_neues_spiel)

st.markdown("---")

# Das 3x3 Gitter (Brett) rendern
for r in range(3):
    # Erstellt 3 gleich große Spalten für die Zeile
    cols = st.columns(3)
    for c in range(3):
        field = st.session_state.board[r][c]
        
        # Leere Felder sind klickbare Buttons
        if field == ' ' and st.session_state.game_active:
            # Button, der handle_click mit den Koordinaten aufruft
            cols[c].button(
                " ",
                key=f"btn_{r}_{c}",
                on_click=handle_click,
                args=(r, c),
                # Stellt sicher, dass die leeren Buttons eine sichtbare Größe haben
                use_container_width=True,
            )
        
        # Belegte Felder zeigen X oder O
        else:
            # Zeigt das X oder O groß und zentriert an
            style = "font-size: 50px; text-align: center; height: 80px; line-height: 80px;"
            cols[c].markdown(f'<div style="{style}">**{field}**</div>', unsafe_allow_html=True)
            
st.markdown("---")
st.caption("Klicke auf ein leeres Feld, um einen Zug zu setzen.")