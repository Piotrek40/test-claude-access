#!/usr/bin/env python3
"""
Kroniki Zapomnianego Królestwa
Tekstowa Gra RPG w stylu D&D

Autor: Claude
Wersja: 1.0
"""

import json
import sys
from utils.display import (clear_screen, print_header, print_separator, press_enter,
                            print_menu, print_slow, colored_text, print_success, print_error)
from utils.dice import roll_stats, calculate_modifier
from engine.character import Character
from engine.save_system import SaveSystem
from engine.world import World


class Game:
    """Główna klasa gry."""

    def __init__(self):
        """Inicjalizuje grę."""
        self.player = None
        self.world = World()
        self.running = True

    def start(self):
        """Rozpoczyna grę."""
        clear_screen()
        self.show_intro()

        # Menu główne
        while self.running:
            clear_screen()
            self.main_menu()

    def show_intro(self):
        """Pokazuje intro gry."""
        with open('data/quests.json', 'r', encoding='utf-8') as f:
            quests_data = json.load(f)
            intro = quests_data.get('intro', {})

        for line in intro.get('tekst', []):
            print(line)

        press_enter()

    def main_menu(self):
        """Menu główne."""
        print_header("KRONIKI ZAPOMNIANEGO KRÓLESTWA")
        print(colored_text("Tekstowa Gra RPG", 'cyan'))
        print_separator()

        options = ["Nowa Gra", "Wczytaj Grę", "Wyjście"]
        choice = print_menu("MENU GŁÓWNE", options)

        if choice == 0:  # Nowa gra
            self.new_game()
        elif choice == 1:  # Wczytaj grę
            self.load_game()
        elif choice == 2:  # Wyjście
            self.quit_game()

    def new_game(self):
        """Rozpoczyna nową grę."""
        clear_screen()
        print_header("TWORZENIE POSTACI")

        # Wybór imienia
        print("\nJak masz na imię?")
        name = input("Imię: ").strip()
        if not name:
            name = "Bohater"

        # Wybór klasy
        with open('data/classes.json', 'r', encoding='utf-8') as f:
            classes_data = json.load(f)

        class_options = []
        class_ids = []
        for class_id, class_info in classes_data['classes'].items():
            class_options.append(f"{class_info['nazwa']} - {class_info['opis']}")
            class_ids.append(class_id)

        print_separator()
        choice = print_menu("WYBIERZ KLASĘ POSTACI", class_options)
        character_class = class_ids[choice]

        # Generowanie atrybutów
        print_separator()
        print("\nGenerowanie atrybutów...")

        # Wybór metody generowania
        print("\n1. Losowanie (4d6, odrzuć najniższy)")
        print("2. Standardowe wartości (15, 14, 13, 12, 10, 8)")

        method_choice = input("Wybierz metodę (1/2): ").strip()

        if method_choice == '1':
            stats = roll_stats()
            print("\nWylosowane wartości:", stats)
        else:
            stats = [15, 14, 13, 12, 10, 8]
            print("\nStandardowe wartości:", stats)

        # Przypisz atrybuty
        attributes = self.assign_attributes(stats)

        # Stwórz postać
        self.player = Character(name, character_class, attributes)

        clear_screen()
        print_success(f"✓ Postać {name} ({classes_data['classes'][character_class]['nazwa']}) została stworzona!")
        print_separator()

        # Pokaż statystyki
        from utils.display import print_stats_panel
        print_stats_panel(self.player)

        press_enter("Naciśnij ENTER aby rozpocząć przygodę...")

        # Rozpocznij grę
        self.game_loop()

    def assign_attributes(self, stats):
        """
        Przypisuje wartości do atrybutów.

        Args:
            stats: Lista wartości do przypisania

        Returns:
            Dict z atrybutami
        """
        attributes_names = {
            'sila': 'Siła',
            'zrecznosc': 'Zręczność',
            'kondycja': 'Kondycja',
            'inteligencja': 'Inteligencja',
            'madrosc': 'Mądrość',
            'charyzma': 'Charyzma'
        }

        print("\nPrzypisz wartości do atrybutów:")
        print("Dostępne wartości:", stats)
        print_separator()

        attributes = {}
        remaining_stats = stats.copy()

        for attr_id, attr_name in attributes_names.items():
            while True:
                print(f"\nDostępne wartości: {remaining_stats}")
                try:
                    value = int(input(f"{attr_name}: "))
                    if value in remaining_stats:
                        attributes[attr_id] = value
                        remaining_stats.remove(value)
                        break
                    else:
                        print_error("Ta wartość nie jest dostępna!")
                except ValueError:
                    print_error("Wprowadź poprawną liczbę!")

        return attributes

    def load_game(self):
        """Wczytuje zapisaną grę."""
        clear_screen()
        print_header("WCZYTAJ GRĘ")

        saves = SaveSystem.list_saves()

        if not saves:
            print_error("Brak zapisanych gier!")
            press_enter()
            return

        # Lista zapisów
        options = []
        for save in saves:
            options.append(f"{save['character_name']} - Poziom {save['level']} {save['class']}")

        options.append("Wróć")

        choice = print_menu("WYBIERZ ZAPIS", options)

        if choice == len(options) - 1:  # Wróć
            return

        # Wczytaj wybrany zapis
        save = saves[choice]
        self.player = SaveSystem.load_game(save['filename'])

        if self.player:
            print_success(f"✓ Wczytano grę: {self.player.name}")
            press_enter()
            self.game_loop()
        else:
            print_error("✗ Błąd wczytywania gry!")
            press_enter()

    def game_loop(self):
        """Główna pętla gry."""
        while self.running and self.player and self.player.is_alive():
            clear_screen()

            # Menu gry
            from utils.display import print_stats_panel
            print_stats_panel(self.player)

            current_location = self.world.get_location(self.player.current_location)
            print(f"\nAktualna lokacja: {current_location['nazwa']}")

            options = [
                "Eksploruj lokację",
                "Zobacz ekwipunek",
                "Odpoczynek",
                "Zapisz grę",
                "Menu główne"
            ]

            choice = print_menu("CO CHCESZ ZROBIĆ?", options)

            if choice == 0:  # Eksploruj lokację
                result = self.world.explore_location(self.player, self.player.current_location)
                if not result:
                    # Gracz zginął
                    self.player_death()
                    return
            elif choice == 1:  # Zobacz ekwipunek
                self.world.show_inventory(self.player)
            elif choice == 2:  # Odpoczynek
                self.world.rest(self.player)
            elif choice == 3:  # Zapisz grę
                self.save_game()
            elif choice == 4:  # Menu główne
                if self.confirm_quit():
                    return

        # Jeśli gracz nie żyje
        if not self.player.is_alive():
            self.player_death()

    def save_game(self):
        """Zapisuje grę."""
        clear_screen()
        print_header("ZAPISZ GRĘ")

        print("\n1. Szybki zapis (nadpisuje poprzedni)")
        print("2. Nowy zapis")
        print("3. Anuluj")

        choice = input("\nWybór: ").strip()

        if choice == '1':
            SaveSystem.quick_save(self.player)
            print_success("✓ Gra zapisana (szybki zapis)!")
        elif choice == '2':
            save_name = input("Nazwa zapisu: ").strip()
            if save_name:
                SaveSystem.save_game(self.player, save_name)
                print_success(f"✓ Gra zapisana jako '{save_name}'!")
            else:
                print_error("Anulowano zapis.")
        else:
            print("Anulowano.")

        press_enter()

    def player_death(self):
        """Obsługuje śmierć gracza."""
        clear_screen()
        print_separator("=")
        print(colored_text("💀 KONIEC GRY 💀", 'red'))
        print_separator("=")
        print("\nTwoja postać zginęła...")
        print(f"{self.player.name} osiągnął poziom {self.player.level}")
        print(f"Zdobyte doświadczenie: {self.player.xp}")
        print_separator("=")
        press_enter()

    def confirm_quit(self):
        """Potwierdza wyjście z gry."""
        print("\nCzy na pewno chcesz wyjść?")
        print("Niezapisane postępy zostaną utracone!")
        response = input("Wyjść? (t/n): ").strip().lower()
        return response in ['t', 'tak', 'y', 'yes']

    def quit_game(self):
        """Wychodzi z gry."""
        print("\nDziękujemy za grę!")
        print("Do zobaczenia!")
        self.running = False
        sys.exit(0)


def main():
    """Główna funkcja uruchamiająca grę."""
    try:
        game = Game()
        game.start()
    except KeyboardInterrupt:
        print("\n\nGra przerwana.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nBłąd krytyczny: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
