"""System companionów - NPCs którzy dołączają do drużyny gracza."""
import json
from utils.dice import calculate_modifier, roll


class Companion:
    """Klasa reprezentująca companiona (NPC towarzyszący graczowi)."""

    def __init__(self, companion_id):
        """
        Inicjalizuje companiona.

        Args:
            companion_id: ID companiona (np. 'theron', 'mira', 'seraph')
        """
        self.companion_id = companion_id
        self.load_data()

    def load_data(self):
        """Wczytuje dane companiona z JSON."""
        with open('data/companions.json', 'r', encoding='utf-8') as f:
            companions_data = json.load(f)

        if self.companion_id not in companions_data:
            raise ValueError(f"Nieznany companion: {self.companion_id}")

        data = companions_data[self.companion_id]

        # Podstawowe info
        self.name = data['nazwa']
        self.description = data['opis']
        self.character_class = data['klasa']
        self.personality = data['osobowosc']
        self.romance_available = data.get('romance', False)
        self.gender = data.get('gender', 'male')

        # Atrybuty bojowe
        self.level = data['poziom']
        self.max_hp = data['hp']
        self.hp = self.max_hp
        self.armor_class = data['kp']
        self.attack_bonus = data['bonus_ataku']
        self.damage = data['obrazenia']

        # Atrybuty
        self.attributes = data.get('atrybuty', {
            'sila': 10, 'zrecznosc': 10, 'kondycja': 10,
            'inteligencja': 10, 'madrosc': 10, 'charyzma': 10
        })

        # Umiejętności specjalne
        self.special_abilities = data.get('umiejetnosci_specjalne', [])

        # Status
        self.is_alive = True
        self.can_leave = data.get('moze_odejsc', True)  # Niektórzy companioni mogą odejść jeśli są nieszczęśliwi

        # Preferences (co lubi/nie lubi - dla approval)
        self.likes = data.get('lubi', [])
        self.dislikes = data.get('nie_lubi', [])

    def take_damage(self, damage):
        """
        Otrzymuje obrażenia.

        Args:
            damage: Ilość obrażeń

        Returns:
            Aktualne HP
        """
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
        return self.hp

    def heal(self, amount):
        """Leczy companiona."""
        if self.is_alive:
            self.hp += amount
            if self.hp > self.max_hp:
                self.hp = self.max_hp
        return self.hp

    def rest(self):
        """Odpoczynek - przywraca HP."""
        if self.is_alive:
            self.hp = self.max_hp

    def get_modifier(self, attribute):
        """Zwraca modyfikator dla danego atrybutu."""
        return calculate_modifier(self.attributes.get(attribute, 10))

    def can_use_ability(self, ability_id):
        """Sprawdza czy companion może użyć danej umiejętności."""
        return ability_id in self.special_abilities

    def get_combat_stats(self):
        """Zwraca statystyki bojowe jako dict."""
        return {
            'name': self.name,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'ac': self.armor_class,
            'attack_bonus': self.attack_bonus,
            'damage': self.damage,
            'is_alive': self.is_alive
        }

    def __str__(self):
        """Reprezentacja stringowa companiona."""
        status = "✓" if self.is_alive else "✗"
        return f"{status} {self.name} ({self.character_class}) - HP: {self.hp}/{self.max_hp}"


class CompanionManager:
    """Manager zarządzający wszystkimi companionami w grze."""

    def __init__(self, player):
        """
        Inicjalizuje CompanionManager.

        Args:
            player: Obiekt Character gracza
        """
        self.player = player
        self.loaded_companions = {}  # {companion_id: Companion object}

    def add_companion(self, companion_id):
        """
        Dodaje companiona do drużyny gracza.

        Args:
            companion_id: ID companiona

        Returns:
            Companion object lub None jeśli błąd
        """
        if companion_id in self.loaded_companions:
            return self.loaded_companions[companion_id]

        try:
            companion = Companion(companion_id)
            self.loaded_companions[companion_id] = companion
            self.player.add_companion(companion_id)
            return companion
        except (FileNotFoundError, ValueError) as e:
            print(f"Błąd dodawania companiona: {e}")
            return None

    def get_companion(self, companion_id):
        """Zwraca obiekt Companion lub None."""
        return self.loaded_companions.get(companion_id)

    def get_active_party(self):
        """Zwraca listę aktywnych companionów (jako obiekty)."""
        active = []
        for comp_id in self.player.active_party:
            if comp_id in self.loaded_companions:
                active.append(self.loaded_companions[comp_id])
        return active

    def remove_companion(self, companion_id, reason='left'):
        """
        Usuwa companiona z drużyny.

        Args:
            companion_id: ID companiona
            reason: Powód ('left', 'died', 'betrayed')
        """
        if companion_id in self.loaded_companions:
            del self.loaded_companions[companion_id]
        self.player.remove_companion(companion_id)

        # Dodaj flag zależny od powodu
        if reason == 'died':
            self.player.add_flag(f'{companion_id}_dead')
        elif reason == 'left':
            self.player.add_flag(f'{companion_id}_left')
        elif reason == 'betrayed':
            self.player.add_flag(f'{companion_id}_betrayed')

    def rest_all(self):
        """Odpoczynek dla wszystkich companionów."""
        for companion in self.loaded_companions.values():
            companion.rest()

    def is_companion_available(self, companion_id):
        """Sprawdza czy companion jest dostępny (nie umarł, nie odszedł)."""
        if self.player.has_flag(f'{companion_id}_dead'):
            return False
        if self.player.has_flag(f'{companion_id}_left'):
            return False
        if self.player.has_flag(f'{companion_id}_betrayed'):
            return False
        return True

    def get_companion_dialogue(self, companion_id, context='default'):
        """
        Zwraca dialogue companiona w danym kontekście.

        Args:
            companion_id: ID companiona
            context: Kontekst (np. 'greeting', 'combat', 'camp', 'romance')

        Returns:
            String z dialogiem
        """
        # To będzie wczytywać z companions.json -> 'dialogi' -> context
        companion = self.get_companion(companion_id)
        if not companion:
            return None

        # TODO: Implement dialogue loading from JSON
        # For now, placeholder
        return f"{companion.name}: [dialogue for {context}]"
