"""System handlu i reputacji handlowej."""

import json
import random
from utils.display import (print_separator, colored_text, print_success,
                           print_error, print_warning, press_enter)


class TradingSystem:
    """Klasa zarządzająca handlem i reputacją."""

    def __init__(self):
        """Inicjalizuje system handlu."""
        self.reputation = {}  # {merchant_id: reputation_level}
        self.price_modifiers = {}  # {item_id: price_modifier}
        self.last_trades = {}  # {merchant_id: [item_ids]}

    def get_reputation_with_merchant(self, player, merchant_id):
        """
        Pobiera reputację gracza u kupca.

        Args:
            player: Postać gracza
            merchant_id: ID kupca

        Returns:
            int: Poziom reputacji (0-100)
        """
        if not hasattr(player, 'merchant_reputation'):
            player.merchant_reputation = {}
        return player.merchant_reputation.get(merchant_id, 50)  # Start z 50

    def modify_reputation(self, player, merchant_id, change):
        """
        Modyfikuje reputację gracza u kupca.

        Args:
            player: Postać gracza
            merchant_id: ID kupca
            change: Zmiana reputacji (może być ujemna)
        """
        if not hasattr(player, 'merchant_reputation'):
            player.merchant_reputation = {}

        current = player.merchant_reputation.get(merchant_id, 50)
        new_rep = max(0, min(100, current + change))
        player.merchant_reputation[merchant_id] = new_rep

        # Informuj gracza o zmianie
        if change > 0:
            print_success(f"\n📈 Twoja reputacja u {merchant_id} wzrosła! ({current} → {new_rep})")
        elif change < 0:
            print_warning(f"\n📉 Twoja reputacja u {merchant_id} spadła! ({current} → {new_rep})")

    def get_reputation_tier(self, reputation):
        """
        Zwraca tier reputacji.

        Args:
            reputation: Poziom reputacji (0-100)

        Returns:
            str: Nazwa tier'a
        """
        if reputation >= 90:
            return "Legendarny"
        elif reputation >= 75:
            return "Zaufany"
        elif reputation >= 60:
            return "Przyjazny"
        elif reputation >= 40:
            return "Neutralny"
        elif reputation >= 25:
            return "Nieufny"
        else:
            return "Wrogi"

    def get_price_modifier(self, player, merchant_id, item, selling=False):
        """
        Oblicza modyfikator ceny bazując na reputacji.

        Args:
            player: Postać gracza
            merchant_id: ID kupca
            item: Przedmiot
            selling: Czy gracz sprzedaje (True) czy kupuje (False)

        Returns:
            float: Modyfikator ceny (np. 0.9 = 10% taniej)
        """
        reputation = self.get_reputation_with_merchant(player, merchant_id)

        # Bazowy modyfikator z reputacji
        if reputation >= 90:
            rep_modifier = 0.7 if not selling else 1.3  # 30% taniej/drożej
        elif reputation >= 75:
            rep_modifier = 0.8 if not selling else 1.2  # 20% taniej/drożej
        elif reputation >= 60:
            rep_modifier = 0.9 if not selling else 1.1  # 10% taniej/drożej
        elif reputation >= 40:
            rep_modifier = 1.0  # Normalna cena
        elif reputation >= 25:
            rep_modifier = 1.1 if not selling else 0.9  # 10% drożej/taniej
        else:
            rep_modifier = 1.3 if not selling else 0.7  # 30% drożej/taniej

        # Modyfikator z rzadkości przedmiotu
        rarity = item.get('rzadkosc', 'common')
        rarity_mods = {
            'common': 1.0,
            'uncommon': 1.2,
            'rare': 1.5,
            'legendary': 2.0
        }
        rarity_modifier = rarity_mods.get(rarity, 1.0)

        # Losowa fluktuacja rynkowa (±10%)
        market_modifier = random.uniform(0.9, 1.1)

        # Końcowy modyfikator
        final_modifier = rep_modifier * market_modifier

        return final_modifier

    def show_trading_menu(self, player, merchant_id, merchant_data):
        """
        Pokazuje główne menu handlu.

        Args:
            player: Postać gracza
            merchant_id: ID kupca
            merchant_data: Dane kupca z JSON
        """
        reputation = self.get_reputation_with_merchant(player, merchant_id)
        tier = self.get_reputation_tier(reputation)

        while True:
            print_separator("=")
            print(f"💰 HANDEL: {merchant_data.get('nazwa', 'Kupiec')}")
            print_separator("=")
            print(f"Twoje złoto: {colored_text(str(player.gold), 'yellow')}")
            print(f"Reputacja: {colored_text(tier, 'cyan')} ({reputation}/100)")
            print_separator("-")

            options = [
                "Kup przedmioty",
                "Sprzedaj przedmioty",
                "Zobacz informacje o reputacji",
                "Zakończ handel"
            ]

            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")

            try:
                choice = int(input("\nWybór: "))
                if choice == 1:
                    self.buy_items_menu(player, merchant_id, merchant_data)
                elif choice == 2:
                    self.sell_items_menu(player, merchant_id, merchant_data)
                elif choice == 3:
                    self.show_reputation_info(player, merchant_id)
                    press_enter()
                elif choice == 4:
                    break
                else:
                    print_error("Nieprawidłowy wybór!")
            except ValueError:
                print_error("Wprowadź poprawną liczbę!")

    def buy_items_menu(self, player, merchant_id, merchant_data):
        """Menu kupowania przedmiotów."""
        asortyment = merchant_data.get('asortyment', [])

        if not asortyment:
            print_error("Ten handlarz nie ma nic do sprzedania.")
            press_enter()
            return

        # Wczytaj przedmioty
        with open('data/items.json', 'r', encoding='utf-8') as f:
            items_data = json.load(f)

        while True:
            print_separator("=")
            print(f"🛒 KUPOWANIE - {merchant_data.get('nazwa', 'Kupiec')}")
            print_separator("=")
            print(f"Twoje złoto: {colored_text(str(player.gold), 'yellow')}")
            print_separator("-")

            items = []
            for item_id in asortyment:
                for category in items_data.values():
                    if item_id in category:
                        item = category[item_id].copy()
                        item['id'] = item_id

                        # Oblicz cenę z modyfikatorem
                        base_price = item.get('wartosc', 100)
                        modifier = self.get_price_modifier(player, merchant_id, item, selling=False)
                        final_price = int(base_price * modifier)

                        item['final_price'] = final_price
                        items.append(item)
                        break

            print("\nDostępne przedmioty:")
            for i, item in enumerate(items, 1):
                base_price = item.get('wartosc', 100)
                final_price = item['final_price']

                # Pokaż różnicę ceny jeśli jest
                if final_price < base_price:
                    price_str = colored_text(f"{final_price}", 'green') + f" ({base_price})"
                elif final_price > base_price:
                    price_str = colored_text(f"{final_price}", 'red') + f" ({base_price})"
                else:
                    price_str = str(final_price)

                can_afford = "✓" if player.gold >= final_price else "✗"
                print(f"  {i}. [{can_afford}] {item['nazwa']} - {price_str} złota")

            print("  0. Wróć")

            try:
                choice = int(input("\nCo chcesz kupić? "))
                if choice == 0:
                    break
                if 1 <= choice <= len(items):
                    item = items[choice - 1]
                    final_price = item['final_price']

                    if player.gold >= final_price:
                        # Potwierdź zakup
                        confirm = input(f"\nKupić {item['nazwa']} za {final_price} złota? (t/n): ").strip().lower()
                        if confirm in ['t', 'tak']:
                            player.gold -= final_price
                            # Usuń zbędne pola przed dodaniem
                            item_to_add = item.copy()
                            del item_to_add['final_price']
                            player.add_item(item_to_add)

                            print_success(f"✓ Kupiono {item['nazwa']}!")

                            # Zwiększ reputację za handel
                            self.modify_reputation(player, merchant_id, 1)

                            press_enter()
                    else:
                        print_error("Nie masz wystarczająco złota!")
                        press_enter()
                else:
                    print_error("Nieprawidłowy wybór!")
                    press_enter()
            except ValueError:
                print_error("Wprowadź poprawną liczbę!")
                press_enter()

    def sell_items_menu(self, player, merchant_id, merchant_data):
        """Menu sprzedawania przedmiotów."""
        while True:
            print_separator("=")
            print(f"💵 SPRZEDAWANIE - {merchant_data.get('nazwa', 'Kupiec')}")
            print_separator("=")
            print(f"Twoje złoto: {colored_text(str(player.gold), 'yellow')}")
            print_separator("-")

            # Filtruj przedmioty które można sprzedać
            sellable_items = []
            for item in player.inventory:
                # Nie można sprzedać założonych przedmiotów
                if item in [player.equipped.get('bron'), player.equipped.get('zbroja'), player.equipped.get('tarcza')]:
                    continue
                # Nie można sprzedać materiałów bazowych (chyba że kupiec skupuje)
                if item.get('typ') == 'material':
                    continue

                sellable_items.append(item)

            if not sellable_items:
                print_error("Nie masz nic do sprzedania!")
                press_enter()
                return

            print("\nTwoje przedmioty:")
            for i, item in enumerate(sellable_items, 1):
                base_value = item.get('wartosc', 10)
                modifier = self.get_price_modifier(player, merchant_id, item, selling=True)
                sell_price = int(base_value * modifier)

                # Pokaż różnicę ceny
                if sell_price > base_value:
                    price_str = colored_text(f"{sell_price}", 'green') + f" ({base_value})"
                elif sell_price < base_value:
                    price_str = colored_text(f"{sell_price}", 'red') + f" ({base_value})"
                else:
                    price_str = str(sell_price)

                print(f"  {i}. {item['nazwa']} - {price_str} złota")

            print("  0. Wróć")

            try:
                choice = int(input("\nCo chcesz sprzedać? "))
                if choice == 0:
                    break
                if 1 <= choice <= len(sellable_items):
                    item = sellable_items[choice - 1]
                    base_value = item.get('wartosc', 10)
                    modifier = self.get_price_modifier(player, merchant_id, item, selling=True)
                    sell_price = int(base_value * modifier)

                    # Potwierdź sprzedaż
                    confirm = input(f"\nSprzedać {item['nazwa']} za {sell_price} złota? (t/n): ").strip().lower()
                    if confirm in ['t', 'tak']:
                        player.gold += sell_price
                        player.inventory.remove(item)

                        print_success(f"✓ Sprzedano {item['nazwa']} za {sell_price} złota!")

                        # Zwiększ reputację za handel
                        self.modify_reputation(player, merchant_id, 1)

                        press_enter()
                else:
                    print_error("Nieprawidłowy wybór!")
                    press_enter()
            except ValueError:
                print_error("Wprowadź poprawną liczbę!")
                press_enter()

    def show_reputation_info(self, player, merchant_id):
        """Pokazuje informacje o reputacji."""
        reputation = self.get_reputation_with_merchant(player, merchant_id)
        tier = self.get_reputation_tier(reputation)

        print_separator("=")
        print("📊 INFORMACJE O REPUTACJI")
        print_separator("=")

        print(f"\nAktualny poziom: {colored_text(tier, 'cyan')} ({reputation}/100)")
        print("\nBonusy na obecnym poziomie:")

        if reputation >= 90:
            print(colored_text("  • 30% zniżki przy kupnie", 'green'))
            print(colored_text("  • 30% więcej przy sprzedaży", 'green'))
        elif reputation >= 75:
            print(colored_text("  • 20% zniżki przy kupnie", 'green'))
            print(colored_text("  • 20% więcej przy sprzedaży", 'green'))
        elif reputation >= 60:
            print(colored_text("  • 10% zniżki przy kupnie", 'green'))
            print(colored_text("  • 10% więcej przy sprzedaży", 'green'))
        elif reputation >= 40:
            print("  • Normalne ceny")
        elif reputation >= 25:
            print(colored_text("  • 10% drożej przy kupnie", 'red'))
            print(colored_text("  • 10% mniej przy sprzedaży", 'red'))
        else:
            print(colored_text("  • 30% drożej przy kupnie", 'red'))
            print(colored_text("  • 30% mniej przy sprzedaży", 'red'))

        print("\nJak poprawić reputację:")
        print("  • Kupuj i sprzedawaj u kupca (+1 za każdą transakcję)")
        print("  • Wykonuj questy dla kupca (+5 za quest)")
        print("  • Nie kradnij i nie oszukuj (-20 za oszustwo)")
