# Kroniki Zapomnianego Królestwa

Pełnoprawna tekstowa gra RPG w stylu D&D, napisana w Pythonie, z polskim interfejsem.

## 📖 Opis

To kompleksowa gra RPG z:
- **Systemem mechanik inspirowanym D&D 5e** (rzuty k20, atrybuty, klasy postaci)
- **Głęboką fabułą** z questami głównymi i pobocznymi
- **Systemem walki turowej** z krytykami, zaklęciami i taktyką
- **Czterema klasami postaci**: Wojownik, Mag, Łotr, Kleryk
- **Rozbudowanym światem** z wieloma lokacjami do eksploracji
- **Systemem ekwipunku** z bronią, zbrojami, miksturami i magicznymi przedmiotami
- **Zapisami gry** - możliwość zapisania postępu

## 🎮 Jak uruchomić

### Wymagania
- Python 3.7 lub nowszy
- Brak zewnętrznych zależności (tylko standardowa biblioteka Pythona)

### Uruchomienie
```bash
python3 main.py
```

lub (na Windows):
```bash
python main.py
```

## 🗺️ Struktura projektu

```
.
├── main.py                 # Główny plik gry
├── data/                   # Dane gry w JSON
│   ├── classes.json       # Definicje klas postaci
│   ├── items.json         # Przedmioty, broń, zbroje
│   ├── monsters.json      # Potwory i przeciwnicy
│   ├── locations.json     # Lokacje i świat gry
│   └── quests.json        # Questy i fabuła
├── engine/                 # Silnik gry
│   ├── character.py       # System postaci
│   ├── combat.py          # System walki
│   ├── world.py           # Zarządzanie światem
│   └── save_system.py     # Zapisy gry
├── utils/                  # Narzędzia pomocnicze
│   ├── dice.py            # System rzutów kostką
│   └── display.py         # Interfejs terminalowy
└── saves/                  # Katalog zapisów (tworzony automatycznie)
```

## 🎲 Mechaniki gry

### Atrybuty postaci
- **Siła** - wpływa na atak bronią i obrażenia wręcz
- **Zręczność** - wpływa na klasę pancerza i broń zręcznościową
- **Kondycja** - determinuje punkty zdrowia
- **Inteligencja** - wpływa na moc zaklęć dla Maga
- **Mądrość** - wpływa na zaklęcia Kleryka
- **Charyzma** - wpływa na interakcje z NPC

### Klasy postaci

#### 🗡️ Wojownik
- Najwyższa kostka zdrowia (k10)
- Specjalista od walki wręcz
- Startowy ekwipunek: Miecz długi, tarcza, zbroja kolcza
- Umiejętności specjalne: Drugi atak (poziom 3), Ulepszone krytyki (poziom 5)

#### 🔮 Mag
- Potężne zaklęcia bojowe
- Niska wytrzymałość (k6)
- Startowe zaklęcia: Magiczny pocisk, Tarcza, Spalające dłonie
- System slotów zaklęć i many

#### 🗝️ Łotr
- Wszechstronny, szybki
- Ataki z zaskoczenia
- Wysokie umiejętności (otwieranie zamków, skradanie)
- Specjalne: Unik (poziom 3), Podwójne obrażenia (poziom 5)

#### ⚕️ Kleryk
- Mistrz leczenia i wsparcia
- Zaklęcia boskie
- Dobre umiejętności bojowe
- Może walczyć i leczyć

### System walki
- Turowa walka w stylu D&D
- Rzuty k20 na trafienie vs Klasa Pancerza
- Krytyczne trafienia (20) - podwójne obrażenia
- Krytyczne porażki (1) - automatyczne chybienie
- Zaklęcia, mikstury, możliwość ucieczki

## 🌍 Świat gry

### Lokacje
- **Wioska Zielony Gaj** - punkt startowy, handel, odpoczynek
- **Ciemny Las** - niebezpieczne tereny z goblinami i wilkami
- **Opuszczona Kopalnia** - dungeon z trollem jako bossem
- **Ruiny Zamku Czarnego Wawrzynu** - główna lokacja fabularna z Mrocznym Czarnoksiężnikiem
- **Góra Ognistego Szczytu** - legendarna lokacja ze smokiem

