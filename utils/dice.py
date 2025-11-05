"""System rzutów kostką w stylu D&D."""
import random
import re


def roll(dice_string):
    """
    Rzut kostką w notacji D&D (np. "2d6+3", "1d20", "3d8-2").

    Args:
        dice_string: String w formacie "XdY+Z" gdzie:
            X = liczba kostek
            Y = typ kostki (liczba ścianek)
            Z = modyfikator (opcjonalny)

    Returns:
        Wynik rzutu jako int
    """
    # Obsługa przypadku gdy podano samą liczbę
    if isinstance(dice_string, int):
        return dice_string

    dice_string = str(dice_string).lower().strip()

    # Jeśli to sama liczba jako string
    if dice_string.isdigit():
        return int(dice_string)

    # Parsowanie wyrażenia kostki
    # Format: XdY+Z lub XdY-Z lub XdY
    pattern = r'(\d+)d(\d+)([\+\-]\d+)?'
    match = re.match(pattern, dice_string)

    if not match:
        raise ValueError(f"Nieprawidłowy format kostki: {dice_string}")

    num_dice = int(match.group(1))
    dice_type = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    # Wykonanie rzutów
    total = sum(random.randint(1, dice_type) for _ in range(num_dice))
    total += modifier

    return max(0, total)  # Minimum 0


def roll_with_advantage():
    """Rzut z przewagą (rzuć dwa razy k20, weź wyższy wynik)."""
    roll1 = random.randint(1, 20)
    roll2 = random.randint(1, 20)
    return max(roll1, roll2)


def roll_with_disadvantage():
    """Rzut z komplikacją (rzuć dwa razy k20, weź niższy wynik)."""
    roll1 = random.randint(1, 20)
    roll2 = random.randint(1, 20)
    return min(roll1, roll2)


def d20():
    """Prosty rzut k20."""
    return random.randint(1, 20)


def d6():
    """Prosty rzut k6."""
    return random.randint(1, 6)


def d4():
    """Prosty rzut k4."""
    return random.randint(1, 4)


def d8():
    """Prosty rzut k8."""
    return random.randint(1, 8)


def d10():
    """Prosty rzut k10."""
    return random.randint(1, 10)


def d12():
    """Prosty rzut k12."""
    return random.randint(1, 12)


def ability_check(modifier, difficulty=10):
    """
    Test umiejętności.

    Args:
        modifier: Modyfikator do testu
        difficulty: Trudność testu (DC)

    Returns:
        Tuple (sukces: bool, wynik_rzutu: int)
    """
    result = d20() + modifier
    return (result >= difficulty, result)


def saving_throw(modifier, difficulty=10):
    """
    Rzut obronny.

    Args:
        modifier: Modyfikator do rzutu
        difficulty: Trudność (DC)

    Returns:
        Tuple (sukces: bool, wynik_rzutu: int)
    """
    result = d20() + modifier
    return (result >= difficulty, result)


def calculate_modifier(ability_score):
    """
    Oblicza modyfikator na podstawie wartości atrybutu.
    Zgodnie z zasadami D&D 5e.

    Args:
        ability_score: Wartość atrybutu (1-20+)

    Returns:
        Modyfikator (może być ujemny)
    """
    return (ability_score - 10) // 2


def roll_stats():
    """
    Losowanie statystyk postaci metodą 4d6 drop lowest.
    (Rzuć 4 kostkami k6, odrzuć najniższy wynik)

    Returns:
        Lista 6 wylosowanych wartości atrybutów
    """
    stats = []
    for _ in range(6):
        rolls = [d6() for _ in range(4)]
        rolls.remove(min(rolls))  # Usuń najniższy
        stats.append(sum(rolls))
    return stats
