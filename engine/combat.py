"""System walki."""
import json
from utils.dice import d20, roll, calculate_modifier
from utils.display import (print_combat_status, print_separator, press_enter,
                            print_success, print_error, print_warning, colored_text)


class Monster:
    """Klasa reprezentująca potwora/przeciwnika."""

    def __init__(self, monster_id, monster_data):
        """
        Inicjalizuje potwora.

        Args:
            monster_id: ID potwora
            monster_data: Dane potwora ze słownika
        """
        self.id = monster_id
        self.name = monster_data['nazwa']
        self.level = monster_data['poziom']
        self.typ = monster_data['typ']
        self.max_hp = monster_data['zdrowie']
        self.hp = self.max_hp
        self.armor_class = monster_data['klasa_pancerza']
        self.attributes = monster_data['atrybuty']
        self.attack_data = monster_data['atak']
        self.xp_reward = monster_data['doswiadczenie']
        self.loot = monster_data.get('lup', [])
        self.special = monster_data.get('specjalne', {})
        self.resistances = monster_data.get('odpornosci', [])
        self.weaknesses = monster_data.get('slabosci', [])
        self.spells = monster_data.get('zaklecia', [])
        self.is_boss = monster_data.get('boss', False)

    def get_modifier(self, attribute):
        """Zwraca modyfikator dla atrybutu."""
        return calculate_modifier(self.attributes[attribute])

    def take_damage(self, damage, damage_type='physical'):
        """
        Otrzymuje obrażenia.

        Args:
            damage: Ilość obrażeń
            damage_type: Typ obrażeń

        Returns:
            Rzeczywiste obrażenia (po oporach/słabościach)
        """
        # Sprawdź odporności i słabości
        if damage_type in self.resistances:
            damage = damage // 2
            print_warning(f"{self.name} jest odporny na ten typ ataku!")

        if damage_type in self.weaknesses:
            damage = int(damage * 1.5)
            print_success(f"{self.name} jest słaby na ten typ ataku!")

        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        return damage

    def is_alive(self):
        """Sprawdza czy potwór żyje."""
        return self.hp > 0

    def attack(self):
        """
        Wykonuje atak.

        Returns:
            Tuple (roll, bonus, damage_roll)
        """
        attack_roll = d20()
        attack_bonus = self.attack_data.get('bonus', 0)
        damage_roll = self.attack_data.get('obrazenia', '1d6')

        return attack_roll, attack_bonus, damage_roll


