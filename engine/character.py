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

        # System talentów
        self.talent_points = 0  # Punkty talentów do wydania
        self.learned_talents = []  # Lista wyuczonych talentów (IDs)
        self.talent_cooldowns = {}  # Cooldowny aktywnych talentów {talent_id: pozostałe_tury}
        self.talent_buffs = {}  # Aktywne buffy z talentów {buff_name: remaining_turns}

        # System reputacji frakcji (-100 do 100)
        self.reputation = {
            'kosciol': 0,      # Kościół Wiecznego Płomienia
            'orkden': 0,       # Orkden Nowego Świtu
            'zmierzchli': 0,   # Zmierzchli
            'starfall': 50,    # Wioska Starfall (zaczynamy jako resident)
            'nobility': 0,     # Arystokracja (minor)
            'merchants': 0     # Gildia Kupiecka (minor)
        }

        # Tracking głównych wyborów (dla endings i consequences)
        self.major_choices = {}  # {choice_id: selected_option}

        # Flags dla questów i eventów
        self.story_flags = set()  # Set stringów np. 'starfall_evacuated', 'cassian_redeemed'

        # Companioni
        self.companions = []  # Lista companion IDs którzy dołączyli
        self.active_party = []  # Lista companion IDs w aktywnej drużynie (max 3)

        # System romansów
        self.romances = {
            'theron': {
                'approval': 0,           # 0-100
                'romance_active': False,  # Czy romance się zaczął
                'romance_locked': False,  # Czy zablokowany (wybrano kogoś innego)
                'scenes_unlocked': [],   # Lista scene IDs które odblokowano
                'relationship_stage': 'stranger'  # 'stranger', 'friend', 'close_friend', 'romantic_interest', 'lover'
            },
            'seraph': {
                'approval': 0,
                'romance_active': False,
                'romance_locked': False,
                'scenes_unlocked': [],
                'relationship_stage': 'stranger'
            },
            'mira': {
                'approval': 0,
                'romance_active': False,
                'romance_locked': False,
                'scenes_unlocked': [],
                'relationship_stage': 'stranger'
            },
            'pyrus': {
                'approval': 0,
                'romance_active': False,
                'romance_locked': False,
                'scenes_unlocked': [],
                'relationship_stage': 'stranger'
            },
            'morwen': {
                'approval': 0,
                'romance_active': False,
                'romance_locked': False,
                'scenes_unlocked': [],
                'relationship_stage': 'stranger'
            }
        }

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

        # Daj punkt talentu (od poziomu 2)
        if self.level >= 2:
            self.talent_points += 1

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

    # ===== SYSTEM TALENTÓW =====

    def get_talent_data(self, talent_id):
        """
        Pobiera dane talentu z JSON.

        Args:
            talent_id: ID talentu (np. 'berserker_1')

        Returns:
            Dict z danymi talentu lub None
        """
        with open('data/talents.json', 'r', encoding='utf-8') as f:
            talents_data = json.load(f)

        # Szukaj talentu w odpowiedniej klasie i ścieżce
        for tree_name, tree_data in talents_data[self.character_class].items():
            if talent_id in tree_data['talenty']:
                return tree_data['talenty'][talent_id]
        return None

    def can_learn_talent(self, talent_id):
        """
        Sprawdza czy postać może się nauczyć talentu.

        Args:
            talent_id: ID talentu

        Returns:
            Tuple (możliwe: bool, powód: str)
        """
        # Czy już ma ten talent?
        if talent_id in self.learned_talents:
            return False, "Już znasz ten talent!"

        talent_data = self.get_talent_data(talent_id)
        if not talent_data:
            return False, "Nieznany talent!"

        # Sprawdź poziom postaci
        if self.level < talent_data['wymagany_poziom_postaci']:
            return False, f"Wymagany poziom {talent_data['wymagany_poziom_postaci']}"

        # Sprawdź wymagania (poprzedni talent)
        if 'wymaga' in talent_data:
            required_talent = talent_data['wymaga']
            if required_talent not in self.learned_talents:
                req_data = self.get_talent_data(required_talent)
                return False, f"Wymaga talentu: {req_data['nazwa']}"

        # Sprawdź punkty talentów
        if self.talent_points <= 0:
            return False, "Brak punktów talentów!"

        return True, "OK"

    def learn_talent(self, talent_id):
        """
        Uczy postać talentu.

        Args:
            talent_id: ID talentu

        Returns:
            Tuple (sukces: bool, wiadomość: str)
        """
        can_learn, reason = self.can_learn_talent(talent_id)
        if not can_learn:
            return False, reason

        talent_data = self.get_talent_data(talent_id)
        self.learned_talents.append(talent_id)
        self.talent_points -= 1

        return True, f"Nauczyłeś się: {talent_data['nazwa']}!"

    def has_talent(self, talent_id):
        """Sprawdza czy postać ma dany talent."""
        return talent_id in self.learned_talents

    def get_active_talents(self):
        """
        Zwraca listę aktywnych talentów (do użycia w walce).

        Returns:
            Lista tuple (talent_id, talent_data)
        """
        active = []
        for talent_id in self.learned_talents:
            talent_data = self.get_talent_data(talent_id)
            if talent_data and talent_data['typ'] == 'aktywny':
                # Sprawdź cooldown
                if talent_id not in self.talent_cooldowns or self.talent_cooldowns[talent_id] <= 0:
                    active.append((talent_id, talent_data))
        return active

    def use_talent(self, talent_id):
        """
        Używa aktywnego talentu (ustawia cooldown).

        Args:
            talent_id: ID talentu

        Returns:
            Tuple (sukces: bool, efekt: dict)
        """
        if talent_id not in self.learned_talents:
            return False, None

        talent_data = self.get_talent_data(talent_id)
        if not talent_data or talent_data['typ'] != 'aktywny':
            return False, None

        # Sprawdź cooldown
        if talent_id in self.talent_cooldowns and self.talent_cooldowns[talent_id] > 0:
            return False, None

        # Sprawdź koszt many (jeśli jest)
        if 'mana_cost' in talent_data['efekt']:
            cost = talent_data['efekt']['mana_cost']
            if hasattr(self, 'mana') and self.mana >= cost:
                self.mana -= cost
            else:
                return False, None

        # Ustaw cooldown
        if 'cooldown' in talent_data['efekt']:
            self.talent_cooldowns[talent_id] = talent_data['efekt']['cooldown']

        return True, talent_data['efekt']

    def update_talent_cooldowns(self):
        """Aktualizuje cooldowny talentów (wywołuj co turę)."""
        for talent_id in list(self.talent_cooldowns.keys()):
            if self.talent_cooldowns[talent_id] > 0:
                self.talent_cooldowns[talent_id] -= 1

    def get_talent_bonuses(self):
        """
        Oblicza wszystkie bonusy z pasywnych talentów.

        Returns:
            Dict z bonusami
        """
        bonuses = {
            'damage_bonus': 0,
            'armor_bonus': 0,
            'attack_bonus': 0,
            'crit_chance': 0,
            'dodge_chance': 0,
            'life_aura': 0,
            'combat_regen': 0,
        }

        for talent_id in self.learned_talents:
            talent_data = self.get_talent_data(talent_id)
            if not talent_data or talent_data['typ'] != 'pasywny':
                continue

            efekt = talent_data['efekt']
            typ = efekt['typ']

            # Mapuj efekty na bonusy
            if typ == 'damage_bonus':
                bonuses['damage_bonus'] += efekt['wartosc']
            elif typ == 'armor_bonus':
                bonuses['armor_bonus'] += efekt['wartosc']
            elif typ == 'attack_bonus':
                bonuses['attack_bonus'] += efekt['wartosc']
            elif typ == 'crit_chance':
                bonuses['crit_chance'] += efekt['wartosc']
            elif typ == 'dodge_chance':
                bonuses['dodge_chance'] += efekt['wartosc']
            elif typ == 'life_aura':
                bonuses['life_aura'] += efekt['heal_per_turn']
            elif typ == 'combat_regen':
                bonuses['combat_regen'] += efekt['wartosc']

        return bonuses

    # ===== KONIEC SYSTEMU TALENTÓW =====

    # ===== SYSTEM REPUTACJI =====

    def change_reputation(self, faction, amount):
        """
        Zmienia reputację z frakcją.

        Args:
            faction: ID frakcji ('kosciol', 'orkden', 'zmierzchli', etc.)
            amount: Zmiana reputacji (+/-)

        Returns:
            Tuple (nowa_reputacja, tier_name, tier_changed)
        """
        if faction not in self.reputation:
            return None, None, False

        old_tier = self.get_reputation_tier(faction)
        self.reputation[faction] = max(-100, min(100, self.reputation[faction] + amount))
        new_tier = self.get_reputation_tier(faction)

        tier_changed = (old_tier != new_tier)

        return self.reputation[faction], new_tier, tier_changed

    def get_reputation_tier(self, faction):
        """
        Zwraca tier reputacji dla frakcji.

        Returns:
            String: 'apostate', 'heretic', 'enemy', 'suspected', 'distrusted',
                    'tolerated', 'accepted', 'respected', 'honored', 'champion'
        """
        rep = self.reputation.get(faction, 0)

        if rep <= -80:
            return 'apostate'
        elif rep <= -60:
            return 'heretic'
        elif rep <= -40:
            return 'enemy'
        elif rep <= -20:
            return 'suspected'
        elif rep < 0:
            return 'distrusted'
        elif rep < 20:
            return 'tolerated'
        elif rep < 40:
            return 'accepted'
        elif rep < 60:
            return 'respected'
        elif rep < 80:
            return 'honored'
        else:
            return 'champion'

    def get_reputation_tier_pl(self, faction):
        """Zwraca polską nazwę tier reputacji."""
        tier = self.get_reputation_tier(faction)
        tiers_pl = {
            'apostate': 'Apostata',
            'heretic': 'Heretyk',
            'enemy': 'Wróg',
            'suspected': 'Podejrzany',
            'distrusted': 'Nieufany',
            'tolerated': 'Tolerowany',
            'accepted': 'Zaakceptowany',
            'respected': 'Szanowany',
            'honored': 'Honorowany',
            'champion': 'Mistrz'
        }
        return tiers_pl.get(tier, 'Nieznany')

    # ===== SYSTEM WYBORÓW I FLAGS =====

    def make_choice(self, choice_id, selected_option):
        """
        Rejestruje główny wybór gracza.

        Args:
            choice_id: ID wyboru (np. 'starfall_fate')
            selected_option: Wybrana opcja (np. 'evacuate', 'defend')
        """
        self.major_choices[choice_id] = selected_option

    def get_choice(self, choice_id):
        """Zwraca wybraną opcję dla danego wyboru."""
        return self.major_choices.get(choice_id)

    def add_flag(self, flag):
        """Dodaje story flag."""
        self.story_flags.add(flag)

    def has_flag(self, flag):
        """Sprawdza czy ma dany flag."""
        return flag in self.story_flags

    def remove_flag(self, flag):
        """Usuwa story flag."""
        self.story_flags.discard(flag)

    # ===== SYSTEM COMPANIONÓW =====

    def add_companion(self, companion_id):
        """
        Dodaje companiona do drużyny.

        Args:
            companion_id: ID companiona (np. 'theron', 'mira')

        Returns:
            bool: True jeśli dodano
        """
        if companion_id not in self.companions:
            self.companions.append(companion_id)
            # Automatycznie dodaj do aktywnej party jeśli jest miejsce
            if len(self.active_party) < 3:
                self.active_party.append(companion_id)
            return True
        return False

    def remove_companion(self, companion_id):
        """Usuwa companiona (np. gdy umiera lub odchodzi)."""
        if companion_id in self.companions:
            self.companions.remove(companion_id)
        if companion_id in self.active_party:
            self.active_party.remove(companion_id)

    def has_companion(self, companion_id):
        """Sprawdza czy companion jest w drużynie."""
        return companion_id in self.companions

    # ===== SYSTEM ROMANSÓW =====

    def change_approval(self, companion_id, amount):
        """
        Zmienia approval z companionem.

        Args:
            companion_id: ID companiona
            amount: Zmiana approval (+/-)

        Returns:
            Tuple (new_approval, old_stage, new_stage, stage_changed)
        """
        if companion_id not in self.romances:
            return None, None, None, False

        romance = self.romances[companion_id]
        old_stage = romance['relationship_stage']

        romance['approval'] = max(0, min(100, romance['approval'] + amount))

        # Automatycznie update relationship stage
        new_approval = romance['approval']
        if new_approval >= 81:
            romance['relationship_stage'] = 'lover' if romance['romance_active'] else 'romantic_interest'
        elif new_approval >= 61:
            romance['relationship_stage'] = 'romantic_interest' if romance['romance_active'] else 'close_friend'
        elif new_approval >= 41:
            romance['relationship_stage'] = 'close_friend'
        elif new_approval >= 21:
            romance['relationship_stage'] = 'friend'
        else:
            romance['relationship_stage'] = 'stranger'

        new_stage = romance['relationship_stage']
        stage_changed = (old_stage != new_stage)

        return new_approval, old_stage, new_stage, stage_changed

    def start_romance(self, companion_id):
        """
        Rozpoczyna romance z companionem (po pierwszym kiss).

        Args:
            companion_id: ID companiona

        Returns:
            bool: True jeśli można rozpocząć
        """
        if companion_id not in self.romances:
            return False

        romance = self.romances[companion_id]

        # Sprawdź czy jest zablokowany
        if romance['romance_locked']:
            return False

        # Sprawdź approval (minimum 61 do romance)
        if romance['approval'] < 61:
            return False

        # Zablokuj inne romanse (monogamy)
        for other_id, other_romance in self.romances.items():
            if other_id != companion_id:
                other_romance['romance_locked'] = True

        romance['romance_active'] = True
        romance['relationship_stage'] = 'romantic_interest'

        return True

    def unlock_romance_scene(self, companion_id, scene_id):
        """Odblokowuje scenę romantyczną."""
        if companion_id in self.romances:
            if scene_id not in self.romances[companion_id]['scenes_unlocked']:
                self.romances[companion_id]['scenes_unlocked'].append(scene_id)

    def has_romance_scene(self, companion_id, scene_id):
        """Sprawdza czy scena została odblokowana."""
        if companion_id in self.romances:
            return scene_id in self.romances[companion_id]['scenes_unlocked']
        return False

    def get_romance_status(self, companion_id):
        """Zwraca pełny status romansu z companionem."""
        return self.romances.get(companion_id)

    def is_romancing(self, companion_id):
        """Sprawdza czy jest w romansie z companionem."""
        if companion_id in self.romances:
            return self.romances[companion_id]['romance_active']
        return False

    def get_active_romance(self):
        """Zwraca ID companiona z którym jest aktywny romans (lub None)."""
        for companion_id, romance in self.romances.items():
            if romance['romance_active']:
                return companion_id
        return None

    # ===== KONIEC SYSTEMU ROMANSÓW =====

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
            'status_effects': self.status_effects,
            'talent_points': self.talent_points,
            'learned_talents': self.learned_talents,
            'talent_cooldowns': self.talent_cooldowns,
            'talent_buffs': self.talent_buffs,
            # Nowe systemy
            'reputation': self.reputation,
            'major_choices': self.major_choices,
            'story_flags': list(self.story_flags),  # Set -> list dla JSON
            'companions': self.companions,
            'active_party': self.active_party,
            'romances': self.romances
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
        char.talent_points = data.get('talent_points', 0)
        char.learned_talents = data.get('learned_talents', [])
        char.talent_cooldowns = data.get('talent_cooldowns', {})
        char.talent_buffs = data.get('talent_buffs', {})
        # Nowe systemy (z defaults dla starych save'ów)
        char.reputation = data.get('reputation', {
            'kosciol': 0, 'orkden': 0, 'zmierzchli': 0,
            'starfall': 50, 'nobility': 0, 'merchants': 0
        })
        char.major_choices = data.get('major_choices', {})
        char.story_flags = set(data.get('story_flags', []))  # List -> set
        char.companions = data.get('companions', [])
        char.active_party = data.get('active_party', [])
        char.romances = data.get('romances', {
            'theron': {'approval': 0, 'romance_active': False, 'romance_locked': False, 'scenes_unlocked': [], 'relationship_stage': 'stranger'},
            'seraph': {'approval': 0, 'romance_active': False, 'romance_locked': False, 'scenes_unlocked': [], 'relationship_stage': 'stranger'},
            'mira': {'approval': 0, 'romance_active': False, 'romance_locked': False, 'scenes_unlocked': [], 'relationship_stage': 'stranger'},
            'pyrus': {'approval': 0, 'romance_active': False, 'romance_locked': False, 'scenes_unlocked': [], 'relationship_stage': 'stranger'},
            'morwen': {'approval': 0, 'romance_active': False, 'romance_locked': False, 'scenes_unlocked': [], 'relationship_stage': 'stranger'}
        })
        return char
