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
            can_craft, reason = self.can_craft(player, recipe_data)
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
            tuple: (bool, str) - (czy może skraftować, powód jeśli nie może)
        """
        # Sprawdź poziom
        if 'min_level' in recipe and player.level < recipe['min_level']:
            return False, f"Wymagany poziom: {recipe['min_level']}"

        # Sprawdź złoto
        cost = recipe.get('koszt_zlota', 0)
        if player.gold < cost:
            return False, f"Brak złota (potrzeba: {cost}, masz: {player.gold})"

        # Sprawdź materiały
        materials = recipe.get('materialy', {})
        for material_id, required_amount in materials.items():
            if not self.has_material(player, material_id, required_amount):
                current = self.get_material_count(player, material_id)
                return False, f"Brak materiału: {material_id} (potrzeba: {required_amount}, masz: {current})"

        return True, "OK"

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
        return self.get_material_count(player, material_id) >= amount

    def get_material_count(self, player, material_id):
        """
        Zwraca ilość materiału w ekwipunku gracza.

        Args:
            player: Obiekt gracza
            material_id: ID materiału

        Returns:
            int: Ilość materiału
        """
        count = 0
        for item in player.inventory:
            if item.get('id') == material_id:
                count += item.get('quantity', item.get('stack', 1))
        return count

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
        can_craft, reason = self.can_craft(player, recipe)
        if not can_craft:
            print_error(f"\nNie możesz tego skraftować: {reason}")
            return False, reason

        # Potwierdź
        confirm = input("\nCzy chcesz skraftować ten przedmiot? (t/n): ").strip().lower()
        if confirm != 't':
            print_warning("Anulowano.")
            return False, "Anulowano"

        # Konsumuj zasoby
        if not self.consume_materials(player, materials):
            print_error("Błąd przy konsumowaniu materiałów!")
            return False, "Błąd przy konsumowaniu materiałów"

        player.gold -= cost

        # Dodaj przedmiot
        result = recipe.get('wynik', {})
        if 'id' in result:
            # Ładuj z items.json
            item = self.load_item_from_db(result['id'])
            if item:
                player.add_item(item)
                item_name = item.get('nazwa', 'Przedmiot')
                print_success(f"\n✓ Wytworzono: {item_name}!")
                return True, f"Wytworzono: {item_name}"
        else:
            # Bezpośrednio z przepisu
            player.add_item(result)
            item_name = result.get('nazwa', 'Przedmiot')
            print_success(f"\n✓ Wytworzono: {item_name}!")
            return True, f"Wytworzono: {item_name}"

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

    def upgrade_item(self, player, item, recipe=None):
        """Ulepsza przedmiot."""
        current_level = item.get('poziom_upgrade', item.get('upgrade_level', 0))

        if current_level >= 3:
            print_error("Ten przedmiot jest już maksymalnie ulepszony (+3)!")
            return False, "Przedmiot jest już maksymalnie ulepszony"

        # Znajdź odpowiedni przepis upgrade jeśli nie podano
        if not recipe:
            item_type = item['typ']
            recipe_key = f"{item_type}_plus_{current_level + 1}"

            if item_type == 'bron':
                recipe = self.recipes.get('weapon_upgrades', {}).get(f"miecz_plus_{current_level + 1}")
            elif item_type == 'zbroja':
                recipe = self.recipes.get('armor_upgrades', {}).get(f"zbroja_plus_{current_level + 1}")

        if not recipe:
            print_error("Brak przepisu na upgrade tego przedmiotu!")
            return False, "Brak przepisu na upgrade"

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
        can_craft, reason = self.can_craft(player, recipe)
        if not can_craft:
            print_error(f"\nNie możesz tego ulepszyć: {reason}")
            return False, reason

        # Sprawdź poziom progresywny
        target_level = recipe.get('poziom_upgrade', current_level + 1)
        if target_level > current_level + 1:
            return False, f"Musisz najpierw ulepszyć do +{current_level + 1}"

        # Potwierdź
        confirm = input("\nCzy chcesz ulepszyć ten przedmiot? (t/n): ").strip().lower()
        if confirm != 't':
            print_warning("Anulowano.")
            return False, "Anulowano"

        # Konsumuj zasoby
        if not self.consume_materials(player, materials):
            print_error("Błąd przy konsumowaniu materiałów!")
            return False, "Błąd przy konsumowaniu materiałów"

        player.gold -= cost

        # Ulepsz przedmiot
        efekt = recipe['efekt']
        item['poziom_upgrade'] = current_level + 1
        item['upgrade_level'] = current_level + 1  # Alternatywny klucz

        # Aplikuj bonusy
        if 'bonus_obrazen' in efekt:
            bonus_str = str(efekt['bonus_obrazen']).strip('+')
            bonus = int(bonus_str)
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

        item_name = item['nazwa']
        print_success(f"\n✓ Ulepszono przedmiot do {item_name}!")
        return True, f"Ulepszono przedmiot do {item_name}"

    def enchant_item_menu(self, player):
        """Menu enchantowania."""
        print_separator("=")
        print("✨ ENCHANTING - DODAWANIE ZAKLĘĆ")
        print_separator("=")

        # Wybierz przedmiot do enchantowania
        weapons = [item for item in player.inventory if item.get('typ') == 'bron']

        if not weapons:
            print_error("Nie masz żadnej broni do enchantowania!")
            press_enter()
            return

        print("\nWybierz broń do enchantowania:")
        for i, weapon in enumerate(weapons, 1):
            enchants = weapon.get('enchants', [])
            enchant_str = f" [{', '.join(enchants)}]" if enchants else ""
            print(f"  {i}. {weapon['nazwa']}{enchant_str}")

        print("  0. Anuluj")

        try:
            choice = int(input("\nWybór: "))
            if choice == 0:
                return
            if 1 <= choice <= len(weapons):
                selected_weapon = weapons[choice - 1]
                self.enchant_item(player, selected_weapon)
            else:
                print_error("Nieprawidłowy wybór!")
        except ValueError:
            print_error("Wprowadź poprawną liczbę!")

        press_enter()

    def enchant_item(self, player, item):
        """
        Enchantuje przedmiot magicznymi właściwościami.

        Args:
            player: Obiekt gracza
            item: Przedmiot do enchantowania

        Returns:
            tuple: (success, message)
        """
        # Sprawdź czy przedmiot może być enchantowany
        if item.get('typ') != 'bron':
            return False, "Możesz enchantować tylko broń!"

        # Sprawdź maksymalną liczbę enchantów (max 2)
        current_enchants = item.get('enchants', [])
        if len(current_enchants) >= 2:
            return False, "Ta broń ma już maksymalną liczbę zaklęć (2)!"

        # Wyświetl dostępne enchanty
        print_separator("-")
        print(f"🔮 Enchantowanie: {item['nazwa']}")
        print_separator("-")

        # Filtruj enchanty których jeszcze nie ma
        available_enchants = []
        for enchant_id, recipe in self.recipes.get('enchantments', {}).items():
            if recipe.get('efekt', {}).get('enchant') not in current_enchants:
                available_enchants.append((enchant_id, recipe))

        if not available_enchants:
            print_error("Brak dostępnych zaklęć dla tej broni!")
            return False, "Brak dostępnych zaklęć"

        print("\nDostępne zaklęcia:")
        for i, (enchant_id, recipe) in enumerate(available_enchants, 1):
            can_craft, reason = self.can_craft(player, recipe)
            status = colored_text("✓", 'green') if can_craft else colored_text("✗", 'red')
            print(f"  {i}. {status} {recipe['nazwa']}")
            print(f"     {recipe['opis']}")
            print(f"     Koszt: {recipe['koszt_zlota']} złota")

        print("  0. Anuluj")

        try:
            choice = int(input("\nWybierz zaklęcie (0 aby anulować): "))
            if choice == 0:
                return False, "Anulowano"
            if 1 <= choice <= len(available_enchants):
                enchant_id, recipe = available_enchants[choice - 1]

                # Sprawdź wymagania
                can_craft, reason = self.can_craft(player, recipe)
                if not can_craft:
                    print_error(f"\nNie możesz dodać tego zaklęcia: {reason}")
                    return False, reason

                # Pokaż szczegóły
                print_separator("-")
                print(f"✨ {recipe['nazwa']}")
                print(f"   {recipe['opis']}")
                print_separator("-")

                # Wyświetl materiały
                materials = recipe.get('materialy', {})
                print("\nWymagane materiały:")
                for mat_id, amount in materials.items():
                    mat_name = self.get_material_name(mat_id)
                    has_amount = self.get_material_count(player, mat_id)
                    status = colored_text("✓", 'green') if has_amount >= amount else colored_text("✗", 'red')
                    print(f"  {status} {mat_name}: {has_amount}/{amount}")

                cost = recipe.get('koszt_zlota', 0)
                if cost > 0:
                    status = colored_text("✓", 'green') if player.gold >= cost else colored_text("✗", 'red')
                    print(f"\n{status} Koszt: {cost} złota (masz: {player.gold})")

                # Potwierdź
                confirm = input("\nCzy chcesz dodać to zaklęcie? (t/n): ").strip().lower()
                if confirm != 't':
                    print_warning("Anulowano.")
                    return False, "Anulowano"

                # Konsumuj zasoby
                if not self.consume_materials(player, materials):
                    print_error("Błąd przy konsumowaniu materiałów!")
                    return False, "Błąd konsumpcji materiałów"

                player.gold -= cost

                # Aplikuj enchant
                efekt = recipe['efekt']
                enchant_type = efekt.get('enchant')

                # Dodaj enchant do listy
                if 'enchants' not in item:
                    item['enchants'] = []
                item['enchants'].append(enchant_type)

                # Aplikuj efekty
                if 'bonus_obrazen_element' in efekt:
                    if 'obrazenia_dodatkowe' not in item:
                        item['obrazenia_dodatkowe'] = []
                    item['obrazenia_dodatkowe'].append(efekt['bonus_obrazen_element'])

                if 'bonus_ataku' in efekt:
                    item['bonus_ataku'] = item.get('bonus_ataku', 0) + efekt['bonus_ataku']

                if 'efekt_specjalny' in efekt:
                    if 'efekty_specjalne' not in item:
                        item['efekty_specjalne'] = []
                    item['efekty_specjalne'].append(efekt['efekt_specjalny'])

                # Dodaj prefix do nazwy
                if 'prefix' in efekt:
                    base_name = item['nazwa']
                    # Usuń poprzednie prefixy jeśli są
                    for old_prefix in ['Płonący', 'Lodowy', 'Błyskawiczny', 'Wampiryczny', 'Święty', 'Ciemny']:
                        if base_name.startswith(old_prefix):
                            base_name = base_name[len(old_prefix):].strip()
                    item['nazwa'] = f"{efekt['prefix']} {base_name}"

                # Zwiększ wartość
                item['wartosc'] = int(item.get('wartosc', 100) * 1.8)

                item_name = item['nazwa']
                print_success(f"\n✨ Dodano zaklęcie do: {item_name}!")
                return True, f"Dodano zaklęcie do: {item_name}"

            else:
                print_error("Nieprawidłowy wybór!")
                return False, "Nieprawidłowy wybór"
        except ValueError:
            print_error("Wprowadź poprawną liczbę!")
            return False, "Błędne dane"

    def dismantle_item_menu(self, player):
        """Menu rozkładania przedmiotów na materiały."""
        print_separator("=")
        print("♻️  ROZKŁADANIE PRZEDMIOTÓW")
        print_separator("=")

        # Wybierz przedmiot do rozkładania
        dismantlable_items = []
        for item in player.inventory:
            # Można rozkładać broń, zbroję i mikstury (ale nie podstawowe materiały)
            if item.get('typ') in ['bron', 'zbroja'] or item.get('kategoria') == 'mikstura':
                dismantlable_items.append(item)

        if not dismantlable_items:
            print_error("Nie masz żadnych przedmiotów do rozkładania!")
            press_enter()
            return

        print("\nWybierz przedmiot do rozkładania:")
        print(colored_text("⚠ Uwaga: Odzyskasz ~50% wartości materiałów!", 'yellow'))
        print()

        for i, item in enumerate(dismantlable_items, 1):
            value = item.get('wartosc', 0)
            print(f"  {i}. {item['nazwa']} (wartość: {value} złota)")

        print("  0. Anuluj")

        try:
            choice = int(input("\nWybór: "))
            if choice == 0:
                return
            if 1 <= choice <= len(dismantlable_items):
                selected_item = dismantlable_items[choice - 1]
                self.dismantle_item(player, selected_item)
            else:
                print_error("Nieprawidłowy wybór!")
        except ValueError:
            print_error("Wprowadź poprawną liczbę!")

        press_enter()

    def dismantle_item(self, player, item):
        """
        Rozkłada przedmiot na materiały (50% zwrotu).

        Args:
            player: Obiekt gracza
            item: Przedmiot do rozkładania

        Returns:
            tuple: (success, message)
        """
        print_separator("-")
        print(f"♻️  Rozkładanie: {item['nazwa']}")
        print_separator("-")

        # Oblicz co można odzyskać
        recovered_materials = {}
        recovered_gold = int(item.get('wartosc', 0) * 0.3)  # 30% wartości jako złoto

        # Bazowe materiały w zależności od typu
        item_type = item.get('typ', '')

        if item_type == 'bron':
            # Broń zwraca metale i kamienie
            recovered_materials['stal'] = 2
            recovered_materials['kamien_ostrzacy'] = 1

            # Jeśli upgraded, zwróć więcej
            upgrade_level = item.get('poziom_upgrade', item.get('upgrade_level', 0))
            if upgrade_level > 0:
                recovered_materials['stal'] += upgrade_level * 2
                if upgrade_level >= 2:
                    recovered_materials['starozytny_metal'] = 1
                if upgrade_level >= 3:
                    recovered_materials['mithryl'] = 1

            # Jeśli enchanted, zwróć materiały magiczne
            if item.get('enchants'):
                recovered_materials['krysztaly_many'] = len(item['enchants']) * 2
                recovered_materials['magiczna_runa'] = len(item['enchants'])

        elif item_type == 'zbroja':
            # Zbroja zwraca skórę i metal
            recovered_materials['skora'] = 3
            recovered_materials['stal'] = 1

            upgrade_level = item.get('poziom_upgrade', item.get('upgrade_level', 0))
            if upgrade_level > 0:
                recovered_materials['skora'] += upgrade_level * 2
                recovered_materials['stal'] += upgrade_level

        elif item.get('kategoria') == 'mikstura':
            # Mikstury zwracają zioła
            recovered_materials['ziola_leczace'] = 1
            recovered_materials['woda'] = 1

        # Pokaż co zostanie odzyskane
        print("\nOdzyskane materiały:")
        if recovered_materials:
            for mat_id, amount in recovered_materials.items():
                mat_name = self.get_material_name(mat_id)
                print(f"  • {mat_name} x{amount}")
        if recovered_gold > 0:
            print(f"  • {recovered_gold} złota")

        if not recovered_materials and recovered_gold == 0:
            print_warning("  Brak materiałów do odzyskania z tego przedmiotu.")
            return False, "Brak materiałów do odzyskania"

        # Potwierdź
        confirm = input("\n⚠ Czy na pewno chcesz rozłożyć ten przedmiot? (t/n): ").strip().lower()
        if confirm != 't':
            print_warning("Anulowano.")
            return False, "Anulowano"

        # Usuń przedmiot
        if item in player.inventory:
            player.inventory.remove(item)

        # Dodaj materiały
        for mat_id, amount in recovered_materials.items():
            self.add_materials_to_player(player, {mat_id: amount})

        # Dodaj złoto
        player.gold += recovered_gold

        print_success(f"\n✓ Rozłożono {item['nazwa']}!")
        return True, f"Rozłożono {item['nazwa']}"

    def add_materials_to_player(self, player, materials_dict):
        """
        Dodaje materiały do ekwipunku gracza.

        Args:
            player: Postać gracza
            materials_dict: Dict {material_id: quantity}
        """
        for mat_id, quantity in materials_dict.items():
            # Znajdź materiał w danych
            material = None
            for category in self.materials_data.values():
                if mat_id in category:
                    material = category[mat_id].copy()
                    material['id'] = mat_id
                    material['typ'] = 'material'
                    material['quantity'] = quantity
                    break

            if material:
                player.add_item(material)

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
