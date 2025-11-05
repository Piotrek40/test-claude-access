"""System świata gry i lokacji."""
import json
import random
from utils.display import (print_header, print_separator, press_enter,
                            print_menu, colored_text, print_error, print_success)
from engine.combat import load_monster, CombatSystem


class World:
    """Klasa zarządzająca światem gry."""

    def __init__(self):
        """Inicjalizuje świat gry."""
        self.load_data()

    def load_data(self):
        """Wczytuje dane świata z plików JSON."""
        with open('data/locations.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.locations = data['lokacje']
            self.npcs = data['npc']

        with open('data/quests.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.quests = data['questy']
            self.random_events = data.get('wydarzenia_losowe', {})

    def get_location(self, location_id):
        """
        Zwraca dane lokacji.

        Args:
            location_id: ID lokacji

        Returns:
            Dict z danymi lokacji lub None
        """
        return self.locations.get(location_id)

    def get_npc(self, npc_id):
        """
        Zwraca dane NPC.

        Args:
            npc_id: ID NPC

        Returns:
            Dict z danymi NPC lub None
        """
        return self.npcs.get(npc_id)

    def explore_location(self, player, location_id):
        """
        Eksploruje lokację.

        Args:
            player: Postać gracza
            location_id: ID lokacji do eksploracji

        Returns:
            True jeśli kontynuować grę, False jeśli kończyć
        """
        location = self.get_location(location_id)
        if not location:
            print_error(f"Nieznana lokacja: {location_id}")
            return True

        # Wyświetl opis lokacji
        print_header(location['nazwa'])
        print(location['opis'])
        print_separator()

        # Sprawdź losowe spotkania
        if location.get('niebezpieczenstwo') and random.randint(1, 100) <= 30:
            if self.random_encounter(player, location):
                return True  # Walka się odbyła
            else:
                return False  # Gracz zginął

        # Menu akcji w lokacji
        while True:
            actions = ["Eksploruj okolicę", "Zobacz ekwipunek", "Odpoczynek", "Idź gdzie indziej"]

            # Sprawdź czy są miejsca do odwiedzenia
            if 'miejsca' in location and location['miejsca']:
                actions.insert(0, "Odwiedź miejsce")

            choice = print_menu("CO CHCESZ ZROBIĆ?", actions)
            action = actions[choice]

            if action == "Odwiedź miejsce":
                result = self.visit_place(player, location)
                if not result:
                    return False  # Gracz zginął
            elif action == "Eksploruj okolicę":
                self.explore_area(player, location)
            elif action == "Zobacz ekwipunek":
                self.show_inventory(player)
            elif action == "Odpoczynek":
                self.rest(player)
            elif action == "Idź gdzie indziej":
                # Wybierz nowe miejsce
                new_location = self.choose_destination(player, location)
                if new_location:
                    player.current_location = new_location
                    return True
                # Jeśli None, pozostajemy w tej lokacji (kontynuuj pętlę)

    def visit_place(self, player, location):
        """
        Odwiedza konkretne miejsce w lokacji.

        Args:
            player: Postać gracza
            location: Dane lokacji

        Returns:
            True jeśli kontynuować, False jeśli gracz zginął
        """
        places = location['miejsca']
        place_names = list(places.keys())

        # Menu wyboru miejsca
        options = [places[p]['nazwa'] for p in place_names]
        options.append("Wróć")

        choice = print_menu("GDZIE CHCESZ PÓJŚĆ?", options)

        if choice == len(options) - 1:  # Wróć
            return True

        place_id = place_names[choice]
        place = places[place_id]

        # Wyświetl opis miejsca
        print_header(place['nazwa'])
        print(place['opis'])
        print_separator()

        # Sprawdź czy są potwory
        if 'potwory' in place:
            print(colored_text("⚠ Widzisz wrogów!", 'red'))
            for monster_id in place['potwory']:
                monster = load_monster(monster_id)
                if monster:
                    combat = CombatSystem(player, monster)
                    if not combat.start_combat():
                        return False  # Gracz przegrał

        # Sprawdź czy są skarby
        if 'skarby' in place:
            self.find_treasure(player, place['skarby'])

        # Sprawdź czy jest boss
        if 'boss' in place:
            print(colored_text("⚔ SPOTKANIE Z BOSSEM! ⚔", 'red'))
            press_enter()
            monster = load_monster(place['boss'])
            if monster:
                combat = CombatSystem(player, monster)
                if not combat.start_combat():
                    return False  # Gracz przegrał

        # Sprawdź NPC
        if 'npc' in place:
            for npc_id in place['npc']:
                self.talk_to_npc(player, npc_id)

        press_enter()
        return True

    def explore_area(self, player, location):
        """Eksploruje okolicę (szukanie skarbów, losowe wydarzenia)."""
        print("\nRozglądasz się po okolicy...")

        # Szansa na znalezienie czegoś
        roll = random.randint(1, 100)

        if roll <= 20:
            # Znaleziono skarb
            print_success("✓ Znalazłeś coś!")
            gold = random.randint(10, 50)
            player.gold += gold
            print(f"+ {gold} złota")
        elif roll <= 30:
            # Znaleziono miksturę
            print_success("✓ Znalazłeś miksturę leczenia!")
            # Dodaj miksturę do ekwipunku
            with open('data/items.json', 'r', encoding='utf-8') as f:
                items_data = json.load(f)
                potion = items_data['mikstury']['mikstura_leczenia'].copy()
                player.add_item(potion)
        else:
            print("Nic ciekawego nie znalazłeś.")

        press_enter()

    def random_encounter(self, player, location):
        """
        Losowe spotkanie w niebezpiecznej lokacji.

        Args:
            player: Postać gracza
            location: Dane lokacji

        Returns:
            True jeśli kontynuować, False jeśli gracz zginął
        """
        encounters = location.get('losowe_spotkania', [])
        if not encounters:
            return True

        # Wybierz losowe spotkanie
        total_chance = sum(e.get('szansa', 0) for e in encounters)
        roll = random.randint(1, total_chance)

        cumulative = 0
        for encounter in encounters:
            cumulative += encounter.get('szansa', 0)
            if roll <= cumulative:
                # To spotkanie!
                if 'potwar' in encounter:
                    print(colored_text("\n⚠ SPOTKANIE Z POTWOREM! ⚠", 'red'))
                    monster = load_monster(encounter['potwar'])
                    if monster:
                        combat = CombatSystem(player, monster)
                        return combat.start_combat()
                elif 'wydarzenie' in encounter:
                    # Inne wydarzenie (np. znaleziony skarb)
                    return True
                break

        return True

    def find_treasure(self, player, treasures):
        """
        Znajduje skarb.

        Args:
            player: Postać gracza
            treasures: Lista skarbów (format: "przedmiot:szansa%")
        """
        print_success("\n💰 Znalazłeś skarb!")

        for treasure in treasures:
            parts = treasure.split(':')
            item_id = parts[0]

            # Sprawdź szansę
            chance = 100
            if len(parts) > 1:
                chance = int(parts[1].rstrip('%'))

            if random.randint(1, 100) <= chance:
                if item_id == 'zloto':
                    gold = random.randint(50, 150)
                    player.gold += gold
                    print(f"  + {gold} złota")
                else:
                    # Znajdź przedmiot
                    with open('data/items.json', 'r', encoding='utf-8') as f:
                        items_data = json.load(f)

                    for category in items_data.values():
                        if item_id in category:
                            item = category[item_id].copy()
                            player.add_item(item)
                            print(f"  + {item['nazwa']}")
                            break

    def talk_to_npc(self, player, npc_id):
        """
        Rozmawia z NPC.

        Args:
            player: Postać gracza
            npc_id: ID NPC
        """
        npc = self.get_npc(npc_id)
        if not npc:
            return

        print_header(f"Rozmowa z: {npc['nazwa']}")
        print(npc['opis'])
        print_separator()

        # Powitanie
        if 'dialogi' in npc and 'powitanie' in npc['dialogi']:
            print(f"{npc['nazwa']}: \"{npc['dialogi']['powitanie']}\"")

        # Handel
        if npc.get('handel', False):
            if input("\nChcesz handlować? (t/n): ").lower() in ['t', 'tak']:
                self.trade_with_npc(player, npc)

        press_enter()

    def trade_with_npc(self, player, npc):
        """
        Handel z NPC.

        Args:
            player: Postać gracza
            npc: Dane NPC
        """
        print_header("HANDEL")
        print(f"Twoje złoto: {player.gold}")
        print_separator()

        asortyment = npc.get('asortyment', [])
        if not asortyment:
            print("Ten handlarz nie ma nic do sprzedania.")
            return

        # Wczytaj przedmioty
        with open('data/items.json', 'r', encoding='utf-8') as f:
            items_data = json.load(f)

        while True:
            print("\nDostępne przedmioty:")
            items = []
            for item_id in asortyment:
                for category in items_data.values():
                    if item_id in category:
                        item = category[item_id]
                        items.append(item)
                        print(f"  {len(items)}. {item['nazwa']} - {item['wartosc']} złota")
                        break

            print(f"  0. Zakończ handel")

            try:
                choice = int(input("\nCo chcesz kupić? "))
                if choice == 0:
                    break
                if 1 <= choice <= len(items):
                    item = items[choice - 1]
                    if player.gold >= item['wartosc']:
                        player.gold -= item['wartosc']
                        player.add_item(item.copy())
                        print_success(f"Kupiono {item['nazwa']}!")
                    else:
                        print_error("Nie masz wystarczająco złota!")
                else:
                    print_error("Nieprawidłowy wybór!")
            except ValueError:
                print_error("Wprowadź poprawną liczbę!")

    def show_inventory(self, player):
        """Pokazuje ekwipunek gracza."""
        from utils.display import print_stats_panel

        print_stats_panel(player)

        if not player.inventory:
            print("Ekwipunek jest pusty.")
            press_enter()
            return

        print("\n--- EKWIPUNEK ---")
        for i, item in enumerate(player.inventory, 1):
            equipped_marker = ""
            if item == player.equipped.get('bron') or \
               item == player.equipped.get('zbroja') or \
               item == player.equipped.get('tarcza'):
                equipped_marker = " [ZAŁOŻONE]"
            print(f"  {i}. {item['nazwa']}{equipped_marker}")
            if 'opis' in item:
                print(f"     {item['opis']}")

        # Menu akcji z ekwipunkiem
        print("\n1. Załóż przedmiot")
        print("2. Użyj przedmiot")
        print("3. Wróć")

        try:
            choice = int(input("\nWybór: "))
            if choice == 1:
                item_num = int(input("Który przedmiot? "))
                if 1 <= item_num <= len(player.inventory):
                    item = player.inventory[item_num - 1]
                    if player.equip_item(item):
                        print_success(f"Założono {item['nazwa']}!")
                    else:
                        print_error("Nie można założyć tego przedmiotu!")
            elif choice == 2:
                item_num = int(input("Który przedmiot? "))
                if 1 <= item_num <= len(player.inventory):
                    item = player.inventory[item_num - 1]
                    success, message = player.use_item(item)
                    if success:
                        print_success(message)
                    else:
                        print_error(message)
        except ValueError:
            pass

        press_enter()

    def rest(self, player):
        """Odpoczynek - przywraca HP i manę."""
        print("\nOdpoczywasz...")
        player.rest()
        print_success("✓ Odzyskałeś pełne zdrowie!")
        if hasattr(player, 'mana') and player.max_mana > 0:
            print_success("✓ Odzyskałeś pełną manę!")
        press_enter()

    def choose_destination(self, player, current_location):
        """
        Wybiera nowe miejsce do odwiedzenia.

        Args:
            player: Postać gracza
            current_location: Aktualna lokacja

        Returns:
            ID nowej lokacji lub None jeśli anulowano
        """
        exits = current_location.get('wyjscia', {})
        if not exits:
            print_error("Nie ma dokąd iść stąd!")
            press_enter()
            return None

        # Menu wyboru kierunku
        directions = {
            'polnoc': '🡅 Północ',
            'poludnie': '🡇 Południe',
            'wschod': '🡆 Wschód',
            'zachod': '🡄 Zachód'
        }

        options = []
        destinations = []
        for direction, dest_id in exits.items():
            dest = self.get_location(dest_id)
            if dest:
                dir_text = directions.get(direction, direction.capitalize())
                options.append(f"{dir_text} - {dest['nazwa']}")
                destinations.append(dest_id)

        options.append("Zostań tutaj")

        choice = print_menu("DOKĄD CHCESZ PÓJŚĆ?", options)

        if choice == len(options) - 1:  # Zostań tutaj
            return None

        return destinations[choice]
