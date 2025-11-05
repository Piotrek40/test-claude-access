"""System postaci gracza."""
import json
from utils.dice import calculate_modifier, roll


class Character:
    """Klasa reprezentująca postać gracza."""

    def __init__(self, name, character_class, attributes):
        """
        Inicjalizuje postać.

        Args:
            name: Imię postaci
            character_class: Klasa postaci (np. 'wojownik', 'mag')
            attributes: Dict z atrybutami (sila, zrecznosc, etc.)
        """
        self.name = name
        self.character_class = character_class
        self.attributes = attributes
        self.level = 1
        self.xp = 0

        # Wczytaj dane klasy
        with open('data/classes.json', 'r', encoding='utf-8') as f:
            classes_data = json.load(f)

        self.class_data = classes_data['classes'][character_class]

        # Inicjalizuj HP
        self.max_hp = self.class_data['kostka_zdrowia'] + self.get_modifier('kondycja')
        self.hp = self.max_hp

        # Mana dla klas magicznych
        self.mana = 0
        self.max_mana = 0
        if 'zaklecia_startowe' in self.class_data:
            bonusy = self.class_data['bonusy_na_poziom']['1']
            if 'mana' in bonusy:
                self.max_mana = bonusy['mana'] + self.get_modifier('inteligencja')
                self.mana = self.max_mana

        # Ekwipunek
        self.inventory = []
        self.equipped = {
            'bron': None,
            'zbroja': None,
            'tarcza': None
        }
        self.gold = 100

        # Inicjalizuj startowy ekwipunek
        self._init_starting_equipment()

        # Umiejętności
        self.skills = self.class_data.get('umiejetnosci', [])

        # Zaklęcia (jeśli klasa magiczna)
        self.spells = []
        if 'zaklecia_startowe' in self.class_data:
            self.spells = self.class_data['zaklecia_startowe'].copy()

        # Sloty zaklęć
        self.spell_slots = {}
        if 'sloty_zakleć' in self.class_data:
            self.spell_slots = self.class_data['sloty_zakleć']['1'].copy()

        # Questy
        self.active_quests = []
        self.completed_quests = []

        # Lokacja
        self.current_location = 'startowa_wioska'

        # Efekty statusowe
        self.status_effects = []

    def _init_starting_equipment(self):
        """Inicjalizuje startowy ekwipunek."""
        with open('data/items.json', 'r', encoding='utf-8') as f:
            items_data = json.load(f)

        for item_id in self.class_data['ekwipunek_startowy']:
            # Szukaj przedmiotu we wszystkich kategoriach
            item = None
            for category in items_data.values():
                if item_id in category:
                    item = category[item_id].copy()
                    break

            if item:
                self.inventory.append(item)
                # Auto-ekwipuj pierwszą broń i zbroję
                if item['typ'] == 'bron' and not self.equipped['bron']:
                    self.equipped['bron'] = item
                elif item['typ'] == 'zbroja' and not self.equipped['zbroja']:
                    self.equipped['zbroja'] = item
                elif item['typ'] == 'tarcza' and not self.equipped['tarcza']:
                    self.equipped['tarcza'] = item

    def get_modifier(self, attribute):
        """Zwraca modyfikator dla danego atrybutu."""
        return calculate_modifier(self.attributes[attribute])

    @property
    def armor_class(self):
        """Oblicza klasę pancerza (KP/AC)."""
        base_ac = 10
        dex_mod = self.get_modifier('zrecznosc')

        # Zbroja
        if self.equipped['zbroja']:
            armor = self.equipped['zbroja']
            base_ac = armor['klasa_pancerza']
            if not armor.get('bonus_zrecznosci', False):
                dex_mod = 0

        ac = base_ac + dex_mod

        # Tarcza
        if self.equipped['tarcza']:
            ac += self.equipped['tarcza'].get('bonus_kp', 0)

        return ac

    @property
    def attack_bonus(self):
        """Oblicza bonus do ataku."""
        bonus = self.level // 2 + 1  # Bonus biegłości

        # Dodaj modyfikator z głównego atrybutu
        if self.equipped['bron']:
            weapon = self.equipped['bron']
            attr = weapon.get('atrybut', 'sila')
            bonus += self.get_modifier(attr)
            bonus += weapon.get('bonus_ataku', 0)
        else:
            # Bez broni - używaj siły
            bonus += self.get_modifier('sila')

        return bonus

    def get_weapon_damage(self):
        """Zwraca obrazenia broni."""
        if self.equipped['bron']:
            weapon = self.equipped['bron']
            return weapon['obrazenia']
        else:
            # Bez broni - pięści
            return "1d4"

    def take_damage(self, damage):
        """
        Otrzymuje obrażenia.

        Args:
            damage: Ilość obrażeń

        Returns:
            Aktualne HP po obrażeniach
        """
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        return self.hp

    def heal(self, amount):
        """
        Leczy postać.

        Args:
            amount: Ilość uleczonego HP
        """
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        return self.hp

    def is_alive(self):
        """Sprawdza czy postać żyje."""
        return self.hp > 0

    def add_xp(self, amount):
        """
        Dodaje doświadczenie.

        Args:
            amount: Ilość doświadczenia

        Returns:
            True jeśli postać awansowała na nowy poziom
        """
        self.xp += amount
        if self.xp >= self.xp_to_next_level():
            self.level_up()
            return True
        return False

    def xp_to_next_level(self):
        """Zwraca ilość XP potrzebną do następnego poziomu."""
        return self.level * 1000

    def level_up(self):
        """Awansuje postać na kolejny poziom."""
        self.level += 1
        self.xp = 0

        # Pobierz bonusy dla nowego poziomu
        level_str = str(self.level)
        if level_str in self.class_data['bonusy_na_poziom']:
            bonuses = self.class_data['bonusy_na_poziom'][level_str]

            # Zwiększ HP
            if 'zdrowię' in bonuses:
                hp_gain = bonuses['zdrowię'] + self.get_modifier('kondycja')
                self.max_hp += hp_gain
                self.hp = self.max_hp

            # Zwiększ manę (dla klas magicznych)
            if 'mana' in bonuses:
                mana_gain = bonuses['mana']
                self.max_mana += mana_gain
                self.mana = self.max_mana

            # Zaktualizuj sloty zaklęć
            if 'sloty_zakleć' in self.class_data and level_str in self.class_data['sloty_zakleć']:
                self.spell_slots = self.class_data['sloty_zakleć'][level_str].copy()

    def add_item(self, item):
        """Dodaje przedmiot do ekwipunku."""
        self.inventory.append(item)

    def remove_item(self, item):
        """Usuwa przedmiot z ekwipunku."""
        if item in self.inventory:
            self.inventory.remove(item)

    def equip_item(self, item):
        """
        Ekwipuje przedmiot.

        Args:
            item: Przedmiot do ekwipowania

        Returns:
            True jeśli udało się ekwipować
        """
        item_type = item.get('typ')

        if item_type == 'bron':
            # Zdejmij starą broń
            if self.equipped['bron']:
                pass  # Stara broń pozostaje w ekwipunku
            self.equipped['bron'] = item
            return True
        elif item_type == 'zbroja':
            if self.equipped['zbroja']:
                pass
            self.equipped['zbroja'] = item
            return True
        elif item_type == 'tarcza':
            if self.equipped['tarcza']:
                pass
            self.equipped['tarcza'] = item
            return True

        return False

    def use_item(self, item):
        """
        Używa przedmiotu (np. mikstury).

        Args:
            item: Przedmiot do użycia

        Returns:
            Tuple (sukces: bool, wiadomość: str)
        """
        if item.get('typ') == 'mikstura':
            effect = item.get('efekt')

            if effect == 'leczenie':
                heal_amount = roll(item['moc'])
                self.heal(heal_amount)
                self.remove_item(item)
                return True, f"Wypiłeś {item['nazwa']} i odzyskałeś {heal_amount} HP!"

            elif effect == 'mana':
                if not hasattr(self, 'mana'):
                    return False, "Nie możesz używać mikstur many!"
                mana_amount = roll(item['moc'])
                self.mana += mana_amount
                if self.mana > self.max_mana:
                    self.mana = self.max_mana
                self.remove_item(item)
                return True, f"Wypiłeś {item['nazwa']} i odzyskałeś {mana_amount} many!"

        return False, "Nie możesz tego użyć!"

    def rest(self):
        """Odpoczynek - przywraca HP i manę."""
        self.hp = self.max_hp
        if hasattr(self, 'mana'):
            self.mana = self.max_mana
        # Przywróć sloty zaklęć
        level_str = str(self.level)
        if 'sloty_zakleć' in self.class_data and level_str in self.class_data['sloty_zakleć']:
            self.spell_slots = self.class_data['sloty_zakleć'][level_str].copy()

    def to_dict(self):
        """Konwertuje postać do słownika (do zapisu)."""
        return {
            'name': self.name,
            'character_class': self.character_class,
            'attributes': self.attributes,
            'level': self.level,
            'xp': self.xp,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'mana': self.mana,
            'max_mana': self.max_mana,
            'inventory': self.inventory,
            'equipped': self.equipped,
            'gold': self.gold,
            'skills': self.skills,
            'spells': self.spells,
            'spell_slots': self.spell_slots,
            'active_quests': self.active_quests,
            'completed_quests': self.completed_quests,
            'current_location': self.current_location,
            'status_effects': self.status_effects
        }

    @staticmethod
    def from_dict(data):
        """Tworzy postać ze słownika (z zapisu)."""
        char = Character(data['name'], data['character_class'], data['attributes'])
        char.level = data['level']
        char.xp = data['xp']
        char.hp = data['hp']
        char.max_hp = data['max_hp']
        char.mana = data['mana']
        char.max_mana = data['max_mana']
        char.inventory = data['inventory']
        char.equipped = data['equipped']
        char.gold = data['gold']
        char.skills = data['skills']
        char.spells = data['spells']
        char.spell_slots = data['spell_slots']
        char.active_quests = data['active_quests']
        char.completed_quests = data['completed_quests']
        char.current_location = data['current_location']
        char.status_effects = data['status_effects']
        return char
