"""System walki."""
import json
from utils.dice import d20, roll, calculate_modifier
from utils.display import (print_combat_status, print_separator, press_enter,
                            print_success, print_error, print_warning, colored_text)


class Monster:
    """Klasa reprezentująca potwora/przeciwnika."""

    def __init__(self, monster_id, monster_data):
        """
        Inicjalizuje potwora.

        Args:
            monster_id: ID potwora
            monster_data: Dane potwora ze słownika
        """
        self.id = monster_id
        self.name = monster_data['nazwa']
        self.level = monster_data['poziom']
        self.typ = monster_data['typ']
        self.max_hp = monster_data['zdrowie']
        self.hp = self.max_hp
        self.armor_class = monster_data['klasa_pancerza']
        self.attributes = monster_data['atrybuty']
        self.attack_data = monster_data['atak']
        self.xp_reward = monster_data['doswiadczenie']
        self.loot = monster_data.get('lup', [])
        self.special = monster_data.get('specjalne', {})
        self.resistances = monster_data.get('odpornosci', [])
        self.weaknesses = monster_data.get('slabosci', [])
        self.spells = monster_data.get('zaklecia', [])
        self.is_boss = monster_data.get('boss', False)

    def get_modifier(self, attribute):
        """Zwraca modyfikator dla atrybutu."""
        return calculate_modifier(self.attributes[attribute])

    def take_damage(self, damage, damage_type='physical'):
        """
        Otrzymuje obrażenia.

        Args:
            damage: Ilość obrażeń
            damage_type: Typ obrażeń

        Returns:
            Rzeczywiste obrażenia (po oporach/słabościach)
        """
        # Sprawdź odporności i słabości
        if damage_type in self.resistances:
            damage = damage // 2
            print_warning(f"{self.name} jest odporny na ten typ ataku!")

        if damage_type in self.weaknesses:
            damage = int(damage * 1.5)
            print_success(f"{self.name} jest słaby na ten typ ataku!")

        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        return damage

    def is_alive(self):
        """Sprawdza czy potwór żyje."""
        return self.hp > 0

    def attack(self):
        """
        Wykonuje atak.

        Returns:
            Tuple (roll, bonus, damage_roll)
        """
        attack_roll = d20()
        attack_bonus = self.attack_data.get('bonus', 0)
        damage_roll = self.attack_data.get('obrazenia', '1d6')

        return attack_roll, attack_bonus, damage_roll