class CombatSystem:
    """System zarządzania walką."""

    def __init__(self, player, monster):
        """
        Inicjalizuje system walki.

        Args:
            player: Postać gracza
            monster: Potwór do walki
        """
        self.player = player
        self.monster = monster
        self.turn = 1

        # Bonusy z talentów
        self.talent_bonuses = player.get_talent_bonuses()

        # Licznik combo (dla talentu Mistrz Combo)
        self.combo_hits = 0

        # Efekty statusowe na potworze
        self.monster_effects = {
            'bleeding': 0,  # Tury krwawienia
            'bleeding_damage': 0,  # Obrażenia za turę
            'poisoned': 0,  # Tury trucizny
            'poison_damage': 0,  # Obrażenia za turę
            'weakened': 0,  # Tury osłabienia
            'slowed': 0,  # Tury spowolnienia
        }

    def start_combat(self):
        """
        Rozpoczyna walkę.

        Returns:
            True jeśli gracz wygrał, False jeśli przegrał
        """
        print_separator("*")
        print(colored_text(f"⚔ WALKA: {self.player.name} vs {self.monster.name}! ⚔", 'red'))
        print_separator("*")
        press_enter()

        # Główna pętla walki
        while self.player.is_alive() and self.monster.is_alive():
            self.combat_turn()
            self.turn += 1

        # Wynik walki
        if self.player.is_alive():
            return self.victory()
        else:
            return self.defeat()

    def combat_turn(self):
        """Pojedyncza tura walki."""
        print_separator("=")
        print(f"TURA {self.turn}")

        # Efekty na początku tury
        self.start_of_turn_effects()

        print_combat_status(
            self.player.name, self.player.hp, self.player.max_hp,
            self.monster.name, self.monster.hp, self.monster.max_hp
        )

        # Tura gracza
        self.player_turn()

        if not self.monster.is_alive():
            return

        # Tura potwora
        print_separator("-")
        self.monster_turn()

        press_enter()

        # Aktualizuj cooldowny talentów
        self.player.update_talent_cooldowns()

    def start_of_turn_effects(self):
        """Aplikuje efekty na początku tury."""
        # Regeneracja bojowa z talentów
        if self.talent_bonuses['combat_regen'] > 0:
            heal = self.talent_bonuses['combat_regen']
            self.player.heal(heal)
            print_success(f"⚕ Regeneracja bojowa: +{heal} HP")

        # Aura życia z talentów
        if self.talent_bonuses['life_aura'] > 0:
            heal = self.talent_bonuses['life_aura']
            self.player.heal(heal)
            print_success(f"✨ Aura życia: +{heal} HP")

        # Obsługa aktywnych buffów gracza
        buffs_to_remove = []
        for buff_name, buff_data in self.player.talent_buffs.items():
            if 'turns_left' in buff_data:
                # Szał Bojowy - koszt HP
                if buff_name == 'rage_mode':
                    cost = buff_data.get('cost_per_turn', 5)
                    self.player.take_damage(cost)
                    print(colored_text(f"🔥 Szał Bojowy: -{cost} HP", 'red'))

                # Zmniejsz licznik tur
                buff_data['turns_left'] -= 1

                # Informuj o wygasającym buffie
                if buff_data['turns_left'] == 0:
                    buffs_to_remove.append(buff_name)
                    if buff_name == 'rage_mode':
                        print_warning("🔥 Szał Bojowy wygasł!")
                    elif buff_name == 'invisibility':
                        print_warning("👻 Niewidzialność wygasła!")
                    elif buff_name == 'shield':
                        print_warning("🛡️ Tarcza ochronna wygasła!")

        # Usuń wygasłe buffy
        for buff_name in buffs_to_remove:
            del self.player.talent_buffs[buff_name]

        # Efekty DoT na potworze
        if self.monster_effects['bleeding'] > 0:
            dmg = self.monster_effects['bleeding_damage']
            self.monster.take_damage(dmg)
            print(colored_text(f"🩸 {self.monster.name} krwawi: -{dmg} HP", 'red'))
            self.monster_effects['bleeding'] -= 1

        if self.monster_effects['poisoned'] > 0:
            dmg = self.monster_effects['poison_damage']
            self.monster.take_damage(dmg)
            print(colored_text(f"☠ {self.monster.name} jest zatruty: -{dmg} HP", 'green'))
            self.monster_effects['poisoned'] -= 1

    def player_turn(self):
        """Tura gracza."""
        print(f"\n--- Twoja tura ---")

        # Menu akcji
        actions = ["Atakuj", "Użyj mikstury", "Uciekaj"]

        # Dodaj zaklęcia jeśli postać je ma
        if self.player.spells and hasattr(self.player, 'mana') and self.player.mana > 0:
            actions.insert(1, "Rzuć zaklęcie")

        # Dodaj aktywne talenty
        active_talents = self.player.get_active_talents()
        if active_talents:
            actions.insert(1, "Użyj umiejętności")

        print("\nCo chcesz zrobić?")
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action}")

        while True:
            try:
                choice = input("\nWybór: ").strip()
                choice_num = int(choice)
                if 1 <= choice_num <= len(actions):
                    break
                print(f"Wybierz liczbę od 1 do {len(actions)}!")
            except ValueError:
                print("Wprowadź poprawną liczbę!")

        action = actions[choice_num - 1]

        if action == "Atakuj":
            self.player_attack()
        elif action == "Użyj umiejętności":
            self.player_use_talent()
        elif action == "Rzuć zaklęcie":
            self.player_cast_spell()
        elif action == "Użyj mikstury":
            self.player_use_item()
        elif action == "Uciekaj":
            if self.attempt_flee():
                return True

    def player_attack(self):
        """Gracz atakuje."""
        import random

        # Sprawdź bonus do ataku z talentów
        attack_bonus_from_talents = self.talent_bonuses.get('attack_bonus', 0)

        # Rzut na trafienie
        attack_roll = d20()
        total_attack = attack_roll + self.player.attack_bonus + attack_bonus_from_talents

        if attack_bonus_from_talents > 0:
            print(f"\n🎲 Rzut na trafienie: {attack_roll} + {self.player.attack_bonus} + {attack_bonus_from_talents} (talent) = {total_attack}")
        else:
            print(f"\n🎲 Rzut na trafienie: {attack_roll} + {self.player.attack_bonus} = {total_attack}")

        # Sprawdź bonus do szansy krytycznej z talentów
        crit_chance_bonus = self.talent_bonuses.get('crit_chance', 0)
        crit_threshold = 20 - (crit_chance_bonus // 5)  # Każde 5% = -1 do progu (np. 5% -> crit na 19-20)

        # Krytyk (naturalny lub z bonusem)
        is_crit = attack_roll == 20 or (attack_roll >= crit_threshold and crit_chance_bonus > 0)

        if is_crit:
            print(colored_text("💥 KRYTYCZNE TRAFIENIE! 💥", 'yellow'))
            damage_roll = roll(self.player.get_weapon_damage())
            damage = damage_roll * 2

            # Dodaj modyfikator siły/zręczności
            if self.player.equipped['bron']:
                attr = self.player.equipped['bron'].get('atrybut', 'sila')
                damage += self.player.get_modifier(attr) * 2  # x2 na crit
            else:
                damage += self.player.get_modifier('sila') * 2

            # Zastosuj bonus do obrażeń z talentów
            damage = self.apply_damage_bonuses(damage)

            print(f"⚔ Zadajesz {damage} obrażeń!")
            self.monster.take_damage(damage)

            # Zwiększ combo
            self.combo_hits += 1

            # Sprawdź dodatkowy atak
            self.check_extra_attack()

            # Sprawdź efekty statusowe (krwawienie, trucizna)
            self.apply_status_effects()
            return

        # Automatyczna porażka
        if attack_roll == 1:
            print(colored_text("💢 KRYTYCZNA PORAŻKA!", 'red'))
            print("Twój atak chybia!")
            self.combo_hits = 0  # Reset combo
            return

        # Sprawdź trafienie
        if total_attack >= self.monster.armor_class:
            damage = roll(self.player.get_weapon_damage())

            # Dodaj modyfikator siły/zręczności
            if self.player.equipped['bron']:
                attr = self.player.equipped['bron'].get('atrybut', 'sila')
                damage += self.player.get_modifier(attr)
            else:
                damage += self.player.get_modifier('sila')

            damage = max(1, damage)  # Minimum 1 obrażenie

            # Zastosuj bonus do obrażeń z talentów
            damage = self.apply_damage_bonuses(damage)

            print(f"✓ Trafiasz! Zadajesz {damage} obrażeń!")
            self.monster.take_damage(damage)

            # Zwiększ combo
            self.combo_hits += 1

            # Sprawdź dodatkowy atak
            self.check_extra_attack()

            # Sprawdź efekty statusowe (krwawienie, trucizna)
            self.apply_status_effects()
        else:
            print(colored_text("✗ Chybiasz!", 'red'))
            self.combo_hits = 0  # Reset combo

    def apply_damage_bonuses(self, base_damage):
        """
        Aplikuje bonusy do obrażeń z talentów i buffów.

        Args:
            base_damage: Bazowe obrażenia

        Returns:
            Obrażenia po bonusach
        """
        damage = base_damage

        # Bonus % z talentów pasywnych
        damage_bonus = self.talent_bonuses.get('damage_bonus', 0)
        if damage_bonus > 0:
            bonus_dmg = int(damage * damage_bonus)
            damage += bonus_dmg
            if bonus_dmg > 0:
                print(colored_text(f"  ⚡ Bonus z talentów: +{bonus_dmg} obrażeń", 'yellow'))

        # Sprawdź aktywne buffy (np. Szał Bojowy)
        if 'rage_mode' in self.player.talent_buffs:
            buff = self.player.talent_buffs['rage_mode']
            multiplier = buff.get('damage_multiplier', 1.0)
            original_damage = damage
            damage = int(damage * multiplier)
            print(colored_text(f"  🔥 SZAŁ BOJOWY: {original_damage} → {damage} obrażeń!", 'red'))

        # Bonus z combo (Mistrz Combo)
        if self.combo_hits >= 3 and self.player.has_talent('mistrz_broni_3'):
            combo_bonus = int(damage * 0.15 * (self.combo_hits - 2))  # +15% za każde combo powyżej 3
            damage += combo_bonus
            print(colored_text(f"  💫 Combo x{self.combo_hits}: +{combo_bonus} obrażeń", 'cyan'))

        return damage

    def check_extra_attack(self):
        """Sprawdza czy gracz dostaje dodatkowy atak z talentów."""
        import random

        # Podwójne Uderzenie (Berserker)
        if self.player.has_talent('berserker_4'):
            if random.random() < 0.25:  # 25% szansy
                print(colored_text("\n⚡ PODWÓJNE UDERZENIE! Atakujesz ponownie!", 'yellow'))
                press_enter("Naciśnij ENTER aby wykonać dodatkowy atak...")
                self.player_attack()

        # Seria Ciosów (Mistrz Broni)
        elif self.player.has_talent('mistrz_broni_4'):
            if random.random() < 0.30:  # 30% szansy
                print(colored_text("\n⚔️ SERIA CIOSÓW! Wykonujesz dodatkowy atak!", 'yellow'))
                press_enter("Naciśnij ENTER aby wykonać dodatkowy atak...")
                self.player_attack()

    def apply_status_effects(self):
        """Aplikuje efekty statusowe na wroga (krwawienie, trucizna, itp.)."""
        import random

        # Krwawienie (Berserker, Zabójca)
        if self.player.has_talent('berserker_3') or self.player.has_talent('zabojca_2'):
            if random.random() < 0.20:  # 20% szansy
                self.monster_effects['bleeding'] = 3  # 3 tury
                self.monster_effects['bleeding_damage'] = 3 + self.player.level
                print(colored_text(f"  🩸 {self.monster.name} zaczyna krwawić!", 'red'))

        # Trucizna (Zabójca)
        if self.player.has_talent('zabojca_3'):
            if random.random() < 0.25:  # 25% szansy
                self.monster_effects['poisoned'] = 4  # 4 tury
                self.monster_effects['poison_damage'] = 2 + self.player.level // 2
                print(colored_text(f"  ☠️ {self.monster.name} został zatruty!", 'green'))

    def player_use_talent(self):
        """Gracz używa aktywnej umiejętności z talentów."""
        active_talents = self.player.get_active_talents()

        if not active_talents:
            print_error("Nie masz dostępnych umiejętności!")
            return

        print("\n--- Twoje umiejętności ---")
        available_talents = []

        for i, talent_id in enumerate(active_talents, 1):
            talent_data = self.player.get_talent_data(talent_id)
            if not talent_data:
                continue

            # Sprawdź cooldown
            if talent_id in self.player.talent_cooldowns and self.player.talent_cooldowns[talent_id] > 0:
                cooldown_left = self.player.talent_cooldowns[talent_id]
                print(f"  {i}. {talent_data['nazwa']} - {colored_text(f'[Cooldown: {cooldown_left} tur]', 'red')}")
                continue

            available_talents.append((i, talent_id, talent_data))
            cooldown = talent_data['efekt'].get('cooldown', 0)
            print(f"  {i}. {talent_data['nazwa']} - {talent_data['opis']}")
            if cooldown > 0:
                print(f"      {colored_text(f'[Cooldown: {cooldown} tur]', 'yellow')}")

        if not available_talents:
            print_warning("\nWszystkie umiejętności są na cooldownie!")
            press_enter()
            return

        print(f"  0. Anuluj")

        try:
            choice = int(input("\nWybierz umiejętność: "))
            if choice == 0:
                return

            # Znajdź wybraną umiejętność
            selected = None
            for num, talent_id, talent_data in available_talents:
                if num == choice:
                    selected = (talent_id, talent_data)
                    break

            if not selected:
                print_error("Nieprawidłowy wybór!")
                return

            talent_id, talent_data = selected

            # Użyj talentu
            success = self.player.use_talent(talent_id)
            if success:
                print_success(f"\n✨ Używasz: {talent_data['nazwa']}!")

                # Aplikuj efekt w walce
                self.apply_talent_effect(talent_id, talent_data)
            else:
                print_error("Nie udało się użyć umiejętności!")

        except ValueError:
            print_error("Wprowadź poprawną liczbę!")

    def apply_talent_effect(self, talent_id, talent_data):
        """
        Aplikuje efekt aktywnego talentu w walce.

        Args:
            talent_id: ID talentu
            talent_data: Dane talentu
        """
        import random

        efekt = talent_data['efekt']
        typ = efekt.get('typ')

        # Szał Bojowy (Berserker Ultimate)
        if typ == 'rage_mode':
            duration = efekt.get('duration', 3)
            self.player.talent_buffs['rage_mode'] = {
                'damage_multiplier': efekt.get('damage_multiplier', 2.0),
                'turns_left': duration,
                'cost_per_turn': efekt.get('cost_per_turn', 5)
            }
            print(colored_text(f"🔥 Wpadasz w SZAŁ BOJOWY na {duration} tury!", 'red'))
            print(colored_text(f"   Obrażenia x{efekt.get('damage_multiplier', 2.0)}, ale tracisz {efekt.get('cost_per_turn', 5)} HP/turę", 'yellow'))

        # Niewidzialność (Zabójca Ultimate)
        elif typ == 'invisibility':
            duration = efekt.get('duration', 2)
            self.player.talent_buffs['invisibility'] = {
                'turns_left': duration,
                'dodge_bonus': efekt.get('dodge_bonus', 100)
            }
            print(colored_text(f"👻 Stajesz się NIEWIDZIALNY na {duration} tury!", 'cyan'))
            print(colored_text(f"   Unikasz wszystkich ataków!", 'cyan'))

        # Święty Gniew (Paladyn Ultimate)
        elif typ == 'holy_fury':
            damage = roll(efekt.get('damage', '10d8'))
            heal = roll(efekt.get('heal', '5d8'))
            self.monster.take_damage(damage, 'holy')
            self.player.heal(heal)
            print(colored_text(f"✨ ŚWIĘTY GNIEW spada na {self.monster.name}!", 'yellow'))
            print(f"   💥 Zadajesz {damage} obrażeń świętym ogniem!")
            print(f"   ⚕️ Leczysz się o {heal} HP!")

        # Bezpośrednie obrażenia
        elif typ == 'direct_damage':
            damage = roll(efekt.get('damage', '5d8'))
            self.monster.take_damage(damage)
            print(f"   💥 Zadajesz {damage} obrażeń!")

        # Leczenie
        elif typ == 'heal':
            heal = roll(efekt.get('amount', '4d8+10'))
            self.player.heal(heal)
            print(f"   ⚕️ Leczysz się o {heal} HP!")

        # Tarcza ochronna
        elif typ == 'shield':
            duration = efekt.get('duration', 3)
            absorption = efekt.get('absorption', 20)
            self.player.talent_buffs['shield'] = {
                'turns_left': duration,
                'absorption': absorption
            }
            print(colored_text(f"🛡️ Otacza cię magiczna tarcza absorbująca {absorption} obrażeń przez {duration} tury!", 'blue'))

    def player_cast_spell(self):
        """Gracz rzuca zaklęcie."""
        if not self.player.spells:
            print_error("Nie znasz żadnych zaklęć!")
            return

        print("\n--- Twoje zaklęcia ---")
        for i, spell in enumerate(self.player.spells, 1):
            print(f"  {i}. {spell}")

        try:
            choice = int(input("\nWybierz zaklęcie (0 aby anulować): "))
            if choice == 0:
                return
            if 1 <= choice <= len(self.player.spells):
                spell_name = self.player.spells[choice - 1]
                self.cast_spell(spell_name)
            else:
                print_error("Nieprawidłowy wybór!")
        except ValueError:
            print_error("Wprowadź poprawną liczbę!")

    def cast_spell(self, spell_name):
        """
        Rzuca zaklęcie.

        Args:
            spell_name: Nazwa zaklęcia
        """
        # Prosty system zaklęć
        spells = {
            'magiczny_pocisk': {'koszt': 1, 'obrazenia': '3d4+3', 'typ': 'zawsze_trafia'},
            'spalajaca_dlonie': {'koszt': 1, 'obrazenia': '3d6', 'typ': 'rzut_obronny'},
            'kula_ognia': {'koszt': 3, 'obrazenia': '8d6', 'typ': 'rzut_obronny'},
            'lodowy_szturm': {'koszt': 2, 'obrazenia': '4d8', 'typ': 'rzut_obronny'},
            'lańcuch_błyskawic': {'koszt': 3, 'obrazenia': '10d6', 'typ': 'rzut_obronny'},
            'leczenie_ran': {'koszt': 1, 'leczenie': '1d8+4'},
            'swiety_blask': {'koszt': 1, 'obrazenia': '2d8', 'typ': 'magiczny'},
        }

        if spell_name not in spells:
            print_error("Nieznane zaklęcie!")
            return

        spell = spells[spell_name]

        # Sprawdź manę
        if self.player.mana < spell['koszt']:
            print_error("Nie masz wystarczająco many!")
            return

        # Zużyj manę
        self.player.mana -= spell['koszt']

        # Efekt zaklęcia
        if 'leczenie' in spell:
            heal = roll(spell['leczenie'])
            self.player.heal(heal)
            print_success(f"✨ Rzucasz {spell_name}! Leczysz się o {heal} HP!")
        elif 'obrazenia' in spell:
            damage = roll(spell['obrazenia'])
            print(f"✨ Rzucasz {spell_name}!")

            if spell['typ'] == 'zawsze_trafia':
                print(f"⚡ Magiczny pocisk zawsze trafia! Zadajesz {damage} obrażeń!")
                self.monster.take_damage(damage, 'magic')
            elif spell['typ'] == 'rzut_obronny':
                # Prosty rzut obronny
                save_roll = d20() + self.monster.get_modifier('zrecznosc')
                dc = 10 + self.player.get_modifier('inteligencja') + self.player.level // 2
                if save_roll < dc:
                    print(f"💥 {self.monster.name} nie unika! Zadajesz {damage} obrażeń!")
                    self.monster.take_damage(damage, 'magic')
                else:
                    damage = damage // 2
                    print(f"⚠ {self.monster.name} częściowo unika! Zadajesz {damage} obrażeń!")
                    self.monster.take_damage(damage, 'magic')

    def player_use_item(self):
        """Gracz używa przedmiotu."""
        # Znajdź mikstury
        potions = [item for item in self.player.inventory if item.get('typ') == 'mikstura']

        if not potions:
            print_error("Nie masz żadnych mikstur!")
            return

        print("\n--- Twoje mikstury ---")
        for i, potion in enumerate(potions, 1):
            print(f"  {i}. {potion['nazwa']}")

        try:
            choice = int(input("\nWybierz miksturę (0 aby anulować): "))
            if choice == 0:
                return
            if 1 <= choice <= len(potions):
                potion = potions[choice - 1]
                success, message = self.player.use_item(potion)
                if success:
                    print_success(message)
                else:
                    print_error(message)
            else:
                print_error("Nieprawidłowy wybór!")
        except ValueError:
            print_error("Wprowadź poprawną liczbę!")

    def monster_turn(self):
        """Tura potwora."""
        import random

        print(f"\n--- Tura {self.monster.name} ---")

        # Potwór atakuje
        attack_roll, attack_bonus, damage_roll = self.monster.attack()

        # Sprawdź KP z bonusem z talentów
        player_ac = self.player.armor_class + self.talent_bonuses.get('armor_bonus', 0)

        total_attack = attack_roll + attack_bonus

        print(f"🎲 {self.monster.name} atakuje!")
        if self.talent_bonuses.get('armor_bonus', 0) > 0:
            print(f"   Rzut: {attack_roll} + {attack_bonus} = {total_attack} vs KP {player_ac} ({self.player.armor_class}+{self.talent_bonuses['armor_bonus']} z talentów)")
        else:
            print(f"   Rzut: {attack_roll} + {attack_bonus} = {total_attack} vs KP {player_ac}")

        # Sprawdź niewidzialność (auto-dodge)
        if 'invisibility' in self.player.talent_buffs:
            print(colored_text("👻 Jesteś niewidzialny - atak przechodzi przez ciebie!", 'cyan'))
            return

        # Sprawdź dodge/evasion
        dodge_chance = self.talent_bonuses.get('dodge_chance', 0)
        if dodge_chance > 0 and random.randint(1, 100) <= dodge_chance:
            print(colored_text(f"⚡ UNIK! Zwinnie unikasz ataku! (szansa: {dodge_chance}%)", 'cyan'))
            return

        # Krytyk
        if attack_roll == 20:
            print(colored_text("💥 KRYTYCZNE TRAFIENIE WROGA!", 'red'))
            damage = roll(damage_roll) * 2

            # Sprawdź tarczę
            damage = self.apply_shield_absorption(damage)

            if damage > 0:
                self.player.take_damage(damage)
                print(f"⚔ {self.monster.name} zadaje ci {damage} obrażeń!")

                # Sprawdź odbicie obrażeń
                self.check_damage_reflect(damage)
            return

        # Automatyczna porażka
        if attack_roll == 1:
            print(colored_text("✓ Potwór chybia!", 'green'))
            return

        # Sprawdź trafienie
        if total_attack >= player_ac:
            damage = roll(damage_roll)

            # Sprawdź tarczę
            damage = self.apply_shield_absorption(damage)

            if damage > 0:
                self.player.take_damage(damage)
                print(colored_text(f"✗ {self.monster.name} trafia! Otrzymujesz {damage} obrażeń!", 'red'))

                # Sprawdź odbicie obrażeń
                self.check_damage_reflect(damage)

                # Sprawdź kontratak
                self.check_counter_attack()
        else:
            print(colored_text(f"✓ Bronisz się przed atakiem!", 'green'))

    def apply_shield_absorption(self, damage):
        """
        Aplikuje absorpcję obrażeń przez tarczę.

        Args:
            damage: Bazowe obrażenia

        Returns:
            Obrażenia po absorpcji
        """
        if 'shield' in self.player.talent_buffs:
            absorption = self.player.talent_buffs['shield'].get('absorption', 0)
            absorbed = min(damage, absorption)
            remaining_damage = max(0, damage - absorbed)

            print(colored_text(f"🛡️ Tarcza absorbuje {absorbed} obrażeń!", 'blue'))

            # Zmniejsz absorpcję tarczy
            self.player.talent_buffs['shield']['absorption'] -= absorbed

            # Jeśli tarcza się wyczerpała, usuń ją
            if self.player.talent_buffs['shield']['absorption'] <= 0:
                del self.player.talent_buffs['shield']
                print_warning("🛡️ Tarcza ochronna została zniszczona!")

            return remaining_damage

        return damage

    def check_damage_reflect(self, damage):
        """
        Sprawdza i aplikuje odbicie obrażeń.

        Args:
            damage: Otrzymane obrażenia
        """
        reflect_percent = self.talent_bonuses.get('damage_reflect', 0)
        if reflect_percent > 0:
            reflected = int(damage * reflect_percent)
            if reflected > 0:
                self.monster.take_damage(reflected)
                print(colored_text(f"⚔️ Odbijasz {reflected} obrażeń na {self.monster.name}! ({int(reflect_percent * 100)}%)", 'yellow'))

    def check_counter_attack(self):
        """Sprawdza szansę na kontratak po otrzymaniu obrażeń."""
        import random

        # Kontratak (Obrońca)
        if self.player.has_talent('obronca_3'):
            if random.random() < 0.20:  # 20% szansy
                print(colored_text("\n⚡ KONTRATAK! Odpowiadasz błyskawicznym ciosem!", 'yellow'))
                # Wykonaj atak (uproszczony, bez wszystkich bonusów)
                damage = roll(self.player.get_weapon_damage())
                if self.player.equipped['bron']:
                    attr = self.player.equipped['bron'].get('atrybut', 'sila')
                    damage += self.player.get_modifier(attr)
                else:
                    damage += self.player.get_modifier('sila')

                damage = max(1, damage)
                self.monster.take_damage(damage)
                print(f"   💥 Zadajesz {damage} obrażeń kontratakując!")

    def attempt_flee(self):
        """
        Próba ucieczki.

        Returns:
            True jeśli uciekł, False jeśli nie
        """
        # Sprawdź czy to boss - z bossa nie można uciec
        if self.monster.is_boss:
            print_error("Nie możesz uciec od bossa!")
            return False

        # Rzut na ucieczkę
        flee_roll = d20() + self.player.get_modifier('zrecznosc')
        difficulty = 10 + self.monster.level

        if flee_roll >= difficulty:
            print_success("✓ Udaje ci się uciec!")
            return True
        else:
            print_error("✗ Nie udało ci się uciec!")
            # Potwór dostaje darmowy atak
            print_warning("Potwór wykorzystuje okazję!")
            self.monster_turn()
            return False

    def victory(self):
        """Gracz wygrywa walkę."""
        print_separator("*")
        print(colored_text(f"⭐ ZWYCIĘSTWO! ⭐", 'green'))
        print(f"Pokonałeś {self.monster.name}!")

        # Nagroda XP
        print(f"\n+ {self.monster.xp_reward} XP")
        leveled_up = self.player.add_xp(self.monster.xp_reward)

        if leveled_up:
            print_separator("*")
            print(colored_text(f"🌟 AWANS NA POZIOM {self.player.level}! 🌟", 'yellow'))
            print(f"Twoje zdrowie zostało przywrócone!")
            print_separator("*")

        # Lup
        self.generate_loot()

        print_separator("*")
        press_enter()
        return True

    def defeat(self):
        """Gracz przegrywa walkę."""
        print_separator("*")
        print(colored_text("💀 PORAŻKA... 💀", 'red'))
        print(f"{self.monster.name} cię pokonał!")
        print("\nTracisz przytomność...")
        print_separator("*")
        press_enter()
        return False

    def generate_loot(self):
        """Generuje łup po walce."""
        import random

        if not self.monster.loot:
            return

        print("\n💰 Łup:")

        for loot_entry in self.monster.loot:
            # Format: "zloto:50-150" lub "miecz_elficki:20%"
            if isinstance(loot_entry, str):
                parts = loot_entry.split(':')
                item_id = parts[0]

                if item_id == 'zloto':
                    # Losowa ilość złota
                    if len(parts) > 1:
                        gold_range = parts[1].split('-')
                        gold = random.randint(int(gold_range[0]), int(gold_range[1]))
                    else:
                        gold = 10
                    self.player.gold += gold
                    print(f"  + {gold} złota")
                else:
                    # Przedmiot z szansą
                    chance = 100
                    if len(parts) > 1:
                        chance = int(parts[1].rstrip('%'))

                    if random.randint(1, 100) <= chance:
                        # Znajdź przedmiot
                        with open('data/items.json', 'r', encoding='utf-8') as f:
                            items_data = json.load(f)

                        for category in items_data.values():
                            if item_id in category:
                                item = category[item_id].copy()
                                self.player.add_item(item)
                                print(f"  + {item['nazwa']}")
                                break


def load_monster(monster_id):
    """
    Wczytuje potwora z danych.

    Args:
        monster_id: ID potwora

    Returns:
        Obiekt Monster
    """
    with open('data/monsters.json', 'r', encoding='utf-8') as f:
        monsters_data = json.load(f)

    # Szukaj w potworach
    if monster_id in monsters_data['potwory']:
        monster_data = monsters_data['potwory'][monster_id]
        return Monster(monster_id, monster_data)

    # Szukaj w bossach
    if 'bossowie' in monsters_data and monster_id in monsters_data['bossowie']:
        monster_data = monsters_data['bossowie'][monster_id]
        return Monster(monster_id, monster_data)

    return None