### NPC
- Starosta - zleceniodawca głównego questa
- Kowal - handel bronią i zbrojami, naprawa ekwipunku
- Handlarz - sprzedaje mikstury
- Karczmarz - odpoczynek za złoto

## 📜 Questy

### Quest główny: "Cień nad Zielonym Gajem"
Wioska jest nękana przez tajemnicze ataki. Odkryj źródło zła i powstrzymaj Mrocznego Czarnoksiężnika!

### Questy poboczne
- Problem z Goblinami
- Tajemnica Opuszczonej Kopalni
- Polowanie na Wampira
- Smocza Zagadka (legendarny quest)

## 💾 System zapisów

Gra automatycznie zapisuje postęp:
- **Szybki zapis** - szybkie zapisanie (nadpisuje poprzedni)
- **Nowy zapis** - stwórz nowy plik zapisu z własną nazwą
- Zapisy zawierają pełny stan gry: postać, ekwipunek, lokację, questy

## 🛠️ Modyfikacja gry

Wszystkie dane gry są w plikach JSON w katalogu `data/`. Możesz łatwo:
- Dodawać nowe przedmioty (`items.json`)
- Tworzyć nowe potwory (`monsters.json`)
- Projektować nowe lokacje (`locations.json`)
- Dodawać questy (`quests.json`)
- Modyfikować klasy postaci (`classes.json`)

### Przykład: Dodanie nowego przedmiotu

Edytuj `data/items.json`:
```json
"moj_super_miecz": {
  "nazwa": "Mój Super Miecz",
  "typ": "bron",
  "rodzaj_broni": "jednoręczna",
  "obrazenia": "2d8",
  "bonus_ataku": 2,
  "atrybut": "sila",
  "wartosc": 1000,
  "waga": 3,
  "magiczny": true,
  "opis": "Legendarny miecz emanujący mocą!"
}
```

## 🎨 Funkcje

✅ Pełny system D&D (atrybuty, rzuty k20, modyfikatory)
✅ 4 klasy postaci z unikalnymi umiejętnościami
✅ System walki turowej z zaklęciami
✅ Rozbudowany świat z wieloma lokacjami
✅ System questów (głównych i pobocznych)
✅ Handel z NPC
✅ Ekwipunek i przedmioty
✅ System poziomów i doświadczenia
✅ Zapisy gry
✅ Polski interfejs i fabuła
✅ Pełna modyfikowalność (JSON)

## 🐛 Znane problemy

Obecnie brak znanych problemów. Jeśli znajdziesz błąd, możesz go zgłosić.

## 📝 Licencja

Projekt stworzony w celach edukacyjnych. Możesz go swobodnie modyfikować i rozwijać.

## 👤 Autor

Gra stworzona przez Claude (Anthropic)

## 🎮 Porady dla graczy

1. **Wybór klasy** - Wojownik jest najłatwiejszy dla początkujących
2. **Eksploracja** - Zbadaj wszystkie lokacje, aby znaleźć skarby
3. **Handel** - Kupuj mikstury leczenia, przydadzą się w walce
4. **Odpoczynek** - Odpocznij po ciężkich walkach, aby odzyskać HP i manę
5. **Zapisuj** - Regularnie zapisuj grę, zwłaszcza przed trudnymi walkami
6. **Poziomy** - Walcz z potworami, aby zdobywać doświadczenie i awansować
7. **Ekwipunek** - Zbieraj lepszy ekwipunek, znacząco zwiększa siłę postaci

## 🌟 Przyszłe funkcje (do rozważenia)

- Więcej klas postaci
- System craftingu
- Towarzysz w drużynie
- Więcej zaklęć i umiejętności
- Rozbudowana fabuła
- Więcej dungeonów i bossów
- System reputacji
- Frakcje i wybory moralne

---

**Miłej zabawy w Kronikach Zapomnianego Królestwa!** 🎲⚔️
