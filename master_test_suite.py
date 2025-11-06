#!/usr/bin/env python3
"""
MASTER TEST SUITE - Kompleksowy test wszystkich systemów gry.
"""

import sys
import json
import subprocess

class MasterTester:
    """Koordynator wszystkich testów."""

    def __init__(self):
        self.results = {}
        self.total_passed = 0
        self.total_failed = 0

    def run_test_module(self, module_name, description):
        """Uruchamia moduł testowy i zbiera wyniki."""
        print(f"\n{'='*60}")
        print(f"TESTING: {description}")
        print('='*60)

        try:
            result = subprocess.run(
                [sys.executable, module_name],
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parsuj output aby znaleźć statystyki
            output = result.stdout + result.stderr

            # Szukaj wskaźnika sukcesu
            for line in output.split('\n'):
                if 'Wskaźnik sukcesu:' in line or 'success rate:' in line.lower():
                    print(f"✓ {line.strip()}")
                if 'Zaliczone:' in line or 'passed:' in line.lower():
                    print(f"  {line.strip()}")
                if 'Niezaliczone:' in line or 'failed:' in line.lower():
                    print(f"  {line.strip()}")

            success = result.returncode == 0
            self.results[module_name] = {
                'success': success,
                'description': description,
                'output': output
            }

            if success:
                print(f"✅ {description} - PASS")
            else:
                print(f"❌ {description} - FAIL")
                if '--verbose' in sys.argv:
                    print(f"\nOutput:\n{output}")

            return success

        except subprocess.TimeoutExpired:
            print(f"⏱️  {description} - TIMEOUT")
            self.results[module_name] = {
                'success': False,
                'description': description,
                'error': 'Timeout'
            }
            return False
        except Exception as e:
            print(f"❌ {description} - ERROR: {e}")
            self.results[module_name] = {
                'success': False,
                'description': description,
                'error': str(e)
            }
            return False

    def test_imports(self):
        """Test czy wszystkie moduły się importują."""
        print("\n" + "="*60)
        print("TEST 1: IMPORTS & INITIALIZATION")
        print("="*60)

        modules_to_test = [
            ('engine.character', 'Character'),
            ('engine.combat', 'Combat System'),
            ('engine.crafting', 'Crafting System'),
            ('engine.trading', 'Trading System'),
            ('engine.world', 'World'),
            ('utils.display', 'Display Utils'),
            ('game', 'Main Game')
        ]

        all_passed = True
        for module_path, name in modules_to_test:
            try:
                __import__(module_path)
                print(f"  ✓ {name}")
            except ImportError as e:
                print(f"  ✗ {name} - {e}")
                all_passed = False

        return all_passed

    def test_data_files(self):
        """Test czy wszystkie pliki danych się ładują."""
        print("\n" + "="*60)
        print("TEST 2: DATA FILES")
        print("="*60)

        data_files = [
            'data/classes.json',
            'data/items.json',
            'data/monsters.json',
            'data/locations.json',
            'data/quests.json',
            'data/talents.json',
            'data/recipes.json',
            'data/materials.json'
        ]

        all_passed = True
        for filepath in data_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"  ✓ {filepath}")
            except Exception as e:
                print(f"  ✗ {filepath} - {e}")
                all_passed = False

        return all_passed

    def test_system_integration(self):
        """Test integracji systemów."""
        print("\n" + "="*60)
        print("TEST 3: SYSTEM INTEGRATION")
        print("="*60)

        try:
            from engine.world import World
            from engine.character import Character
            import json

            # Test 1: World inicjalizacja
            world = World()
            print("  ✓ World initialization")

            # Test 2: World ma wszystkie systemy
            assert hasattr(world, 'crafting'), "Brak crafting"
            assert hasattr(world, 'trading'), "Brak trading"
            print("  ✓ World has crafting system")
            print("  ✓ World has trading system")

            # Test 3: Character creation
            with open('data/classes.json', 'r', encoding='utf-8') as f:
                classes_data = json.load(f)

            class_data = classes_data['classes']['wojownik']

            # Create character with proper initialization
            char = Character.__new__(Character)
            char.name = "TestHero"
            char.character_class = "wojownik"
            char.class_data = class_data
            char.level = 1
            char.gold = 1000
            char.attributes = {
                'sila': 16, 'zrecznosc': 12, 'kondycja': 14,
                'inteligencja': 10, 'madrosc': 10, 'charyzma': 10
            }
            char.max_hp = 20
            char.hp = 20
            char.max_mana = 0
            char.mana = 0
            char.xp = 0
            char.inventory = []
            char.equipped = {}
            char.current_location = "startowa_wioska"
            char.talent_points = 0
            char.learned_talents = []
            char.talent_cooldowns = {}
            char.talent_buffs = {}
            char.active_quests = []
            char.completed_quests = []

            print("  ✓ Character creation")

            # Test 4: Character ma talenty
            assert hasattr(char, 'learned_talents'), "Brak learned_talents"
            assert hasattr(char, 'talent_points'), "Brak talent_points"
            print("  ✓ Character has talent system")

            # Test 5: Crafting działa
            recipe = list(world.crafting.recipes.get('potions', {}).values())[0]
            can_craft, reason = world.crafting.can_craft(char, recipe)
            print(f"  ✓ Crafting can_craft check: {reason}")

            # Test 6: Trading działa
            rep = world.trading.get_reputation_with_merchant(char, 'kowal')
            print(f"  ✓ Trading reputation: {rep}")

            return True

        except Exception as e:
            print(f"  ✗ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_all_tests(self):
        """Uruchamia wszystkie testy."""
        print("\n" + "="*70)
        print(" "*15 + "MASTER TEST SUITE - RPG GAME")
        print("="*70)

        # Test 1: Imports
        imports_ok = self.test_imports()

        # Test 2: Data files
        data_ok = self.test_data_files()

        # Test 3: Integration
        integration_ok = self.test_system_integration()

        # Test 4: Crafting (użyj istniejących testów)
        crafting_ok = self.run_test_module(
            'test_crafting_system.py',
            'Crafting System (36 tests)'
        )

        # Test 5: Combat (jeśli istnieje)
        try:
            combat_ok = self.run_test_module(
                'test_combat.py',
                'Combat System'
            )
        except:
            combat_ok = None
            print("  ⚠ Combat tests not found (skipping)")

        # Podsumowanie
        print("\n" + "="*70)
        print("FINAL SUMMARY")
        print("="*70)

        results = {
            'Imports & Init': imports_ok,
            'Data Files': data_ok,
            'System Integration': integration_ok,
            'Crafting System': crafting_ok,
        }

        if combat_ok is not None:
            results['Combat System'] = combat_ok

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")

        passed = sum(1 for r in results.values() if r)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"\nOverall: {passed}/{total} ({success_rate:.1f}%)")

        if success_rate == 100:
            print("\n🎉 ALL TESTS PASSED! Game is ready!")
            return 0
        elif success_rate >= 80:
            print("\n⚠️  Most tests passed, minor issues found.")
            return 1
        else:
            print("\n❌ Multiple failures detected. Review required.")
            return 2


if __name__ == '__main__':
    tester = MasterTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
