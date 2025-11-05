"""System wyświetlania interfejsu w terminalu."""
import os
import time
import sys


def clear_screen():
    """Czyści ekran terminala."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_separator(char="=", length=70):
    """Drukuje separator."""
    print(char * length)


def print_header(text, char="="):
    """Drukuje nagłówek z separatorami."""
    print_separator(char)
    print(text.center(70))
    print_separator(char)


def print_box(text, width=70):
    """Drukuje tekst w ramce."""
    lines = text.split('\n')
    print("┌" + "─" * (width - 2) + "┐")
    for line in lines:
        padding = width - len(line) - 4
        print(f"│ {line}{' ' * padding} │")
    print("└" + "─" * (width - 2) + "┘")


def print_slow(text, delay=0.03):
    """
    Drukuje tekst znak po znaku z opóźnieniem.

    Args:
        text: Tekst do wydrukowania
        delay: Opóźnienie między znakami w sekundach
    """
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def print_menu(title, options):
    """
    Drukuje menu wyboru.

    Args:
        title: Tytuł menu
        options: Lista opcji jako stringi

    Returns:
        Indeks wybranej opcji (0-based)
    """
    print_header(title)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    print_separator()

    while True:
        try:
            choice = input("\nWybierz opcję: ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(options):
                return choice_num - 1
            else:
                print(f"Wybierz liczbę od 1 do {len(options)}!")
        except ValueError:
            print("Wprowadź poprawną liczbę!")
        except KeyboardInterrupt:
            print("\n\nWyjście z gry...")
            sys.exit(0)


def get_input(prompt=">>> "):
    """
    Pobiera input od użytkownika z obsługą wyjścia.

    Args:
        prompt: Prompt do wyświetlenia

    Returns:
        Input użytkownika
    """
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        print("\n\nWyjście z gry...")
        sys.exit(0)


def confirm(question="Czy jesteś pewien?"):
    """
    Prosi o potwierdzenie (tak/nie).

    Args:
        question: Pytanie do wyświetlenia

    Returns:
        True jeśli tak, False jeśli nie
    """
    while True:
        answer = get_input(f"{question} (t/n): ").lower()
        if answer in ['t', 'tak', 'y', 'yes']:
            return True
        elif answer in ['n', 'nie', 'no']:
            return False
        else:
            print("Odpowiedz 't' (tak) lub 'n' (nie)")


def press_enter(message="Naciśnij ENTER aby kontynuować..."):
    """Czeka na naciśnięcie ENTER."""
    try:
        input(f"\n{message}")
    except KeyboardInterrupt:
        print("\n\nWyjście z gry...")
        sys.exit(0)


def print_combat_status(player_name, player_hp, player_max_hp, enemy_name, enemy_hp, enemy_max_hp):
    """
    Drukuje status walki.

    Args:
        player_name: Imię gracza
        player_hp: Aktualne HP gracza
        player_max_hp: Maksymalne HP gracza
        enemy_name: Nazwa wroga
        enemy_hp: Aktualne HP wroga
        enemy_max_hp: Maksymalne HP wroga
    """
    print_separator("*")

    # Status gracza
    player_hp_percent = (player_hp / player_max_hp * 100) if player_max_hp > 0 else 0
    player_bar = create_hp_bar(player_hp, player_max_hp)
    print(f"{player_name}: {player_hp}/{player_max_hp} HP {player_bar}")

    # Status wroga
    enemy_hp_percent = (enemy_hp / enemy_max_hp * 100) if enemy_max_hp > 0 else 0
    enemy_bar = create_hp_bar(enemy_hp, enemy_max_hp)
    print(f"{enemy_name}: {enemy_hp}/{enemy_max_hp} HP {enemy_bar}")

    print_separator("*")


def create_hp_bar(current_hp, max_hp, length=20):
    """
    Tworzy wizualny pasek HP.

    Args:
        current_hp: Aktualne HP
        max_hp: Maksymalne HP
        length: Długość paska w znakach

    Returns:
        String z paskiem HP
    """
    if max_hp <= 0:
        return "[" + " " * length + "]"

    filled = int((current_hp / max_hp) * length)
    filled = max(0, min(filled, length))  # Clamp do 0-length

    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"


def print_stats_panel(character):
    """
    Drukuje panel ze statystykami postaci.

    Args:
        character: Obiekt postaci
    """
    print_separator("=")
    print(f"  {character.name} - Poziom {character.level} {character.character_class}")
    print_separator("-")
    print(f"  HP: {character.hp}/{character.max_hp}  |  XP: {character.xp}/{character.xp_to_next_level()}")
    if hasattr(character, 'mana'):
        print(f"  Mana: {character.mana}/{character.max_mana}")
    print_separator("-")
    print(f"  Siła: {character.attributes['sila']} ({character.get_modifier('sila'):+d})  |  "
          f"Zręczność: {character.attributes['zrecznosc']} ({character.get_modifier('zrecznosc'):+d})")
    print(f"  Kondycja: {character.attributes['kondycja']} ({character.get_modifier('kondycja'):+d})  |  "
          f"Inteligencja: {character.attributes['inteligencja']} ({character.get_modifier('inteligencja'):+d})")
    print(f"  Mądrość: {character.attributes['madrosc']} ({character.get_modifier('madrosc'):+d})  |  "
          f"Charyzma: {character.attributes['charyzma']} ({character.get_modifier('charyzma'):+d})")
    print_separator("-")
    print(f"  KP: {character.armor_class}  |  Bonus ataku: {character.attack_bonus:+d}")
    print(f"  Złoto: {character.gold}")
    print_separator("=")


def print_inventory(items):
    """
    Drukuje ekwipunek.

    Args:
        items: Lista przedmiotów
    """
    if not items:
        print("Ekwipunek jest pusty.")
        return

    print_header("EKWIPUNEK")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item.get('nazwa', 'Nieznany przedmiot')}")
        if 'opis' in item:
            print(f"     {item['opis']}")
    print_separator()


def colored_text(text, color='default'):
    """
    Zwraca tekst w kolorze (jeśli terminal obsługuje).

    Args:
        text: Tekst do pokolorowania
        color: Kolor ('red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white')

    Returns:
        Pokolorowany tekst
    """
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'default': '\033[0m'
    }

    reset = '\033[0m'
    color_code = colors.get(color, colors['default'])
    return f"{color_code}{text}{reset}"


def print_error(text):
    """Drukuje komunikat błędu."""
    print(colored_text(f"✗ {text}", 'red'))


def print_success(text):
    """Drukuje komunikat sukcesu."""
    print(colored_text(f"✓ {text}", 'green'))


def print_warning(text):
    """Drukuje ostrzeżenie."""
    print(colored_text(f"⚠ {text}", 'yellow'))


def print_info(text):
    """Drukuje informację."""
    print(colored_text(f"ℹ {text}", 'cyan'))
