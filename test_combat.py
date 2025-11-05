#!/usr/bin/env python3
"""
Skrypt testowy dla systemu walki Combat 2.0
Testuje wszystkie mechaniki i sprawdza balans
"""

import sys
import json
from engine.character import Character
from engine.combat import CombatSystem, load_monster
from utils.dice import d20, roll

class CombatTester:
    """Klasa do testowania systemu walki."""

    def __init__(self):
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'errors': []
        }

    def log(self, message, level='INFO'):
        """Loguje wiadomość testową."""
        prefix = {
            'INFO': '✓',
            'WARNING': '⚠',
            'ERROR': '✗',
            'TEST': '🧪'
        }
        print(f"{prefix.get(level, '•')} {message}")

    def test(self, name, condition, error_msg=""):
        """Wykonuje test i loguje rezultat."""
        print(f"\n🧪 TEST: {name}")
        if condition:
            self.log(f"PASSED: {name}", 'INFO')
            self.test_results['passed'] += 1
            return True
        else:
            self.log(f"FAILED: {name} - {error_msg}", 'ERROR')
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{name}: {error_msg}")
            return False

    def warning(self, message):
        """Loguje ostrzeżenie."""
        self.log(message, 'WARNING')
        self.test_results['warnings'] += 1

    def create_test_character(self, class_name='wojownik', level=5):
        """Tworzy postać testową."""
        print(f"\n{'='*60}")
        print(f"TWORZENIE POSTACI TESTOWEJ: {class_name}, poziom {level}")
        print(f"{'='*60}")

        with open('data/classes.json', 'r', encoding='utf-8') as f:
            classes_data = json.load(f)

        class_data = classes_data['classes'][class_name]

        # Stałe atrybuty dla przewidywalności
        attributes = {
            'sila': 16,
            'zrecznosc': 14,
            'kondycja': 15,
            'inteligencja': 12,
            'madrosc': 13,
            'charyzma': 10
        }

        player = Character(
            name="Testowy Wojownik",
            character_class=class_name,
            attributes=attributes
        )

        # Podnieś poziom
        for _ in range(level - 1):
            player.level += 1
            player.max_hp += 8
            player.hp = player.max_hp
            if player.level >= 2:
                player.talent_points += 1

        self.log(f"Utworzono postać: {player.name}, poziom {player.level}, HP: {player.hp}/{player.max_hp}")
        return player

    def test_basic_combat(self):
        """Test 1: Podstawowe mechaniki walki."""
        print(f"\n{'='*60}")
        print("TEST 1: PODSTAWOWE MECHANIKI WALKI")
        print(f"{'='*60}")

        player = self.create_test_character('wojownik', 3)
        monster = load_monster('goblin')

        self.test(
            "Postać została utworzona",
            player is not None and player.hp > 0,
            f"Player HP: {player.hp if player else 'None'}"
        )

        self.test(
            "Potwór został załadowany",
            monster is not None and monster.hp > 0,
            f"Monster: {monster.name if monster else 'None'}"
        )

        # Test systemu walki
        combat = CombatSystem(player, monster)

        self.test(
            "System walki został zainicjalizowany",
            combat is not None,
            "CombatSystem jest None"
        )

        self.test(
            "Bonusy z talentów zostały załadowane",
            combat.talent_bonuses is not None,
            "talent_bonuses jest None"
        )

        self.test(
            "Monster effects zostały zainicjalizowane",
            'bleeding' in combat.monster_effects,
            "Brak kluczy w monster_effects"
        )

        self.test(
            "Player effects zostały zainicjalizowane",
            'defensive_buff' in combat.player_effects,
            "Brak kluczy w player_effects"
        )

        # Test ataku
        initial_monster_hp = monster.hp
        combat.player_attack('normal')

        self.test(
            "Gracz może wykonać atak",
            True,  # Jeśli doszliśmy tutaj, atak się wykonał
            "player_attack() wywołało błąd"
        )

        # Sprawdź czy jest szansa że potwór stracił HP (nie zawsze trafiamy)
        # Wykonajmy 10 ataków - przynajmniej 1 powinien trafić
        hits = 0
        for _ in range(10):
            hp_before = monster.hp
            combat.player_attack('normal')
            if monster.hp < hp_before:
                hits += 1

        self.test(
            "Ataki czasami trafiają (wykonano 10 ataków)",
            hits > 0,
            f"Żaden z 10 ataków nie trafił (hits: {hits})"
        )

        if hits == 0:
            self.warning("Bardzo niska szansa trafienia - może być problem z mechaniką")

        return player, monster, combat

    def test_special_attacks(self):
        """Test 2: Specjalne ataki."""
        print(f"\n{'='*60}")
        print("TEST 2: SPECJALNE ATAKI")
        print(f"{'='*60}")

        player = self.create_test_character('wojownik', 5)
        monster = load_monster('ork')
        combat = CombatSystem(player, monster)

        attack_types = [
            ('normal', 'Normalny Atak'),
            ('power', 'Potężny Cios'),
            ('precise', 'Precyzyjny Cios'),
            ('defensive', 'Postawa Obronna'),
            ('all_out', 'Atak Na Całość'),
            ('disabling', 'Cios Osłabiający')
        ]

        for attack_type, attack_name in attack_types:
            try:
                hp_before = monster.hp
                combat.player_attack(attack_type)

                self.test(
                    f"Atak '{attack_name}' ({attack_type}) działa",
                    True,
                    ""
                )
            except Exception as e:
                self.test(
                    f"Atak '{attack_name}' ({attack_type}) działa",
                    False,
                    f"Błąd: {str(e)}"
                )

        # Test postawy obronnej - czy zwiększa AC
        player2 = self.create_test_character('wojownik', 5)
        monster2 = load_monster('goblin')
        combat2 = CombatSystem(player2, monster2)

        combat2.player_attack('defensive')

        self.test(
            "Postawa obronna ustawia defensive_buff",
            combat2.player_effects['defensive_buff'] > 0,
            f"defensive_buff: {combat2.player_effects['defensive_buff']}"
        )

        # Test ataku na całość - czy ustawia vulnerable
        player3 = self.create_test_character('wojownik', 5)
        monster3 = load_monster('goblin')
        combat3 = CombatSystem(player3, monster3)

        combat3.player_attack('all_out')

        self.test(
            "Atak Na Całość ustawia vulnerable",
            combat3.player_effects['vulnerable'] > 0,
            f"vulnerable: {combat3.player_effects['vulnerable']}"
        )

    def test_status_effects(self):
        """Test 3: Status effects."""
        print(f"\n{'='*60}")
        print("TEST 3: STATUS EFFECTS")
        print(f"{'='*60}")

        player = self.create_test_character('wojownik', 5)
        monster = load_monster('ork')
        combat = CombatSystem(player, monster)

        # Test stun
        combat.monster_effects['stunned'] = 2
        self.test(
            "Stunned effect można ustawić",
            combat.monster_effects['stunned'] == 2,
            f"stunned: {combat.monster_effects['stunned']}"
        )

        # Test czy stun skipuje turę
        combat.monster_turn()

        self.test(
            "Stunned zmniejsza się po turze",
            combat.monster_effects['stunned'] == 1,
            f"stunned po turze: {combat.monster_effects['stunned']}"
        )

        # Test weakened
        combat.monster_effects['weakened'] = 3

        self.test(
            "Weakened effect można ustawić",
            combat.monster_effects['weakened'] == 3,
            f"weakened: {combat.monster_effects['weakened']}"
        )

        # Test vulnerable
        combat.monster_effects['vulnerable'] = 2
        hp_before = monster.hp

        # Wykonaj atak - vulnerable powinien zwiększyć obrażenia
        combat.player_attack('normal')

        self.test(
            "Vulnerable effect można ustawić",
            combat.monster_effects['vulnerable'] >= 0,  # Może się zmniejszyć po turze
            f"vulnerable: {combat.monster_effects['vulnerable']}"
        )

        # Test DoT effects
        combat.monster_effects['bleeding'] = 3
        combat.monster_effects['bleeding_damage'] = 5

        hp_before = monster.hp
        combat.start_of_turn_effects()

        self.test(
            "Bleeding zadaje obrażenia",
            monster.hp < hp_before or combat.monster_effects['bleeding'] == 0,
            f"HP before: {hp_before}, after: {monster.hp}, bleeding: {combat.monster_effects['bleeding']}"
        )

        # Test poison
        monster2 = load_monster('wilk')
        combat2 = CombatSystem(player, monster2)
        combat2.monster_effects['poisoned'] = 4
        combat2.monster_effects['poison_damage'] = 3

        hp_before = monster2.hp
        combat2.start_of_turn_effects()

        self.test(
            "Poison zadaje obrażenia",
            monster2.hp < hp_before,
            f"HP before: {hp_before}, after: {monster2.hp}"
        )

        # Test burn
        monster3 = load_monster('szkielet')
        combat3 = CombatSystem(player, monster3)
        combat3.monster_effects['burned'] = 3
        combat3.monster_effects['burn_damage'] = 5

        hp_before = monster3.hp
        combat3.start_of_turn_effects()

        self.test(
            "Burn zadaje obrażenia",
            monster3.hp < hp_before,
            f"HP before: {hp_before}, after: {monster3.hp}"
        )

    def test_talents(self):
        """Test 4: System talentów w walce."""
        print(f"\n{'='*60}")
        print("TEST 4: SYSTEM TALENTÓW W WALCE")
        print(f"{'='*60}")

        player = self.create_test_character('wojownik', 10)

        # Daj graczowi punkty talentów i naucz kilka talentów
        player.talent_points = 10

        # Naucz talenty berserker (damage bonus, regen, crit)
        talents_to_learn = ['berserker_1', 'berserker_2', 'berserker_3']

        for talent_id in talents_to_learn:
            success = player.learn_talent(talent_id)
            self.test(
                f"Można nauczyć talent: {talent_id}",
                success,
                f"learn_talent zwróciło {success}"
            )

        # Sprawdź czy talent bonuses działają
        bonuses = player.get_talent_bonuses()

        self.test(
            "get_talent_bonuses zwraca dane",
            bonuses is not None,
            "bonuses jest None"
        )

        self.test(
            "Talent damage_bonus działa",
            bonuses.get('damage_bonus', 0) > 0,
            f"damage_bonus: {bonuses.get('damage_bonus', 0)}"
        )

        self.test(
            "Talent combat_regen działa",
            bonuses.get('combat_regen', 0) > 0,
            f"combat_regen: {bonuses.get('combat_regen', 0)}"
        )

        self.test(
            "Talent crit_chance działa",
            bonuses.get('crit_chance', 0) > 0,
            f"crit_chance: {bonuses.get('crit_chance', 0)}"
        )

        # Test aktywnych talentów
        player2 = self.create_test_character('wojownik', 10)
        player2.talent_points = 10

        # Naucz ultimate talent (berserker_5 - Szał Bojowy)
        for talent_id in ['berserker_1', 'berserker_2', 'berserker_3', 'berserker_4', 'berserker_5']:
            player2.learn_talent(talent_id)

        active_talents = player2.get_active_talents()

        self.test(
            "get_active_talents zwraca talenty",
            len(active_talents) > 0,
            f"Liczba aktywnych talentów: {len(active_talents)}"
        )

        self.test(
            "Szał Bojowy jest na liście aktywnych",
            'berserker_5' in active_talents,
            f"Active talents: {active_talents}"
        )

        # Test użycia talentu
        success = player2.use_talent('berserker_5')

        self.test(
            "Można użyć aktywnego talentu",
            success,
            f"use_talent zwróciło {success}"
        )

        self.test(
            "Talent ma cooldown po użyciu",
            player2.talent_cooldowns.get('berserker_5', 0) > 0,
            f"Cooldown: {player2.talent_cooldowns.get('berserker_5', 0)}"
        )

        self.test(
            "Talent ustawił buff",
            len(player2.talent_buffs) > 0,
            f"Talent buffs: {player2.talent_buffs}"
        )

    def test_monster_ai(self):
        """Test 5: AI przeciwników."""
        print(f"\n{'='*60}")
        print("TEST 5: AI PRZECIWNIKÓW")
        print(f"{'='*60}")

        player = self.create_test_character('wojownik', 5)

        # Test 1: Boss enrage
        print("\n--- Test: Boss Enrage ---")
        monster = load_monster('mroczny_czarnoksieznik')  # Boss

        self.test(
            "Boss został załadowany jako boss",
            monster.is_boss == True,
            f"is_boss: {monster.is_boss}"
        )

        # Zmniejsz HP bossa poniżej 50%
        monster.hp = int(monster.max_hp * 0.4)

        combat = CombatSystem(player, monster)

        # Tura potwora powinna wywołać enrage
        initial_attack_bonus = monster.attack_data.get('bonus', 0)
        combat.monster_turn()

        self.test(
            "Boss enrage aktywuje się przy HP < 50%",
            monster.enraged == True,
            f"enraged: {monster.enraged}"
        )

        self.test(
            "Enrage zwiększa attack bonus",
            monster.attack_data.get('bonus', 0) > initial_attack_bonus,
            f"Bonus przed: {initial_attack_bonus}, po: {monster.attack_data.get('bonus', 0)}"
        )

        # Test 2: Użycie mikstury przez przeciwnika
        print("\n--- Test: Użycie mikstury ---")
        monster2 = load_monster('ork_wojownik')
        monster2.inventory = ['mikstura_leczenia_mala']
        monster2.hp = int(monster2.max_hp * 0.25)  # HP < 30%

        combat2 = CombatSystem(player, monster2)

        hp_before = monster2.hp
        combat2.monster_turn()

        self.test(
            "Przeciwnik używa mikstury gdy HP < 30%",
            monster2.used_healing == True or monster2.hp > hp_before,
            f"used_healing: {monster2.used_healing}, HP before: {hp_before}, after: {monster2.hp}"
        )

        # Test 3: Zmiana taktyki
        print("\n--- Test: Zmiana taktyki ---")
        monster3 = load_monster('ork')
        combat3 = CombatSystem(player, monster3)

        # HP > 70%
        monster3.hp = int(monster3.max_hp * 0.8)
        combat3.monster_turn()

        self.test(
            "Taktyka aggressive przy HP > 70%",
            monster3.ai_tactic == 'aggressive',
            f"Taktyka: {monster3.ai_tactic}, HP%: {monster3.get_hp_percentage():.1f}"
        )

        # HP 30-70%
        monster3.hp = int(monster3.max_hp * 0.5)
        combat3.monster_turn()

        self.test(
            "Taktyka balanced przy HP 30-70%",
            monster3.ai_tactic == 'balanced',
            f"Taktyka: {monster3.ai_tactic}, HP%: {monster3.get_hp_percentage():.1f}"
        )

        # HP < 30%
        monster3.hp = int(monster3.max_hp * 0.2)
        combat3.monster_turn()

        self.test(
            "Taktyka defensive przy HP < 30%",
            monster3.ai_tactic == 'defensive',
            f"Taktyka: {monster3.ai_tactic}, HP%: {monster3.get_hp_percentage():.1f}"
        )

    def test_balance(self):
        """Test 6: Balans."""
        print(f"\n{'='*60}")
        print("TEST 6: BALANS WALKI")
        print(f"{'='*60}")

        # Symuluj 10 walk poziom 5 vs Ork Wojownik
        wins = 0
        losses = 0
        avg_turns = 0
        avg_player_hp_left = 0

        print("\nSymulacja 10 walk: Wojownik lvl 5 vs Ork")

        for i in range(10):
            player = self.create_test_character('wojownik', 5)
            monster = load_monster('ork')
            combat = CombatSystem(player, monster)

            turns = 0
            max_turns = 50  # Zabezpieczenie przed nieskończoną pętlą

            while player.is_alive() and monster.is_alive() and turns < max_turns:
                # Tura gracza - używaj różnych ataków losowo
                import random
                attack_types = ['normal', 'power', 'precise', 'defensive']
                combat.player_attack(random.choice(attack_types))

                if not monster.is_alive():
                    break

                # Tura potwora
                combat.monster_turn()

                turns += 1

            if player.is_alive():
                wins += 1
                avg_player_hp_left += player.hp
            else:
                losses += 1

            avg_turns += turns

            print(f"  Walka {i+1}: {'WYGRANA' if player.is_alive() else 'PRZEGRANA'} w {turns} turach, HP gracza: {player.hp}/{player.max_hp}")

        avg_turns /= 10
        if wins > 0:
            avg_player_hp_left /= wins

        win_rate = (wins / 10) * 100

        print(f"\n{'='*60}")
        print(f"WYNIKI SYMULACJI:")
        print(f"  Wygrane: {wins}/10 ({win_rate:.0f}%)")
        print(f"  Przegrane: {losses}/10")
        print(f"  Średnia liczba tur: {avg_turns:.1f}")
        print(f"  Średnie HP gracza po wygranej: {avg_player_hp_left:.0f}")
        print(f"{'='*60}")

        self.test(
            "Win rate jest rozsądny (30-90%)",
            30 <= win_rate <= 90,
            f"Win rate: {win_rate:.0f}% (oczekiwano 30-90%)"
        )

        if win_rate < 30:
            self.warning("Win rate jest bardzo niski - walki mogą być za trudne!")
        elif win_rate > 90:
            self.warning("Win rate jest bardzo wysoki - walki mogą być za łatwe!")

        self.test(
            "Walki nie są za długie (< 30 tur)",
            avg_turns < 30,
            f"Średnia tur: {avg_turns:.1f} (oczekiwano < 30)"
        )

        self.test(
            "Walki nie są za krótkie (> 3 tury)",
            avg_turns > 3,
            f"Średnia tur: {avg_turns:.1f} (oczekiwano > 3)"
        )

    def print_summary(self):
        """Wyświetla podsumowanie testów."""
        print(f"\n{'='*60}")
        print(f"{'='*60}")
        print("PODSUMOWANIE TESTÓW")
        print(f"{'='*60}")
        print(f"{'='*60}")

        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0

        print(f"\n✓ Testy zakończone pomyślnie: {self.test_results['passed']}")
        print(f"✗ Testy zakończone niepowodzeniem: {self.test_results['failed']}")
        print(f"⚠ Ostrzeżenia: {self.test_results['warnings']}")
        print(f"\nWskaźnik sukcesu: {success_rate:.1f}%")

        if self.test_results['errors']:
            print(f"\n{'='*60}")
            print("BŁĘDY:")
            print(f"{'='*60}")
            for error in self.test_results['errors']:
                print(f"  ✗ {error}")

        print(f"\n{'='*60}")
        if self.test_results['failed'] == 0:
            print("🎉 WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE! 🎉")
        else:
            print("⚠️  NIEKTÓRE TESTY NIE POWIODŁY SIĘ ⚠️")
        print(f"{'='*60}\n")

        return self.test_results['failed'] == 0

    def run_all_tests(self):
        """Uruchamia wszystkie testy."""
        print(f"\n{'#'*60}")
        print("#" + " "*58 + "#")
        print("#" + " COMBAT 2.0 - KOMPLEKSOWY TEST ".center(58) + "#")
        print("#" + " "*58 + "#")
        print(f"{'#'*60}\n")

        try:
            self.test_basic_combat()
            self.test_special_attacks()
            self.test_status_effects()
            self.test_talents()
            self.test_monster_ai()
            self.test_balance()
        except Exception as e:
            self.log(f"KRYTYCZNY BŁĄD: {str(e)}", 'ERROR')
            import traceback
            traceback.print_exc()
            self.test_results['failed'] += 1

        return self.print_summary()


if __name__ == '__main__':
    # Mock input() aby nie blokować testów
    import builtins
    builtins.input = lambda *args: ""

    tester = CombatTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
