#!/usr/bin/env python3
"""
Kompleksowy system testowy dla systemu craftingu.
Testuje wszystkie aspekty: crafting, upgrade, materiały, balans.
"""

import json
import sys
import copy
from engine.crafting import CraftingSystem
from engine.character import Character


class CraftingTester:
    """Klasa do testowania systemu craftingu."""

    def __init__(self):
        """Inicjalizacja testera."""
        self.crafting = CraftingSystem()
        self.test_results = []
        self.passed = 0
        self.failed = 0

    def log_test(self, test_name, passed, details=""):
        """Loguje wynik testu."""
        status = "✓ PASS" if passed else "✗ FAIL"
        result = {
            'name': test_name,
            'passed': passed,
            'details': details
        }
        self.test_results.append(result)

        if passed:
            self.passed += 1
            print(f"  {status} - {test_name}")
        else:
            self.failed += 1
            print(f"  {status} - {test_name}")
            if details:
                print(f"       Szczegóły: {details}")

    def create_test_character(self, level=1, gold=1000):
        """Tworzy testową postać."""
        with open('data/classes.json', 'r', encoding='utf-8') as f:
            classes_data = json.load(f)

        class_data = classes_data['classes']['wojownik']

        # Utwórz postać z podstawowymi atrybutami
        player = Character.__new__(Character)
        player.name = "TestWarrior"
        player.character_class = "wojownik"
        player.class_data = class_data
        player.level = level
        player.gold = gold

        # Ustaw atrybuty
        player.attributes = {
            'sila': 16,
            'zrecznosc': 12,
            'kondycja': 14,
            'inteligencja': 10,
            'madrosc': 10,
            'charyzma': 10
        }

        # Inicjalizuj pozostałe pola
        player.max_hp = 20 + (level - 1) * 10
        player.hp = player.max_hp
        player.max_mana = 0
        player.mana = 0
        player.xp = 0
        player.inventory = []
        player.equipped = {}
        player.current_location = "startowa_wioska"

        # Talent system
        player.talent_points = 0
        player.learned_talents = []
        player.talent_cooldowns = {}
        player.talent_buffs = {}

        # Quest system
        player.active_quests = []
        player.completed_quests = []

        return player

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
            for category in self.crafting.materials_data.values():
                if mat_id in category:
                    material = category[mat_id].copy()
                    material['id'] = mat_id
                    material['typ'] = 'material'
                    material['quantity'] = quantity
                    break

            if material:
                player.add_item(material)

    def test_initialization(self):
        """Test 1: Inicjalizacja systemu."""
        print("\n=== TEST 1: INICJALIZACJA SYSTEMU ===")

        # Test czy system się inicjalizuje
        try:
            crafting = CraftingSystem()
            self.log_test("Inicjalizacja CraftingSystem", True)
        except Exception as e:
            self.log_test("Inicjalizacja CraftingSystem", False, str(e))
            return

        # Test czy przepisy się ładują
        has_recipes = len(crafting.recipes) > 0
        self.log_test(
            "Ładowanie przepisów",
            has_recipes,
            f"Załadowano {len(crafting.recipes)} kategorii przepisów"
        )

        # Test czy materiały się ładują
        has_materials = len(crafting.materials_data) > 0
        self.log_test(
            "Ładowanie materiałów",
            has_materials,
            f"Załadowano {len(crafting.materials_data)} kategorii materiałów"
        )

        # Test kategorie przepisów
        expected_categories = ['weapon_upgrades', 'armor_upgrades', 'potions', 'enchantments', 'special_items']
        all_categories_present = all(cat in crafting.recipes for cat in expected_categories)
        self.log_test(
            "Wszystkie kategorie przepisów obecne",
            all_categories_present,
            f"Kategorie: {list(crafting.recipes.keys())}"
        )

    def test_materials_loading(self):
        """Test 2: Ładowanie i struktura materiałów."""
        print("\n=== TEST 2: MATERIAŁY ===")

        # Test podstawowych materiałów
        basic_materials = ['skora', 'kly', 'kosci', 'stal', 'krysztaly_many']

        for mat_id in basic_materials:
            found = False
            for category in self.crafting.materials_data.values():
                if mat_id in category:
                    material = category[mat_id]
                    # Sprawdź strukturę
                    has_required_fields = all(
                        field in material
                        for field in ['nazwa', 'opis', 'rzadkosc', 'value']
                    )
                    self.log_test(
                        f"Materiał '{mat_id}' ma poprawną strukturę",
                        has_required_fields,
                        f"Nazwa: {material.get('nazwa', 'N/A')}"
                    )
                    found = True
                    break

            if not found:
                self.log_test(f"Materiał '{mat_id}' istnieje", False, "Nie znaleziono")

    def test_recipe_structure(self):
        """Test 3: Struktura przepisów."""
        print("\n=== TEST 3: STRUKTURA PRZEPISÓW ===")

        # Test kilku przykładowych przepisów
        recipes_to_test = [
            ('weapon_upgrades', 'miecz_plus_1'),
            ('armor_upgrades', 'zbroja_plus_1'),
            ('potions', 'mikstura_leczenia_mala'),
        ]

        for category, recipe_id in recipes_to_test:
            if category in self.crafting.recipes and recipe_id in self.crafting.recipes[category]:
                recipe = self.crafting.recipes[category][recipe_id]

                # Sprawdź wymagane pola
                required_fields = ['nazwa', 'materialy', 'koszt_zlota']
                has_fields = all(field in recipe for field in required_fields)

                self.log_test(
                    f"Przepis '{recipe_id}' ma wymagane pola",
                    has_fields,
                    f"Nazwa: {recipe.get('nazwa', 'N/A')}"
                )

                # Sprawdź czy materiały są niepuste
                has_materials = len(recipe.get('materialy', {})) > 0
                self.log_test(
                    f"Przepis '{recipe_id}' ma materiały",
                    has_materials,
                    f"Materiały: {list(recipe.get('materialy', {}).keys())}"
                )
            else:
                self.log_test(f"Przepis '{recipe_id}' istnieje", False, "Nie znaleziono")

    def test_basic_crafting(self):
        """Test 4: Podstawowy crafting."""
        print("\n=== TEST 4: PODSTAWOWY CRAFTING ===")

        # Stwórz testowego gracza
        player = self.create_test_character(level=5, gold=500)

        # Dodaj materiały na małą miksturę leczenia
        # Wymaga: ziola_leczace: 3, woda: 1
        self.add_materials_to_player(player, {
            'ziola_leczace': 5,
            'woda': 3
        })

        initial_gold = player.gold

        # Znajdź przepis
        if 'potions' in self.crafting.recipes and 'mikstura_leczenia_mala' in self.crafting.recipes['potions']:
            recipe = self.crafting.recipes['potions']['mikstura_leczenia_mala']

            # Test can_craft
            can_craft, reason = self.crafting.can_craft(player, recipe)
            self.log_test(
                "can_craft() zwraca True dla spełnionych wymagań",
                can_craft,
                reason if not can_craft else "Wszystkie wymagania spełnione"
            )

            if can_craft:
                # Policz mikstury przed craftingiem
                potions_before = sum(1 for item in player.inventory if 'mikstura' in item.get('nazwa', '').lower())

                # Wykonaj crafting
                success, message = self.crafting.craft_item(player, recipe)

                self.log_test(
                    "craft_item() zwraca sukces",
                    success,
                    message
                )

                # Sprawdź czy złoto zostało odjęte
                gold_spent = initial_gold - player.gold
                expected_cost = recipe['koszt_zlota']
                self.log_test(
                    "Złoto zostało poprawnie odjęte",
                    gold_spent == expected_cost,
                    f"Wydano: {gold_spent}, Oczekiwano: {expected_cost}"
                )

                # Sprawdź czy mikstura została dodana
                potions_after = sum(1 for item in player.inventory if 'mikstura' in item.get('nazwa', '').lower())
                self.log_test(
                    "Mikstura została dodana do ekwipunku",
                    potions_after > potions_before,
                    f"Mikstury przed: {potions_before}, po: {potions_after}"
                )

    def test_insufficient_materials(self):
        """Test 5: Crafting bez wystarczających materiałów."""
        print("\n=== TEST 5: BRAK MATERIAŁÓW ===")

        player = self.create_test_character(level=5, gold=1000)

        # Nie dodajemy żadnych materiałów

        if 'potions' in self.crafting.recipes and 'mikstura_leczenia_mala' in self.crafting.recipes['potions']:
            recipe = self.crafting.recipes['potions']['mikstura_leczenia_mala']

            can_craft, reason = self.crafting.can_craft(player, recipe)

            self.log_test(
                "can_craft() zwraca False przy braku materiałów",
                not can_craft,
                reason
            )

            # Próba craftingu powinna się nie udać
            success, message = self.crafting.craft_item(player, recipe)

            self.log_test(
                "craft_item() zwraca niepowodzenie",
                not success,
                message
            )

    def test_insufficient_gold(self):
        """Test 6: Crafting bez wystarczającego złota."""
        print("\n=== TEST 6: BRAK ZŁOTA ===")

        player = self.create_test_character(level=5, gold=10)  # Tylko 10 złota

        # Dodaj materiały
        self.add_materials_to_player(player, {
            'ziola_leczace': 5,
            'woda': 3
        })

        if 'potions' in self.crafting.recipes and 'mikstura_leczenia_mala' in self.crafting.recipes['potions']:
            recipe = self.crafting.recipes['potions']['mikstura_leczenia_mala']

            # Jeśli koszt jest większy niż 10
            if recipe['koszt_zlota'] > 10:
                can_craft, reason = self.crafting.can_craft(player, recipe)

                self.log_test(
                    "can_craft() zwraca False przy braku złota",
                    not can_craft,
                    reason
                )

    def test_level_requirement(self):
        """Test 7: Wymaganie poziomu."""
        print("\n=== TEST 7: WYMAGANIE POZIOMU ===")

        player = self.create_test_character(level=1, gold=1000)

        # Znajdź przepis z wymaganiem poziomu
        recipe_with_level = None
        for category in self.crafting.recipes.values():
            for recipe in category.values():
                if 'min_level' in recipe and recipe['min_level'] > 1:
                    recipe_with_level = recipe
                    break
            if recipe_with_level:
                break

        if recipe_with_level:
            # Dodaj wszystkie wymagane materiały
            materials_needed = recipe_with_level['materialy']
            materials_dict = {mat: qty * 2 for mat, qty in materials_needed.items()}
            self.add_materials_to_player(player, materials_dict)

            can_craft, reason = self.crafting.can_craft(player, recipe_with_level)

            self.log_test(
                "can_craft() sprawdza wymaganie poziomu",
                not can_craft or player.level >= recipe_with_level['min_level'],
                reason if not can_craft else f"Poziom: {player.level}"
            )
        else:
            self.log_test(
                "Znaleziono przepis z wymaganiem poziomu",
                False,
                "Brak przepisu do testowania"
            )

    def test_upgrade_system(self):
        """Test 8: System upgrade'ów."""
        print("\n=== TEST 8: SYSTEM UPGRADE'ÓW ===")

        player = self.create_test_character(level=10, gold=5000)

        # Dodaj podstawowy miecz
        with open('data/items.json', 'r', encoding='utf-8') as f:
            items_data = json.load(f)

        if 'bron' in items_data and 'miecz_dlugi' in items_data['bron']:
            base_sword = items_data['bron']['miecz_dlugi'].copy()
            base_sword['id'] = 'miecz_dlugi'
            base_sword['typ'] = 'bron'
            player.add_item(base_sword)

            # Test upgrade +1
            if 'weapon_upgrades' in self.crafting.recipes and 'miecz_plus_1' in self.crafting.recipes['weapon_upgrades']:
                recipe_plus_1 = self.crafting.recipes['weapon_upgrades']['miecz_plus_1']

                # Dodaj materiały
                materials_needed = recipe_plus_1['materialy']
                materials_dict = {mat: qty * 3 for mat, qty in materials_needed.items()}
                self.add_materials_to_player(player, materials_dict)

                # Zapisz obrażenia przed upgrade (bo upgrade modyfikuje obiekt in-place)
                base_damage_before = base_sword.get('obrazenia', '1d6')

                # Upgrade do +1
                success, message = self.crafting.upgrade_item(player, base_sword, recipe_plus_1)

                self.log_test(
                    "Upgrade do +1 się udaje",
                    success,
                    message
                )

                if success:
                    # Sprawdź czy nazwa się zmieniła
                    upgraded_sword = None
                    for item in player.inventory:
                        if item.get('id') == 'miecz_dlugi' and '+1' in item.get('nazwa', ''):
                            upgraded_sword = item
                            break

                    self.log_test(
                        "Nazwa miecza zawiera '+1'",
                        upgraded_sword is not None,
                        upgraded_sword.get('nazwa', 'N/A') if upgraded_sword else "Nie znaleziono"
                    )

                    if upgraded_sword:
                        # Sprawdź czy bonus został dodany
                        upgraded_damage = upgraded_sword.get('obrazenia', '1d6')

                        # Sprawdź czy upgrade dodał bonus (szukamy '+' w stringu)
                        has_bonus = '+' in upgraded_damage
                        damage_changed = upgraded_damage != base_damage_before

                        self.log_test(
                            "Obrażenia zwiększyły się (dodano bonus)",
                            has_bonus and damage_changed,
                            f"Przed: {base_damage_before}, Po: {upgraded_damage}"
                        )

    def test_progressive_upgrade(self):
        """Test 9: Progresywny upgrade (+1, +2, +3)."""
        print("\n=== TEST 9: PROGRESYWNY UPGRADE ===")

        player = self.create_test_character(level=15, gold=10000)

        # Dodaj miecz +1
        with open('data/items.json', 'r', encoding='utf-8') as f:
            items_data = json.load(f)

        if 'bron' in items_data and 'miecz_dlugi' in items_data['bron']:
            sword_plus_1 = items_data['bron']['miecz_dlugi'].copy()
            sword_plus_1['id'] = 'miecz_dlugi'
            sword_plus_1['typ'] = 'bron'
            sword_plus_1['nazwa'] = 'Miecz Długi +1'
            sword_plus_1['upgrade_level'] = 1
            player.add_item(sword_plus_1)

            # Dodaj dużo materiałów
            all_materials = {}
            for category in self.crafting.materials_data.values():
                for mat_id in category.keys():
                    all_materials[mat_id] = 50
            self.add_materials_to_player(player, all_materials)

            # Test upgrade +2 (wymaga +1)
            if 'weapon_upgrades' in self.crafting.recipes and 'miecz_plus_2' in self.crafting.recipes['weapon_upgrades']:
                recipe_plus_2 = self.crafting.recipes['weapon_upgrades']['miecz_plus_2']

                success, message = self.crafting.upgrade_item(player, sword_plus_1, recipe_plus_2)

                self.log_test(
                    "Upgrade +1 -> +2 się udaje",
                    success,
                    message
                )

            # Test próby upgrade +3 bez +2
            sword_without_plus_2 = items_data['bron']['miecz_dlugi'].copy()
            sword_without_plus_2['id'] = 'miecz_dlugi'
            sword_without_plus_2['typ'] = 'bron'
            sword_without_plus_2['upgrade_level'] = 0

            if 'weapon_upgrades' in self.crafting.recipes and 'miecz_plus_3' in self.crafting.recipes['weapon_upgrades']:
                recipe_plus_3 = self.crafting.recipes['weapon_upgrades']['miecz_plus_3']

                success, message = self.crafting.upgrade_item(player, sword_without_plus_2, recipe_plus_3)

                self.log_test(
                    "Upgrade +0 -> +3 bez +2 się nie udaje",
                    not success,
                    message
                )

    def test_material_consumption(self):
        """Test 10: Konsumpcja materiałów."""
        print("\n=== TEST 10: KONSUMPCJA MATERIAŁÓW ===")

        player = self.create_test_character(level=5, gold=1000)

        # Dodaj dokładną ilość materiałów
        self.add_materials_to_player(player, {
            'ziola_leczace': 3,
            'woda': 1
        })

        initial_herb_count = sum(
            item.get('quantity', 1)
            for item in player.inventory
            if item.get('id') == 'ziola_leczace'
        )

        if 'potions' in self.crafting.recipes and 'mikstura_leczenia_mala' in self.crafting.recipes['potions']:
            recipe = self.crafting.recipes['potions']['mikstura_leczenia_mala']

            # Craft
            success, message = self.crafting.craft_item(player, recipe)

            if success:
                # Sprawdź czy materiały zostały zużyte
                final_herb_count = sum(
                    item.get('quantity', 1)
                    for item in player.inventory
                    if item.get('id') == 'ziola_leczace'
                )

                herbs_used = initial_herb_count - final_herb_count
                expected_herbs = recipe['materialy'].get('ziola_leczace', 0)

                self.log_test(
                    "Materiały zostały poprawnie zużyte",
                    herbs_used == expected_herbs,
                    f"Zużyto: {herbs_used}, Oczekiwano: {expected_herbs}"
                )

    def test_material_stacking(self):
        """Test 11: Stackowanie materiałów."""
        print("\n=== TEST 11: STACKOWANIE MATERIAŁÓW ===")

        player = self.create_test_character(level=1, gold=0)

        # Dodaj ten sam materiał wielokrotnie
        self.add_materials_to_player(player, {'skora': 10})
        self.add_materials_to_player(player, {'skora': 5})

        # Sprawdź czy materiały się stackują
        skora_items = [item for item in player.inventory if item.get('id') == 'skora']

        total_skora = sum(item.get('quantity', 1) for item in skora_items)

        self.log_test(
            "Materiały się stackują",
            total_skora == 15,
            f"Łączna ilość skóry: {total_skora}"
        )

        # Sprawdź czy jest tylko jeden stack (jeśli system stackuje)
        # Lub wiele stacków (jeśli nie)
        num_stacks = len(skora_items)
        self.log_test(
            "Liczba stacków skóry",
            num_stacks > 0,
            f"Stacków: {num_stacks}, Łączna ilość: {total_skora}"
        )

    def test_recipe_balance(self):
        """Test 12: Balans przepisów."""
        print("\n=== TEST 12: BALANS PRZEPISÓW ===")

        # Sprawdź czy koszty są rozsądne
        unbalanced_recipes = []

        for category_name, category_recipes in self.crafting.recipes.items():
            for recipe_id, recipe in category_recipes.items():
                cost = recipe.get('koszt_zlota', 0)

                # Sprawdź czy koszt nie jest zbyt wysoki/niski
                if cost < 0:
                    unbalanced_recipes.append(f"{recipe_id}: ujemny koszt ({cost})")
                elif cost > 10000:
                    unbalanced_recipes.append(f"{recipe_id}: bardzo wysoki koszt ({cost})")

        self.log_test(
            "Wszystkie przepisy mają rozsądne koszty",
            len(unbalanced_recipes) == 0,
            f"Problematyczne: {unbalanced_recipes}" if unbalanced_recipes else "Wszystkie OK"
        )

        # Sprawdź progresję upgrade'ów
        weapon_upgrades = self.crafting.recipes.get('weapon_upgrades', {})

        costs = {}
        for recipe_id, recipe in weapon_upgrades.items():
            if 'plus' in recipe_id:
                level = 1 if 'plus_1' in recipe_id else (2 if 'plus_2' in recipe_id else 3)
                costs[level] = recipe.get('koszt_zlota', 0)

        # Sprawdź czy koszt rośnie z poziomem
        if len(costs) >= 2:
            cost_increases = all(
                costs.get(i, 0) < costs.get(i+1, float('inf'))
                for i in range(1, max(costs.keys()))
            )

            self.log_test(
                "Koszty upgrade'ów rosną progresywnie",
                cost_increases,
                f"Koszty: +1={costs.get(1)}, +2={costs.get(2)}, +3={costs.get(3)}"
            )

    def test_material_droprates(self):
        """Test 13: Drop rate materiałów z potworów."""
        print("\n=== TEST 13: DROP RATE MATERIAŁÓW ===")

        with open('data/monsters.json', 'r', encoding='utf-8') as f:
            monsters_data = json.load(f)

        monsters_without_materials = []

        for monster_id, monster in monsters_data['potwory'].items():
            loot = monster.get('lup', [])

            # Sprawdź czy ma jakieś materiały (nie tylko złoto)
            has_materials = any(
                not item.startswith('zloto:')
                for item in loot
            )

            if not has_materials:
                monsters_without_materials.append(monster.get('nazwa', monster_id))

        self.log_test(
            "Wszystkie potwory dropują materiały",
            len(monsters_without_materials) == 0,
            f"Bez materiałów: {monsters_without_materials}" if monsters_without_materials else "Wszystkie OK"
        )

        # Sprawdź czy boss'y mają rzadkie materiały
        bosses = [m for m in monsters_data['potwory'].values() if m.get('boss', False)]

        bosses_with_rare = 0
        for boss in bosses:
            loot = boss.get('lup', [])
            # Sprawdź czy ma mithryl lub inne rzadkie
            has_rare = any('mithryl' in item or 'smocza' in item for item in loot)
            if has_rare:
                bosses_with_rare += 1

        if len(bosses) > 0:
            self.log_test(
                "Boss'y dropują rzadkie materiały",
                bosses_with_rare > 0,
                f"{bosses_with_rare}/{len(bosses)} bossów ma rzadkie materiały"
            )

    def test_integration_with_world(self):
        """Test 14: Integracja z systemem świata."""
        print("\n=== TEST 14: INTEGRACJA Z WORLD.PY ===")

        try:
            from engine.world import World
            world = World()

            # Sprawdź czy World ma crafting system
            has_crafting = hasattr(world, 'crafting')
            self.log_test(
                "World ma atrybut 'crafting'",
                has_crafting,
                "CraftingSystem zainicjalizowany w World"
            )

            # Sprawdź czy kuźnia ma crafting_station
            if 'startowa_wioska' in world.locations:
                wioska = world.locations['startowa_wioska']
                if 'miejsca' in wioska and 'kuznia' in wioska['miejsca']:
                    kuznia = wioska['miejsca']['kuznia']
                    has_station = kuznia.get('crafting_station', False)

                    self.log_test(
                        "Kuźnia ma flagę crafting_station",
                        has_station,
                        "Gracz może używać stacji craftingowej"
                    )
                else:
                    self.log_test("Kuźnia istnieje w wiosce", False, "Nie znaleziono")
            else:
                self.log_test("Lokacja 'startowa_wioska' istnieje", False, "Nie znaleziono")

        except ImportError as e:
            self.log_test("Import World", False, str(e))

    def run_all_tests(self):
        """Uruchamia wszystkie testy."""
        print("=" * 60)
        print("KOMPLEKSOWY TEST SYSTEMU CRAFTINGU")
        print("=" * 60)

        self.test_initialization()
        self.test_materials_loading()
        self.test_recipe_structure()
        self.test_basic_crafting()
        self.test_insufficient_materials()
        self.test_insufficient_gold()
        self.test_level_requirement()
        self.test_upgrade_system()
        self.test_progressive_upgrade()
        self.test_material_consumption()
        self.test_material_stacking()
        self.test_recipe_balance()
        self.test_material_droprates()
        self.test_integration_with_world()

        # Podsumowanie
        print("\n" + "=" * 60)
        print("PODSUMOWANIE TESTÓW")
        print("=" * 60)

        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\nWykonano testów: {total}")
        print(f"✓ Zaliczone: {self.passed}")
        print(f"✗ Niezaliczone: {self.failed}")
        print(f"Wskaźnik sukcesu: {success_rate:.1f}%")

        if self.failed > 0:
            print("\n⚠ UWAGA: Niektóre testy nie przeszły!")
            print("Szczegóły nieudanych testów:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['name']}: {result['details']}")
        else:
            print("\n🎉 Wszystkie testy przeszły pomyślnie!")

        return success_rate

    def generate_report(self):
        """Generuje szczegółowy raport z testów."""
        report_path = "RAPORT_TESTOW_CRAFTING.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# RAPORT Z TESTÓW SYSTEMU CRAFTINGU\n\n")
            f.write(f"Data: {self.get_timestamp()}\n\n")

            total = self.passed + self.failed
            success_rate = (self.passed / total * 100) if total > 0 else 0

            f.write("## PODSUMOWANIE\n\n")
            f.write(f"- **Wykonano testów**: {total}\n")
            f.write(f"- **✓ Zaliczone**: {self.passed}\n")
            f.write(f"- **✗ Niezaliczone**: {self.failed}\n")
            f.write(f"- **Wskaźnik sukcesu**: {success_rate:.1f}%\n\n")

            f.write("## SZCZEGÓŁOWE WYNIKI\n\n")

            for i, result in enumerate(self.test_results, 1):
                status = "✅ PASS" if result['passed'] else "❌ FAIL"
                f.write(f"### {i}. {result['name']} - {status}\n\n")
                if result['details']:
                    f.write(f"**Szczegóły**: {result['details']}\n\n")

            f.write("## WNIOSKI\n\n")

            if self.failed == 0:
                f.write("🎉 **Wszystkie testy przeszły pomyślnie!**\n\n")
                f.write("System craftingu jest w pełni funkcjonalny i gotowy do użycia.\n")
            else:
                f.write("⚠ **Niektóre testy nie przeszły.**\n\n")
                f.write("Wymaga poprawek w następujących obszarach:\n\n")
                for result in self.test_results:
                    if not result['passed']:
                        f.write(f"- {result['name']}\n")

        print(f"\n📄 Raport zapisany do: {report_path}")

    def get_timestamp(self):
        """Zwraca aktualny timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    # Mockuj input() aby testy były w pełni automatyczne
    # Zwracaj "t" dla wszystkich potwierdzeń
    import builtins
    builtins.input = lambda *args: "t"

    # Uruchom testy
    tester = CraftingTester()
    success_rate = tester.run_all_tests()

    # Generuj raport
    tester.generate_report()

    # Exit code
    sys.exit(0 if tester.failed == 0 else 1)