class CombatSystem:
    """System zarządzania walką."""

    def __init__(self, player, monster):
        """
        Inicjalizuje system walki.

        Args:
            player: Postać gracza
            monster: Potwór do walki
        """
        self.player = player
        self.monster = monster
        self.turn = 1

    def start_combat(self):
        """
        Rozpoczyna walkę.

        Returns:
            True jeśli gracz wygrał, False jeśli przegrał
        """
        print_separator("*")
        print(colored_text(f"⚔ WALKA: {self.player.name} vs {self.monster.name}! ⚔", 'red'))
        print_separator("*")
        press_enter()

        # Główna pętla walki
        while self.player.is_alive() and self.monster.is_alive():
            self.combat_turn()
            self.turn += 1

        # Wynik walki
        if self.player.is_alive():
            return self.victory()
        else:
            return self.defeat()

    def combat_turn(self):
        """Pojedyncza tura walki."""
        print_separator("=")
        print(f"TURA {self.turn}")
        print_combat_status(
            self.player.name, self.player.hp, self.player.max_hp,
            self.monster.name, self.monster.hp, self.monster.max_hp
        )

        # Tura gracza
        self.player_turn()

        if not self.monster.is_alive():
            return

        # Tura potwora
        print_separator("-")
        self.monster_turn()

        press_enter()

    def player_turn(self):
        """Tura gracza."""
        print(f"\n--- Twoja tura ---")

        # Menu akcji
        actions = ["Atakuj", "Użyj mikstury", "Uciekaj"]

        # Dodaj zaklęcia jeśli postać je ma
        if self.player.spells and hasattr(self.player, 'mana') and self.player.mana > 0:
            actions.insert(1, "Rzuć zaklęcie")

        print("\nCo chcesz zrobić?")
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action}")

        while True:
            try:
                choice = input("\nWybór: ").strip()
                choice_num = int(choice)
                if 1 <= choice_num <= len(actions):
                    break
                print(f"Wybierz liczbę od 1 do {len(actions)}!")
            except ValueError:
                print("Wprowadź poprawną liczbę!")

        action = actions[choice_num - 1]

        if action == "Atakuj":
            self.player_attack()
        elif action == "Rzuć zaklęcie":
            self.player_cast_spell()
        elif action == "Użyj mikstury":
            self.player_use_item()
        elif action == "Uciekaj":
            if self.attempt_flee():
                return True

    def player_attack(self):
        """Gracz atakuje."""
        # Rzut na trafienie
        attack_roll = d20()
        total_attack = attack_roll + self.player.attack_bonus

        print(f"\n🎲 Rzut na trafienie: {attack_roll} + {self.player.attack_bonus} = {total_attack}")

        # Krytyk
        if attack_roll == 20:
            print(colored_text("💥 KRYTYCZNE TRAFIENIE! 💥", 'yellow'))
            damage_roll = roll(self.player.get_weapon_damage())
            damage = damage_roll * 2
            print(f"⚔ Zadajesz {damage} obrażeń!")
            actual_damage = self.monster.take_damage(damage)
            return

        # Automatyczna porażka
        if attack_roll == 1:
            print(colored_text("💢 KRYTYCZNA PORAŻKA!", 'red'))
            print("Twój atak chybia!")
            return

        # Sprawdź trafienie
        if total_attack >= self.monster.armor_class:
            damage = roll(self.player.get_weapon_damage())
            # Dodaj modyfikator siły/zręczności
            if self.player.equipped['bron']:
                attr = self.player.equipped['bron'].get('atrybut', 'sila')
                damage += self.player.get_modifier(attr)
            else:
                damage += self.player.get_modifier('sila')

            damage = max(1, damage)  # Minimum 1 obrażenie

            print(f"✓ Trafiasz! Zadajesz {damage} obrażeń!")
            actual_damage = self.monster.take_damage(damage)
        else:
            print(colored_text("✗ Chybiasz!", 'red'))

    def player_cast_spell(self):
        """Gracz rzuca zaklęcie."""
        if not self.player.spells:
            print_error("Nie znasz żadnych zaklęć!")
            return

        print("\n--- Twoje zaklęcia ---")
        for i, spell in enumerate(self.player.spells, 1):
            print(f"  {i}. {spell}")

        try:
            choice = int(input("\nWybierz zaklęcie (0 aby anulować): "))
            if choice == 0:
                return
            if 1 <= choice <= len(self.player.spells):
                spell_name = self.player.spells[choice - 1]
                self.cast_spell(spell_name)
            else:
                print_error("Nieprawidłowy wybór!")
        except ValueError:
            print_error("Wprowadź poprawną liczbę!")

    def cast_spell(self, spell_name):
        """
        Rzuca zaklęcie.

        Args:
            spell_name: Nazwa zaklęcia
        """
        # Prosty system zaklęć
        spells = {
            'magiczny_pocisk': {'koszt': 1, 'obrazenia': '3d4+3', 'typ': 'zawsze_trafia'},
            'spalajaca_dlonie': {'koszt': 1, 'obrazenia': '3d6', 'typ': 'rzut_obronny'},
            'kula_ognia': {'koszt': 3, 'obrazenia': '8d6', 'typ': 'rzut_obronny'},
            'lodowy_szturm': {'koszt': 2, 'obrazenia': '4d8', 'typ': 'rzut_obronny'},
            'lańcuch_błyskawic': {'koszt': 3, 'obrazenia': '10d6', 'typ': 'rzut_obronny'},
            'leczenie_ran': {'koszt': 1, 'leczenie': '1d8+4'},
            'swiety_blask': {'koszt': 1, 'obrazenia': '2d8', 'typ': 'magiczny'},
        }

        if spell_name not in spells:
            print_error("Nieznane zaklęcie!")
            return

        spell = spells[spell_name]

        # Sprawdź manę
        if self.player.mana < spell['koszt']:
            print_error("Nie masz wystarczająco many!")
            return

        # Zużyj manę
        self.player.mana -= spell['koszt']

        # Efekt zaklęcia
        if 'leczenie' in spell:
            heal = roll(spell['leczenie'])
            self.player.heal(heal)
            print_success(f"✨ Rzucasz {spell_name}! Leczysz się o {heal} HP!")
        elif 'obrazenia' in spell:
            damage = roll(spell['obrazenia'])
            print(f"✨ Rzucasz {spell_name}!")

            if spell['typ'] == 'zawsze_trafia':
                print(f"⚡ Magiczny pocisk zawsze trafia! Zadajesz {damage} obrażeń!")
                self.monster.take_damage(damage, 'magic')
            elif spell['typ'] == 'rzut_obronny':
                # Prosty rzut obronny
                save_roll = d20() + self.monster.get_modifier('zrecznosc')
                dc = 10 + self.player.get_modifier('inteligencja') + self.player.level // 2
                if save_roll < dc:
                    print(f"💥 {self.monster.name} nie unika! Zadajesz {damage} obrażeń!")
                    self.monster.take_damage(damage, 'magic')
                else:
                    damage = damage // 2
                    print(f"⚠ {self.monster.name} częściowo unika! Zadajesz {damage} obrażeń!")
                    self.monster.take_damage(damage, 'magic')

    def player_use_item(self):
        """Gracz używa przedmiotu."""
        # Znajdź mikstury
        potions = [item for item in self.player.inventory if item.get('typ') == 'mikstura']

        if not potions:
            print_error("Nie masz żadnych mikstur!")
            return

        print("\n--- Twoje mikstury ---")
        for i, potion in enumerate(potions, 1):
            print(f"  {i}. {potion['nazwa']}")

        try:
            choice = int(input("\nWybierz miksturę (0 aby anulować): "))
            if choice == 0:
                return
            if 1 <= choice <= len(potions):
                potion = potions[choice - 1]
                success, message = self.player.use_item(potion)
                if success:
                    print_success(message)
                else:
                    print_error(message)
            else:
                print_error("Nieprawidłowy wybór!")
        except ValueError:
            print_error("Wprowadź poprawną liczbę!")

    def monster_turn(self):
        """Tura potwora."""
        print(f"\n--- Tura {self.monster.name} ---")

        # Potwór atakuje
        attack_roll, attack_bonus, damage_roll = self.monster.attack()
        total_attack = attack_roll + attack_bonus

        print(f"🎲 {self.monster.name} atakuje!")
        print(f"   Rzut: {attack_roll} + {attack_bonus} = {total_attack} vs KP {self.player.armor_class}")

        # Krytyk
        if attack_roll == 20:
            print(colored_text("💥 KRYTYCZNE TRAFIENIE WROGA!", 'red'))
            damage = roll(damage_roll) * 2
            self.player.take_damage(damage)
            print(f"⚔ {self.monster.name} zadaje ci {damage} obrażeń!")
            return

        # Automatyczna porażka
        if attack_roll == 1:
            print(colored_text("✓ Potwór chybia!", 'green'))
            return

        # Sprawdź trafienie
        if total_attack >= self.player.armor_class:
            damage = roll(damage_roll)
            self.player.take_damage(damage)
            print(colored_text(f"✗ {self.monster.name} trafia! Otrzymujesz {damage} obrażeń!", 'red'))
        else:
            print(colored_text(f"✓ Bronisz się przed atakiem!", 'green'))

    def attempt_flee(self):
        """
        Próba ucieczki.

        Returns:
            True jeśli uciekł, False jeśli nie
        """
        # Sprawdź czy to boss - z bossa nie można uciec
        if self.monster.is_boss:
            print_error("Nie możesz uciec od bossa!")
            return False

        # Rzut na ucieczkę
        flee_roll = d20() + self.player.get_modifier('zrecznosc')
        difficulty = 10 + self.monster.level

        if flee_roll >= difficulty:
            print_success("✓ Udaje ci się uciec!")
            return True
        else:
            print_error("✗ Nie udało ci się uciec!")
            # Potwór dostaje darmowy atak
            print_warning("Potwór wykorzystuje okazję!")
            self.monster_turn()
            return False

    def victory(self):
        """Gracz wygrywa walkę."""
        print_separator("*")
        print(colored_text(f"⭐ ZWYCIĘSTWO! ⭐", 'green'))
        print(f"Pokonałeś {self.monster.name}!")

        # Nagroda XP
        print(f"\n+ {self.monster.xp_reward} XP")
        leveled_up = self.player.add_xp(self.monster.xp_reward)

        if leveled_up:
            print_separator("*")
            print(colored_text(f"🌟 AWANS NA POZIOM {self.player.level}! 🌟", 'yellow'))
            print(f"Twoje zdrowie zostało przywrócone!")
            print_separator("*")

        # Lup
        self.generate_loot()

        print_separator("*")
        press_enter()
        return True

    def defeat(self):
        """Gracz przegrywa walkę."""
        print_separator("*")
        print(colored_text("💀 PORAŻKA... 💀", 'red'))
        print(f"{self.monster.name} cię pokonał!")
        print("\nTracisz przytomność...")
        print_separator("*")
        press_enter()
        return False

    def generate_loot(self):
        """Generuje łup po walce."""
        import random

        if not self.monster.loot:
            return

        print("\n💰 Łup:")

        for loot_entry in self.monster.loot:
            # Format: "zloto:50-150" lub "miecz_elficki:20%"
            if isinstance(loot_entry, str):
                parts = loot_entry.split(':')
                item_id = parts[0]

                if item_id == 'zloto':
                    # Losowa ilość złota
                    if len(parts) > 1:
                        gold_range = parts[1].split('-')
                        gold = random.randint(int(gold_range[0]), int(gold_range[1]))
                    else:
                        gold = 10
                    self.player.gold += gold
                    print(f"  + {gold} złota")
                else:
                    # Przedmiot z szansą
                    chance = 100
                    if len(parts) > 1:
                        chance = int(parts[1].rstrip('%'))

                    if random.randint(1, 100) <= chance:
                        # Znajdź przedmiot
                        with open('data/items.json', 'r', encoding='utf-8') as f:
                            items_data = json.load(f)

                        for category in items_data.values():
                            if item_id in category:
                                item = category[item_id].copy()
                                self.player.add_item(item)
                                print(f"  + {item['nazwa']}")
                                break


def load_monster(monster_id):
    """
    Wczytuje potwora z danych.

    Args:
        monster_id: ID potwora

    Returns:
        Obiekt Monster
    """
    with open('data/monsters.json', 'r', encoding='utf-8') as f:
        monsters_data = json.load(f)

    # Szukaj w potworach
    if monster_id in monsters_data['potwory']:
        monster_data = monsters_data['potwory'][monster_id]
        return Monster(monster_id, monster_data)

    # Szukaj w bossach
    if 'bossowie' in monsters_data and monster_id in monsters_data['bossowie']:
        monster_data = monsters_data['bossowie'][monster_id]
        return Monster(monster_id, monster_data)

    return None
