"""System świata gry i lokacji."""
import json
import random
from utils.display import (print_header, print_separator, press_enter,
                            print_menu, colored_text, print_error, print_success)
from engine.combat import load_monster, CombatSystem
from engine.crafting import CraftingSystem
from engine.trading import TradingSystem


class World:
    """Klasa zarządzająca światem gry."""

    def __init__(self):
        """Inicjalizuje świat gry."""
        self.load_data()
        self.crafting = CraftingSystem()
        self.trading = TradingSystem()

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

        # Aktualizuj postęp questów - odwiedzenie lokacji
        self.update_quest_progress(player, 'visit', location_id)

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
                    else:
                        # Aktualizuj postęp questów
                        self.update_quest_progress(player, 'kill', monster_id)

        # Sprawdź czy są skarby
        if 'skarby' in place:
            self.find_treasure(player, place['skarby'])

        # Sprawdź czy jest boss
        if 'boss' in place:
            print(colored_text("⚔ SPOTKANIE Z BOSSEM! ⚔", 'red'))
            press_enter()
            boss_id = place['boss']
            monster = load_monster(boss_id)
            if monster:
                combat = CombatSystem(player, monster)
                if not combat.start_combat():
                    return False  # Gracz przegrał
                else:
                    # Aktualizuj postęp questów
                    self.update_quest_progress(player, 'kill', boss_id)

        # Sprawdź NPC
        if 'npc' in place:
            for npc_id in place['npc']:
                self.talk_to_npc(player, npc_id)

        # Sprawdź czy jest stacja craftingowa
        if place.get('crafting_station', False):
            print_separator()
            print(colored_text("🔨 Dostępna: Stacja Craftingowa", 'yellow'))
            print("W rogu widzisz stół warsztatowy z narzędziami do tworzenia przedmiotów.")

            use_crafting = input("\nCzy chcesz użyć stacji craftingowej? (t/n): ").strip().lower()
            if use_crafting in ['t', 'tak']:
                self.crafting.show_crafting_menu(player)

        press_enter()
        return True

    def explore_area(self, player, location):
        """Eksploruje okolicę (szukanie skarbów, losowe wydarzenia)."""
        print("\nRozglądasz się po okolicy...")

        found_something = False

        # Sprawdź czy można zbierać materiały
        gatherable = location.get('gatherable_materials', {})
        if gatherable:
            print(colored_text("\n🌿 Możesz tutaj zbierać materiały!", 'green'))

            for material_id, data in gatherable.items():
                chance = data.get('szansa', 0)
                roll = random.randint(1, 100)

                if roll <= chance:
                    # Znaleziono materiał!
                    amount_range = data.get('ilosc', '1')
                    if '-' in amount_range:
                        min_amt, max_amt = map(int, amount_range.split('-'))
                        amount = random.randint(min_amt, max_amt)
                    else:
                        amount = int(amount_range)

                    # Dodaj materiał
                    self.crafting.add_materials_to_player(player, {material_id: amount})

                    # Pobierz nazwę materiału
                    mat_name = self.crafting.get_material_name(material_id)
                    print_success(f"✓ Znalazłeś: {mat_name} x{amount}")
                    found_something = True

        # Dodatkowa szansa na znalezienie złota lub mikstury
        roll = random.randint(1, 100)

        if roll <= 15 and not found_something:
            # Znaleziono skarb
            print_success("✓ Znalazłeś coś!")
            gold = random.randint(10, 50)
            player.gold += gold
            print(f"+ {gold} złota")
            found_something = True
        elif roll <= 25 and not found_something:
            # Znaleziono miksturę
            print_success("✓ Znalazłeś miksturę leczenia!")
            # Dodaj miksturę do ekwipunku
            with open('data/items.json', 'r', encoding='utf-8') as f:
                items_data = json.load(f)
                potion = items_data['mikstury']['mikstura_leczenia'].copy()
                player.add_item(potion)
            found_something = True

        if not found_something:
            print("Nic ciekawego nie znalazłeś tym razem.")

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
                    monster_id = encounter['potwar']
                    monster = load_monster(monster_id)
                    if monster:
                        combat = CombatSystem(player, monster)
                        result = combat.start_combat()
                        if result:
                            # Gracz wygrał - aktualizuj quest
                            self.update_quest_progress(player, 'kill', monster_id)
                        return result
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
            treasures: Lista skarbów (formaty: "zloto:50-150", "przedmiot:20%", "przedmiot")
        """
        print_success("\n💰 Znalazłeś skarb!")

        for treasure in treasures:
            parts = treasure.split(':')
            item_id = parts[0]

            # Specjalna obsługa dla złota
            if item_id == 'zloto':
                if len(parts) > 1:
                    # Format "zloto:50-150" lub "zloto:100"
                    gold_range = parts[1]
                    if '-' in gold_range:
                        min_gold, max_gold = gold_range.split('-')
                        gold = random.randint(int(min_gold), int(max_gold))
                    else:
                        gold = int(gold_range)
                else:
                    gold = 10  # Domyślna wartość
                player.gold += gold
                print(f"  + {gold} złota")
            else:
                # Dla przedmiotów sprawdź szansę
                chance = 100
                if len(parts) > 1:
                    # Format "przedmiot:20%" - usuń % i parsuj
                    chance = int(parts[1].rstrip('%'))

                if random.randint(1, 100) <= chance:
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
            print(f"\n{npc['nazwa']}: \"{npc['dialogi']['powitanie']}\"")

        # Menu dialogowe
        while True:
            print_separator("-")
            options = []

            # Sprawdź questy
            if 'quest' in npc:
                quest_id = npc['quest']
                # Sprawdź czy quest jest już aktywny
                if quest_id in player.active_quests:
                    # Quest aktywny - sprawdź czy ukończony
                    if self.check_quest_completion(player, quest_id):
                        options.append("Oddaj quest")
                    else:
                        options.append("Sprawdź postęp questa")
                elif quest_id not in player.completed_quests:
                    # Quest dostępny
                    options.append("Porozmawiaj o problemie")

            # Handel
            if npc.get('handel', False):
                options.append("Handluj")

            # Plotki/rozmowa
            if 'dialogi' in npc and 'plotki' in npc['dialogi']:
                options.append("Posłuchaj plotek")

            options.append("Zakończ rozmowę")

            # Jeśli tylko opcja to "Zakończ rozmowę", od razu wychodzimy
            if len(options) == 1:
                break

            print("\nCo chcesz zrobić?")
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")

            try:
                choice = int(input("\nWybór: ").strip())
                if 1 <= choice <= len(options):
                    selected = options[choice - 1]

                    if selected == "Porozmawiaj o problemie":
                        self.start_quest(player, npc)
                    elif selected == "Oddaj quest":
                        self.complete_quest(player, npc)
                        break  # Po oddaniu questa wychodzimy z rozmowy
                    elif selected == "Sprawdź postęp questa":
                        self.show_quest_progress(player, npc['quest'])
                    elif selected == "Handluj":
                        self.trade_with_npc(player, npc)
                    elif selected == "Posłuchaj plotek":
                        print(f"\n{npc['nazwa']}: \"{npc['dialogi']['plotki']}\"")
                        press_enter()
                    elif selected == "Zakończ rozmowę":
                        break
                else:
                    print_error("Nieprawidłowy wybór!")
            except ValueError:
                print_error("Wprowadź poprawną liczbę!")

        print("\nŻegnaj!")

    def trade_with_npc(self, player, npc):
        """
        Handel z NPC - używa nowego systemu tradingu.

        Args:
            player: Postać gracza
            npc: Dane NPC
        """
        # Deleguj do trading systemu
        merchant_id = npc.get('id', 'unknown_merchant')
        self.trading.show_trading_menu(player, merchant_id, npc)

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

    def start_quest(self, player, npc):
        """
        Rozpoczyna quest od NPC.

        Args:
            player: Postać gracza
            npc: Dane NPC
        """
        quest_id = npc.get('quest')
        if not quest_id:
            return

        quest_data = self.quests.get(quest_id)
        if not quest_data:
            return

        print_separator("=")
        print(colored_text(f"NOWY QUEST: {quest_data['nazwa']}", 'yellow'))
        print_separator("=")

        # Wyświetl dialog startowy
        if 'dialogi' in npc and 'quest_start' in npc['dialogi']:
            print(f"\n{npc['nazwa']}: \"{npc['dialogi']['quest_start']}\"")

        print(f"\n{quest_data['opis']}")

        # Sprawdź wymagania
        if 'wymagania' in quest_data:
            reqs = quest_data['wymagania']
            if 'min_poziom' in reqs and player.level < reqs['min_poziom']:
                print_error(f"\nPotrzebujesz poziom {reqs['min_poziom']} aby przyjąć ten quest!")
                press_enter()
                return

        # Przyjmij quest
        if input("\n\nCzy chcesz przyjąć ten quest? (t/n): ").lower() in ['t', 'tak']:
            # Dodaj quest z pierwszym etapem
            quest_state = {
                'id': quest_id,
                'etap': 1,
                'postep': {}
            }
            player.active_quests.append(quest_state)
            print_success(f"\n✓ Przyjąłeś quest: {quest_data['nazwa']}")

            # Pokaż pierwszy etap
            etap = quest_data['etapy'][0]
            print(f"\n--- {etap['nazwa']} ---")
            print(etap['opis'])
            press_enter()
        else:
            print("\nMoże później...")
            press_enter()

    def complete_quest(self, player, npc):
        """
        Oddaje ukończony quest.

        Args:
            player: Postać gracza
            npc: Dane NPC
        """
        quest_id = npc.get('quest')
        if not quest_id:
            return

        # Znajdź quest w aktywnych
        quest_state = None
        for q in player.active_quests:
            if q['id'] == quest_id:
                quest_state = q
                break

        if not quest_state:
            return

        quest_data = self.quests.get(quest_id)
        current_etap = quest_data['etapy'][quest_state['etap'] - 1]

        print_separator("=")
        print(colored_text(f"QUEST UKOŃCZONY: {quest_data['nazwa']}", 'green'))
        print_separator("=")

        # Dialog ukończenia
        if 'dialogi' in npc and 'quest_complete' in npc['dialogi']:
            print(f"\n{npc['nazwa']}: \"{npc['dialogi']['quest_complete']}\"")

        # Nagrody
        print("\n--- NAGRODY ---")
        if 'nagroda_xp' in current_etap:
            xp = current_etap['nagroda_xp']
            print(f"+ {xp} XP")
            leveled_up = player.add_xp(xp)
            if leveled_up:
                print_success(f"🌟 AWANS NA POZIOM {player.level}! 🌟")

        if 'nagroda_zloto' in current_etap:
            gold = current_etap['nagroda_zloto']
            player.gold += gold
            print(f"+ {gold} złota")

        if 'nagroda_przedmioty' in current_etap:
            with open('data/items.json', 'r', encoding='utf-8') as f:
                items_data = json.load(f)

            for item_id in current_etap['nagroda_przedmioty']:
                for category in items_data.values():
                    if item_id in category:
                        item = category[item_id].copy()
                        player.add_item(item)
                        print(f"+ {item['nazwa']}")
                        break

        # Sprawdź czy są kolejne etapy
        if 'kolejny_etap' in current_etap:
            next_etap_num = current_etap['kolejny_etap']
            quest_state['etap'] = next_etap_num
            next_etap = quest_data['etapy'][next_etap_num - 1]
            print_separator("-")
            print(colored_text(f"NASTĘPNY ETAP: {next_etap['nazwa']}", 'cyan'))
            print(next_etap['opis'])
        elif current_etap.get('koniec', False):
            # Quest całkowicie ukończony
            player.active_quests.remove(quest_state)
            player.completed_quests.append(quest_id)
            print_separator("-")
            print_success("Quest całkowicie ukończony!")

        press_enter()

    def check_quest_completion(self, player, quest_id):
        """
        Sprawdza czy quest jest ukończony.

        Args:
            player: Postać gracza
            quest_id: ID questa

        Returns:
            True jeśli quest jest ukończony
        """
        # Znajdź quest w aktywnych
        quest_state = None
        for q in player.active_quests:
            if q['id'] == quest_id:
                quest_state = q
                break

        if not quest_state:
            return False

        quest_data = self.quests.get(quest_id)
        current_etap = quest_data['etapy'][quest_state['etap'] - 1]

        # Sprawdź cel
        cel = current_etap['cel']

        # Różne typy celów
        if cel.startswith('pokonaj:'):
            # Format: "pokonaj:goblin" lub "pokonaj:goblin:5"
            parts = cel.split(':')
            monster_id = parts[1]
            required_count = int(parts[2]) if len(parts) > 2 else 1

            killed = quest_state['postep'].get(f'killed_{monster_id}', 0)
            return killed >= required_count

        elif cel.startswith('odwiedz_lokacje:'):
            # Format: "odwiedz_lokacje:ciemny_las"
            location_id = cel.split(':')[1]
            return quest_state['postep'].get(f'visited_{location_id}', False)

        elif cel.startswith('porozmawiaj:'):
            # Format: "porozmawiaj:starosta"
            npc_id = cel.split(':')[1]
            # Ten cel będzie spełniony gdy gracz rozmawia z NPC
            return True

        elif cel.startswith('zbierz:'):
            # Format: "zbierz:item_id:5"
            parts = cel.split(':')
            item_id = parts[1]
            required_count = int(parts[2]) if len(parts) > 2 else 1

            # Sprawdź w ekwipunku
            count = sum(1 for item in player.inventory if item.get('id') == item_id)
            return count >= required_count

        return False

    def show_quest_progress(self, player, quest_id):
        """
        Pokazuje postęp questa.

        Args:
            player: Postać gracza
            quest_id: ID questa
        """
        # Znajdź quest
        quest_state = None
        for q in player.active_quests:
            if q['id'] == quest_id:
                quest_state = q
                break

        if not quest_state:
            print_error("Nie masz tego questa!")
            press_enter()
            return

        quest_data = self.quests.get(quest_id)
        current_etap = quest_data['etapy'][quest_state['etap'] - 1]

        print_separator("=")
        print(colored_text(f"QUEST: {quest_data['nazwa']}", 'cyan'))
        print_separator("=")
        print(f"\nAktualny etap: {current_etap['nazwa']}")
        print(current_etap['opis'])

        # Pokaż postęp
        cel = current_etap['cel']
        if cel.startswith('pokonaj:'):
            parts = cel.split(':')
            monster_id = parts[1]
            required_count = int(parts[2]) if len(parts) > 2 else 1
            killed = quest_state['postep'].get(f'killed_{monster_id}', 0)
            print(f"\nPostęp: {killed}/{required_count}")

        if self.check_quest_completion(player, quest_id):
            print_success("\n✓ Etap ukończony! Wróć do zleceniodawcy!")
        else:
            print("\n⚠ Quest w trakcie...")

        press_enter()

    def update_quest_progress(self, player, event_type, event_data):
        """
        Aktualizuje postęp questów.

        Args:
            player: Postać gracza
            event_type: Typ wydarzenia ('kill', 'visit', 'talk')
            event_data: Dane wydarzenia (ID potwora, lokacji, NPC)
        """
        for quest_state in player.active_quests:
            quest_data = self.quests.get(quest_state['id'])
            if not quest_data:
                continue

            current_etap = quest_data['etapy'][quest_state['etap'] - 1]
            cel = current_etap['cel']

            # Aktualizuj w zależności od typu
            if event_type == 'kill' and cel.startswith('pokonaj:'):
                monster_id = cel.split(':')[1]
                if monster_id == event_data:
                    key = f'killed_{monster_id}'
                    quest_state['postep'][key] = quest_state['postep'].get(key, 0) + 1
                    print_success(f"✓ Postęp questa zaktualizowany!")

            elif event_type == 'visit' and cel.startswith('odwiedz_lokacje:'):
                location_id = cel.split(':')[1]
                if location_id == event_data or event_data in location_id:
                    quest_state['postep'][f'visited_{location_id}'] = True
                    print_success(f"✓ Postęp questa zaktualizowany!")

    def show_all_quests(self, player):
        """
        Wyświetla wszystkie questy gracza.

        Args:
            player: Postać gracza
        """
        print_header("DZIENNIK QUESTÓW")

        # Aktywne questy
        if player.active_quests:
            print(colored_text("\n=== AKTYWNE QUESTY ===", 'yellow'))
            for quest_state in player.active_quests:
                quest_data = self.quests.get(quest_state['id'])
                if quest_data:
                    current_etap = quest_data['etapy'][quest_state['etap'] - 1]
                    print(f"\n📜 {quest_data['nazwa']}")
                    print(f"   Etap {quest_state['etap']}: {current_etap['nazwa']}")

                    # Sprawdź czy ukończony
                    if self.check_quest_completion(player, quest_state['id']):
                        print(colored_text("   ✓ Gotowy do oddania!", 'green'))
                    else:
                        # Pokaż postęp
                        cel = current_etap['cel']
                        if cel.startswith('pokonaj:'):
                            parts = cel.split(':')
                            monster_id = parts[1]
                            required = int(parts[2]) if len(parts) > 2 else 1
                            killed = quest_state['postep'].get(f'killed_{monster_id}', 0)
                            print(f"   Postęp: {killed}/{required}")
                        else:
                            print(f"   W trakcie...")
        else:
            print("\nNie masz aktywnych questów.")

        # Ukończone questy
        if player.completed_quests:
            print(colored_text("\n\n=== UKOŃCZONE QUESTY ===", 'green'))
            for quest_id in player.completed_quests:
                quest_data = self.quests.get(quest_id)
                if quest_data:
                    print(f"✓ {quest_data['nazwa']}")

        press_enter()

    def show_talent_tree(self, player):
        """
        Wyświetla drzewo talentów i pozwala wybrać talent.

        Args:
            player: Postać gracza
        """
        import json

        # Wczytaj talenty
        with open('data/talents.json', 'r', encoding='utf-8') as f:
            talents_data = json.load(f)

        class_talents = talents_data[player.character_class]

        while True:
            print_header(f"TALENTY - {player.character_class.upper()}")
            print(f"Dostępne punkty: {colored_text(str(player.talent_points), 'yellow')}")
            print_separator()

            # Wyświetl 3 ścieżki
            trees = list(class_talents.keys())

            print("\nWybierz ścieżkę talentów:")
            for i, tree_id in enumerate(trees, 1):
                tree = class_talents[tree_id]
                learned_in_tree = sum(1 for t_id in tree['talenty'].keys() if player.has_talent(t_id))
                print(f"  {i}. {tree['nazwa']} ({learned_in_tree}/5 talentów)")
                print(f"     {tree['opis']}")

            print(f"  0. Wróć")

            try:
                choice = int(input("\nWybór: ").strip())
                if choice == 0:
                    break
                if 1 <= choice <= len(trees):
                    tree_id = trees[choice - 1]
                    self.show_talent_tree_detail(player, class_talents[tree_id], tree_id)
                else:
                    print_error("Nieprawidłowy wybór!")
                    press_enter()
            except ValueError:
                print_error("Wprowadź poprawną liczbę!")
                press_enter()
            except KeyboardInterrupt:
                break

    def show_talent_tree_detail(self, player, tree_data, tree_id):
        """
        Pokazuje szczegóły konkretnej ścieżki talentów.

        Args:
            player: Postać gracza
            tree_data: Dane ścieżki
            tree_id: ID ścieżki
        """
        while True:
            print_header(f"{tree_data['nazwa']}")
            print(tree_data['opis'])
            print_separator()
            print(f"Punkty talentów: {colored_text(str(player.talent_points), 'yellow')}")
            print_separator()

            # Wyświetl talenty (1-5)
            talents_list = []
            for i in range(1, 6):
                talent_id = f"{tree_id}_{i}"
                if talent_id in tree_data['talenty']:
                    talent = tree_data['talenty'][talent_id]
                    talents_list.append((talent_id, talent))

            for i, (talent_id, talent) in enumerate(talents_list, 1):
                # Status talentu
                if player.has_talent(talent_id):
                    status = colored_text("✓ WYUCZONY", 'green')
                else:
                    can_learn, reason = player.can_learn_talent(talent_id)
                    if can_learn:
                        status = colored_text("◯ DOSTĘPNY", 'yellow')
                    else:
                        status = colored_text("✗ ZABLOKOWANY", 'red')

                # Typ talentu
                typ_str = "PASYWNY" if talent['typ'] == 'pasywny' else colored_text("AKTYWNY", 'cyan')

                print(f"\n{i}. [{typ_str}] {talent['nazwa']} {status}")
                print(f"   {talent['opis']}")
                print(f"   Wymagany poziom: {talent['wymagany_poziom_postaci']}")

                # Wymagania
                if 'wymaga' in talent:
                    req_id = talent['wymaga']
                    req_talent = tree_data['talenty'][req_id]
                    req_status = "✓" if player.has_talent(req_id) else "✗"
                    print(f"   Wymaga: {req_status} {req_talent['nazwa']}")

                # Cooldown i koszt (dla aktywnych)
                if talent['typ'] == 'aktywny':
                    efekt = talent['efekt']
                    if 'cooldown' in efekt:
                        print(f"   Cooldown: {efekt['cooldown']} tur")
                    if 'mana_cost' in efekt:
                        print(f"   Koszt: {efekt['mana_cost']} many")

            print(f"\n  0. Wróć")

            try:
                choice = int(input("\nWybierz talent aby go nauczyć (lub 0): ").strip())
                if choice == 0:
                    break
                if 1 <= choice <= len(talents_list):
                    talent_id, talent = talents_list[choice - 1]

                    # Próba nauki
                    if player.has_talent(talent_id):
                        print_warning("Już znasz ten talent!")
                        press_enter()
                    else:
                        can_learn, reason = player.can_learn_talent(talent_id)
                        if can_learn:
                            # Potwierdź
                            print_separator()
                            print(f"Czy chcesz nauczyć się: {colored_text(talent['nazwa'], 'yellow')}?")
                            print(f"{talent['opis']}")
                            if input("\nPotwierdź (t/n): ").lower() in ['t', 'tak']:
                                success, message = player.learn_talent(talent_id)
                                if success:
                                    print_success(f"\n{message}")
                                    press_enter()
                                else:
                                    print_error(f"\n{message}")
                                    press_enter()
                        else:
                            print_error(f"Nie możesz się tego nauczyć: {reason}")
                            press_enter()
                else:
                    print_error("Nieprawidłowy wybór!")
                    press_enter()
            except ValueError:
                print_error("Wprowadź poprawną liczbę!")
                press_enter()
            except KeyboardInterrupt:
                break
