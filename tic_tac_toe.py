0# 1. Spielbrett erstellen
def erstelle_brett():
    brett = []
    for i in range(3):
        zeile = [' ', ' ', ' ']
        brett.append(zeile)
    return brett

# 2. Spielbrett ausgeben
def drucke_brett(brett):
    for zeile in brett:
        print('|'.join(zeile))
        print('------')

#6. Unsere Main :)
def spiele_tic_tac_toe():
    brett = erstelle_brett()
    aktueller_spieler = 'X'

    while True:
        drucke_brett(brett)

        try:
            zeile = int(input(f'Spieler {aktueller_spieler}, wähle deine Zeile (0-2).'))
            spalte = int(input(f'Spieler {aktueller_spieler}, wähle deine Spalte (0-2).'))
            if zeile < 0 or zeile > 2 or spalte < 0 or spalte > 2:
                print('Du darfst nur Züge zwischen 0 und 2 setzen!')
                continue

            else:
                if not mache_zug(brett,aktueller_spieler,zeile,spalte):
                    print('Ungültig, versuche es erneut')
                    continue
        except ValueError:
            print('Gib doch bitte eine Ganzzahl ein!')
            continue

        if pruefe_gewonnen(brett,aktueller_spieler):
            drucke_brett(brett)
            print(f'Hey, du hast gewonnen Spieler {aktueller_spieler}')
            break
        elif pruefe_unentschieden(brett):
            drucke_brett(brett)
            print('Unentschieden! Kein Spieler hat gewonnen.')
            break

        aktueller_spieler = 'O' if aktueller_spieler == 'X' else 'X'

# 3. Zug machen
def mache_zug(brett,aktueller_spieler,zeile,spalte):
    if brett[zeile][spalte] == ' ':
        brett[zeile][spalte] = aktueller_spieler
        return True
    else:
        return False

#4. Gewinn überprüfen
def pruefe_gewonnen(brett,aktueller_spieler):
    for zeile in range(3):
        if brett[zeile][0] == brett[zeile][1] == brett[zeile][2] == aktueller_spieler:
            return True
    for spalte in range(3):
        if brett[0][spalte] == brett[1][spalte] == brett[2][spalte] == aktueller_spieler:
            return True
    if brett[0][0] == brett[1][1] == brett[2][2] == aktueller_spieler or\
        brett[0][2] == brett[1][1] == brett[2][0] == aktueller_spieler:
            return True

#5. Prüfe ob unentschieden
def pruefe_unentschieden(brett):
    for zeile in brett:
        if ' ' in zeile:
            return False
    return True
spiele_tic_tac_toe()