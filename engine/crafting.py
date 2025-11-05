"""System craftingu i upgrade'owania przedmiotów."""

import json
import copy
from utils.display import (print_separator, colored_text, print_success,
                           print_error, print_warning, press_enter)


class CraftingSystem:
    """Klasa zarządzająca craftingiem."""

    def __init__(self):
        """Inicjalizuje system craftingu."""
        self.recipes = self.load_recipes()
        self.materials_data = self.load_materials()

    def load_recipes(self):
        """Wczytuje przepisy z JSON."""
        try:
            with open('data/recipes.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print_error("Brak pliku recipes.json!")
            return {}

    def load_materials(self):
        """Wczytuje dane materiałów z JSON."""
        try:
            with open('data/materials.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print_error("Brak pliku materials.json!")
            return {}

    def show_crafting_menu(self, player):
        """
        Pokazuje menu craftingu.

        Args:
            player: Obiekt gracza
        """
        while True:
            print_separator("=")
            print(colored_text("🔨 STACJA CRAFTINGOWA 🔨", 'yellow'))
            print_separator("=")

            options = [
                "Stwórz przedmiot (Craft)",
                "Ulepsz przedmiot (Upgrade)",
                "Dodaj zaklęcie (Enchant)",
                "Rozłóż przedmiot (Dismantle)",
                "Zobacz przepisy",
                "Zobacz materiały",
                "Wyjdź"
            ]

            for i, option in enumerate(options, 1):
                print(f"  {i}. {option}")

            choice = input("\nWybór: ").strip()

            if choice == '1':
                self.craft_item_menu(player)
            elif choice == '2':
                self.upgrade_item_menu(player)
            elif choice == '3':
                self.enchant_item_menu(player)
            elif choice == '4':
                self.dismantle_item_menu(player)
            elif choice == '5':
                self.show_recipes()
            elif choice == '6':
                self.show_materials(player)
            elif choice == '7':
                break
            else:
                print_error("Nieprawidłowy wybór!")

    def craft_item_menu(self, player):
        """
        Menu craftowania nowych przedmiotów.

        Args:
            player: Obiekt gracza
        """
        print_separator("=")
        print("🔨 CRAFTOWANIE PRZEDMIOTÓW")
        print_separator("=")

        # Zbierz wszystkie przepisy typu craft
        craft_recipes = []

        for category, recipes in self.recipes.items():
            for recipe_id, recipe_data in recipes.items():
                if recipe_data.get('kategoria') == 'craft':
                    craft_recipes.append((recipe_id, recipe_data, category))

        if not craft_recipes:
            print_warning("Brak dostępnych przepisów!")
            press_enter()
            return

        # Wyświetl przepisy
        print("\nDostępne przepisy:")
        for i, (recipe_id, recipe_data, category) in enumerate(craft_recipes, 1):
            can_craft = self.can_craft(player, recipe_data)
            status = colored_text("✓", 'green') if can_craft else colored_text("✗", 'red')
            print(f"  {i}. {status} {recipe_data['nazwa']}")

        print(f"  0. Anuluj")

        try:
            choice = int(input("\nWybierz przepis (0 aby anulować): "))
            if choice == 0:
                return
            if 1 <= choice <= len(craft_recipes):
                recipe_id, recipe_data, category = craft_recipes[choice - 1]
                self.craft_item(player, recipe_data)
            else:
                print_error("Nieprawidłowy wybór!")
        except ValueError:
            print_error("Wprowadź poprawną liczbę!")

        press_enter()

    def can_craft(self, player, recipe):
        """
        Sprawdza czy gracz może skraftować przedmiot.

        Args:
            player: Obiekt gracza
            recipe: Dane przepisu

        Returns:
            bool: True jeśli może skraftować
        """
        # Sprawdź poziom
        if 'wymagany_poziom' in recipe and player.level < recipe['wymagany_poziom']:
            return False

        # Sprawdź złoto
        if player.gold < recipe.get('koszt_zlota', 0):
            return False

        # Sprawdź materiały
        materials = recipe.get('materialy', {})
        for material_id, required_amount in materials.items():
            if not self.has_material(player, material_id, required_amount):
                return False

        return True

    def has_material(self, player, material_id, amount):
        """
        Sprawdza czy gracz ma wystarczającą ilość materiału.

        Args:
            player: Obiekt gracza
            material_id: ID materiału
            amount: Wymagana ilość

        Returns:
            bool: True jeśli ma wystarczająco
        """
        # Materiały są trzymane w inventory jako items
        count = 0
        for item in player.inventory:
            if item.get('id') == material_id:
                count += item.get('stack', 1)

        return count >= amount

    def consume_materials(self, player, materials):
        """
        Konsumuje materiały z inventory gracza.

        Args:
            player: Obiekt gracza
            materials: Dict {material_id: amount}

        Returns:
            bool: True jeśli sukces
        """
        # Najpierw sprawdź czy ma wszystko
        for material_id, amount in materials.items():
            if not self.has_material(player, material_id, amount):
                return False

        # Konsumuj materiały
        for material_id, amount_needed in materials.items():
            remaining = amount_needed
            items_to_remove = []

            for item in player.inventory:
                if item.get('id') == material_id and remaining > 0:
                    stack = item.get('stack', 1)

                    if stack <= remaining:
                        # Usuń cały stack
                        items_to_remove.append(item)
                        remaining -= stack
                    else:
                        # Zmniejsz stack
                        item['stack'] = stack - remaining
                        remaining = 0
                        break

            # Usuń zużyte itemy
            for item in items_to_remove:
                player.inventory.remove(item)

        return True

    def craft_item(self, player, recipe):
        """
        Craftuje przedmiot.

        Args:
            player: Obiekt gracza
            recipe: Przepis
        """
        print_separator("-")
        print(f"📜 {recipe['nazwa']}")
        print(f"   {recipe['opis']}")
        print_separator("-")

        # Pokaż wymagania
        print("\nWymagane materiały:")
        materials = recipe.get('materialy', {})
        for material_id, amount in materials.items():
            material_name = self.get_material_name(material_id)
            has_amount = self.count_material(player, material_id)
            status = colored_text("✓", 'green') if has_amount >= amount else colored_text("✗", 'red')
            print(f"  {status} {material_name}: {has_amount}/{amount}")

        cost = recipe.get('koszt_zlota', 0)
        if cost > 0:
            status = colored_text("✓", 'green') if player.gold >= cost else colored_text("✗", 'red')
            print(f"\n{status} Koszt: {cost} złota (masz: {player.gold})")

        # Sprawdź czy może skraftować
        if not self.can_craft(player, recipe):
            print_error("\nNie masz wystarczających zasobów!")
            return

        # Potwierdź
        confirm = input("\nCzy chcesz skraftować ten przedmiot? (t/n): ").strip().lower()
        if confirm != 't':
            print_warning("Anulowano.")
            return

        # Konsumuj zasoby
        if not self.consume_materials(player, materials):
            print_error("Błąd przy konsumowaniu materiałów!")
            return

        player.gold -= cost

        # Dodaj przedmiot
        result = recipe.get('wynik', {})
        if 'id' in result:
            # Ładuj z items.json
            item = self.load_item_from_db(result['id'])
            if item:
                player.add_item(item)
                print_success(f"\n✓ Wytworzono: {item.get('nazwa', 'Przedmiot')}!")
        else:
            # Bezpośrednio z przepisu
            player.add_item(result)
            print_success(f"\n✓ Wytworzono: {result.get('nazwa', 'Przedmiot')}!")

    def load_item_from_db(self, item_id):
        """Ładuje przedmiot z bazy danych items.json."""
        try:
            with open('data/items.json', 'r', encoding='utf-8') as f:
                items_data = json.load(f)

            for category in items_data.values():
                if item_id in category:
                    return category[item_id].copy()

            return None
        except:
            return None

    def count_material(self, player, material_id):
        """Zlicza ilość materiału w inventory."""
        count = 0
        for item in player.inventory:
            if item.get('id') == material_id:
                count += item.get('stack', 1)
        return count

    def get_material_name(self, material_id):
        """Pobiera nazwę materiału."""
        for category in self.materials_data.values():
            if material_id in category:
                return category[material_id]['nazwa']
        return material_id

    def upgrade_item_menu(self, player):
        """Menu upgrade'owania przedmiotów."""
        print_separator("=")
        print("⬆️  ULEPSZANIE PRZEDMIOTÓW")
        print_separator("=")

        # Pokaż przedmioty które można ulepszyć
        upgradeable = []
        for item in player.inventory:
            if item.get('typ') in ['bron', 'zbroja']:
                upgradeable.append(item)

        if not upgradeable:
            print_warning("Nie masz przedmiotów do ulepszenia!")
            press_enter()
            return

        print("\nPrzedmioty do ulepszenia:")
        for i, item in enumerate(upgradeable, 1):
            current_level = item.get('poziom_upgrade', 0)
            print(f"  {i}. {item['nazwa']} (poziom: +{current_level})")

        print(f"  0. Anuluj")

        try:
            choice = int(input("\nWybierz przedmiot: "))
            if choice == 0:
                return
            if 1 <= choice <= len(upgradeable):
                item = upgradeable[choice - 1]
                self.upgrade_item(player, item)
            else:
                print_error("Nieprawidłowy wybór!")
        except ValueError:
            print_error("Wprowadź poprawną liczbę!")

        press_enter()

    def upgrade_item(self, player, item):
        """Ulepsza przedmiot."""
        current_level = item.get('poziom_upgrade', 0)

        if current_level >= 3:
            print_error("Ten przedmiot jest już maksymalnie ulepszony (+3)!")
            return

        # Znajdź odpowiedni przepis upgrade
        item_type = item['typ']
        recipe_key = f"{item_type}_plus_{current_level + 1}"

        recipe = None
        if item_type == 'bron':
            recipe = self.recipes.get('weapon_upgrades', {}).get(f"miecz_plus_{current_level + 1}")
        elif item_type == 'zbroja':
            recipe = self.recipes.get('armor_upgrades', {}).get(f"zbroja_plus_{current_level + 1}")

        if not recipe:
            print_error("Brak przepisu na upgrade tego przedmiotu!")
            return

        print_separator("-")
        print(f"⬆️  {recipe['nazwa']}")
        print(f"   {recipe['opis']}")
        print_separator("-")

        # Pokaż wymagania
        print("\nWymagane materiały:")
        materials = recipe.get('materialy', {})
        for material_id, amount in materials.items():
            material_name = self.get_material_name(material_id)
            has_amount = self.count_material(player, material_id)
            status = colored_text("✓", 'green') if has_amount >= amount else colored_text("✗", 'red')
            print(f"  {status} {material_name}: {has_amount}/{amount}")

        cost = recipe.get('koszt_zlota', 0)
        if cost > 0:
            status = colored_text("✓", 'green') if player.gold >= cost else colored_text("✗", 'red')
            print(f"\n{status} Koszt: {cost} złota (masz: {player.gold})")

        # Sprawdź czy może ulepszyć
        if not self.can_craft(player, recipe):
            print_error("\nNie masz wystarczających zasobów!")
            return

        # Potwierdź
        confirm = input("\nCzy chcesz ulepszyć ten przedmiot? (t/n): ").strip().lower()
        if confirm != 't':
            print_warning("Anulowano.")
            return

        # Konsumuj zasoby
        if not self.consume_materials(player, materials):
            print_error("Błąd przy konsumowaniu materiałów!")
            return

        player.gold -= cost

        # Ulepsz przedmiot
        efekt = recipe['efekt']
        item['poziom_upgrade'] = current_level + 1

        # Aplikuj bonusy
        if 'bonus_obrazen' in efekt:
            bonus = int(efekt['bonus_obrazen'])
            # Parsuj obecne obrażenia i dodaj bonus
            current_dmg = item.get('obrazenia', '1d6')
            # Prosta implementacja - dodaj +X do końca
            if '+' in current_dmg:
                base, old_bonus = current_dmg.split('+')
                item['obrazenia'] = f"{base}+{int(old_bonus) + bonus}"
            else:
                item['obrazenia'] = f"{current_dmg}+{bonus}"

        if 'bonus_ataku' in efekt:
            item['bonus_ataku'] = item.get('bonus_ataku', 0) + efekt['bonus_ataku']

        if 'bonus_klasy_pancerza' in efekt:
            item['klasa_pancerza'] = item.get('klasa_pancerza', 10) + efekt['bonus_klasy_pancerza']

        # Dodaj suffix do nazwy
        if 'suffix' in efekt:
            base_name = item['nazwa'].split('+')[0].strip()
            item['nazwa'] = f"{base_name} {efekt['suffix']}"

        # Zwiększ wartość
        item['wartosc'] = int(item.get('wartosc', 100) * 1.5)

        print_success(f"\n✓ Ulepszono przedmiot do {item['nazwa']}!")

    def enchant_item_menu(self, player):
        """Menu enchantowania."""
        print_separator("=")
        print("✨ ENCHANTING - DODAWANIE ZAKLĘĆ")
        print_separator("=")
        print_warning("Ta funkcja będzie dostępna wkrótce!")
        press_enter()

    def dismantle_item_menu(self, player):
        """Menu rozkładania przedmiotów na materiały."""
        print_separator("=")
        print("♻️  ROZK

ŁADANIE PRZEDMIOTÓW")
        print_separator("=")
        print_warning("Ta funkcja będzie dostępna wkrótce!")
        press_enter()

    def show_recipes(self):
        """Pokazuje wszystkie przepisy."""
        print_separator("=")
        print("📚 KSIĄŻKA PRZEPISÓW")
        print_separator("=")

        for category_name, recipes in self.recipes.items():
            category_display = {
                'weapon_upgrades': '⚔️  ULEPSZANIE BRONI',
                'armor_upgrades': '🛡️  ULEPSZANIE ZBROI',
                'potions': '🧪 MIKSTURY',
                'enchantments': '✨ ZAKLĘCIA',
                'special_items': '🌟 SPECJALNE PRZEDMIOTY'
            }

            print(f"\n{category_display.get(category_name, category_name.upper())}:")

            for recipe_id, recipe_data in recipes.items():
                print(f"  • {recipe_data['nazwa']}")
                print(f"    {recipe_data['opis']}")

        press_enter()

    def show_materials(self, player):
        """Pokazuje materiały w inventory gracza."""
        print_separator("=")
        print("📦 TWOJE MATERIAŁY")
        print_separator("=")

        materials_found = {}

        # Zbierz materiały z inventory
        for item in player.inventory:
            item_id = item.get('id', '')
            # Sprawdź czy to materiał
            for category in self.materials_data.values():
                if item_id in category:
                    count = item.get('stack', 1)
                    if item_id in materials_found:
                        materials_found[item_id] += count
                    else:
                        materials_found[item_id] = count

        if not materials_found:
            print_warning("Nie masz żadnych materiałów!")
        else:
            for material_id, count in sorted(materials_found.items()):
                name = self.get_material_name(material_id)
                print(f"  {name}: {count}")

        press_enter()
