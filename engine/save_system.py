"""System zapisywania i wczytywania gry."""
import json
import os
from datetime import datetime
from engine.character import Character


class SaveSystem:
    """System zarządzania zapisami gry."""

    SAVE_DIR = 'saves'

    @staticmethod
    def ensure_save_dir():
        """Upewnia się, że katalog zapisów istnieje."""
        if not os.path.exists(SaveSystem.SAVE_DIR):
            os.makedirs(SaveSystem.SAVE_DIR)

    @staticmethod
    def save_game(character, save_name=None):
        """
        Zapisuje grę.

        Args:
            character: Postać do zapisania
            save_name: Nazwa zapisu (opcjonalnie)

        Returns:
            Ścieżka do pliku zapisu
        """
        SaveSystem.ensure_save_dir()

        if save_name is None:
            # Automatyczna nazwa z datą i czasem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"save_{timestamp}"

        # Dodaj rozszerzenie jeśli nie ma
        if not save_name.endswith('.json'):
            save_name += '.json'

        save_path = os.path.join(SaveSystem.SAVE_DIR, save_name)

        # Przygotuj dane do zapisu
        save_data = {
            'version': '1.0',
            'saved_at': datetime.now().isoformat(),
            'character': character.to_dict()
        }

        # Zapisz do pliku
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        return save_path

    @staticmethod
    def load_game(save_name):
        """
        Wczytuje grę.

        Args:
            save_name: Nazwa zapisu

        Returns:
            Obiekt postaci lub None jeśli błąd
        """
        # Dodaj rozszerzenie jeśli nie ma
        if not save_name.endswith('.json'):
            save_name += '.json'

        save_path = os.path.join(SaveSystem.SAVE_DIR, save_name)

        if not os.path.exists(save_path):
            return None

        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            # Wczytaj postać
            character = Character.from_dict(save_data['character'])
            return character

        except Exception as e:
            print(f"Błąd wczytywania zapisu: {e}")
            return None

    @staticmethod
    def list_saves():
        """
        Listuje wszystkie dostępne zapisy.

        Returns:
            Lista nazw zapisów
        """
        SaveSystem.ensure_save_dir()

        saves = []
        for filename in os.listdir(SaveSystem.SAVE_DIR):
            if filename.endswith('.json'):
                save_path = os.path.join(SaveSystem.SAVE_DIR, filename)
                try:
                    with open(save_path, 'r', encoding='utf-8') as f:
                        save_data = json.load(f)

                    saves.append({
                        'filename': filename,
                        'character_name': save_data['character']['name'],
                        'level': save_data['character']['level'],
                        'class': save_data['character']['character_class'],
                        'saved_at': save_data.get('saved_at', 'Unknown')
                    })
                except:
                    # Pomiń uszkodzone zapisy
                    continue

        # Sortuj po dacie (najnowsze pierwsze)
        saves.sort(key=lambda x: x['saved_at'], reverse=True)
        return saves

    @staticmethod
    def delete_save(save_name):
        """
        Usuwa zapis.

        Args:
            save_name: Nazwa zapisu

        Returns:
            True jeśli udało się usunąć
        """
        if not save_name.endswith('.json'):
            save_name += '.json'

        save_path = os.path.join(SaveSystem.SAVE_DIR, save_name)

        if os.path.exists(save_path):
            try:
                os.remove(save_path)
                return True
            except:
                return False
        return False

    @staticmethod
    def quick_save(character):
        """
        Szybki zapis (nadpisuje quicksave.json).

        Args:
            character: Postać do zapisania

        Returns:
            Ścieżka do pliku zapisu
        """
        return SaveSystem.save_game(character, 'quicksave.json')

    @staticmethod
    def quick_load():
        """
        Szybkie wczytanie (wczytuje quicksave.json).

        Returns:
            Obiekt postaci lub None
        """
        return SaveSystem.load_game('quicksave.json')

    @staticmethod
    def auto_save(character):
        """
        Automatyczny zapis.

        Args:
            character: Postać do zapisania

        Returns:
            Ścieżka do pliku zapisu
        """
        return SaveSystem.save_game(character, 'autosave.json')
