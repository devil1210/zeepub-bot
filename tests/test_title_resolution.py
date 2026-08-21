import unittest

from utils.metadata_utils import (
    is_romaji_string,
    is_spanish_string,
    resolve_title_cascade,
)


class TestTitleResolution(unittest.TestCase):
    def test_is_spanish_string(self):
        # Explicit Spanish titles with accents and common words
        self.assertTrue(
            is_spanish_string(
                "Las Chicas del Departamento de Artes Escénicas no me Dejan en Paz, Siendo yo solo un Chico Común y Corriente"
            )
        )
        self.assertTrue(
            is_spanish_string("La Mazmorra Oculta en la que Solo Yo Puedo Entrar")
        )
        self.assertTrue(is_spanish_string("El Héroe del Escudo y su Aventura"))
        # Romaji / English strings should NOT be marked as Spanish
        self.assertFalse(is_spanish_string("Ore dake Haireru Kakushi Dungeon"))
        self.assertFalse(
            is_spanish_string(
                "The Girls in The Entertainment Department Won't Let me, an Ordinary Person, Escape"
            )
        )
        self.assertFalse(is_spanish_string("Sword Art Online"))
        self.assertFalse(is_spanish_string(""))
        self.assertFalse(is_spanish_string(None))

    def test_is_romaji_string(self):
        # Romaji strings
        self.assertTrue(is_romaji_string("Ore dake Haireru Kakushi Dungeon"))
        self.assertTrue(is_romaji_string("Kusuriya no Hitorigoto"))
        self.assertTrue(is_romaji_string("Mushoku Tensei: Isekai Ittara Honki Dasu"))
        self.assertTrue(is_romaji_string("Jaku-Chara Tomozaki-kun"))
        self.assertTrue(
            is_romaji_string("ダンジョンに出会いを求めるのは間違っているだろうか")
        )

        # Spanish titles must NEVER be marked as Romaji even if they contain words like "de" or "no"
        self.assertFalse(
            is_romaji_string(
                "Las Chicas del Departamento de Artes Escénicas no me Dejan en Paz, Siendo yo solo un Chico Común y Corriente"
            )
        )
        self.assertFalse(
            is_romaji_string("No me gusta la comida picante de mi hermana")
        )
        self.assertFalse(is_romaji_string("The Hidden Dungeon Only I Can Enter"))
        self.assertFalse(is_romaji_string(""))
        self.assertFalse(is_romaji_string(None))

    def test_resolve_title_cascade_spanish_trapped_in_romaji(self):
        # Case where Spanish title was stored in romaji_title field
        data = {
            "english_title": "The Girls in The Entertainment Department Won't Let me, an Ordinary Person, Escape",
            "romaji_title": "Las Chicas del Departamento de Artes Escénicas no me Dejan en Paz, Siendo yo solo un Chico Común y Corriente",
            "spanish_title": None,
        }
        t_en, t_jp, t_es = resolve_title_cascade(data)
        self.assertEqual(
            t_en,
            "The Girls in The Entertainment Department Won't Let me, an Ordinary Person, Escape",
        )
        self.assertIsNone(t_jp)
        self.assertEqual(
            t_es,
            "Las Chicas del Departamento de Artes Escénicas no me Dejan en Paz, Siendo yo solo un Chico Común y Corriente",
        )

    def test_resolve_title_cascade_three_distinct_titles(self):
        data = {
            "english_title": "The Hidden Dungeon Only I Can Enter",
            "romaji_title": "Ore dake Haireru Kakushi Dungeon",
            "spanish_title": "La Mazmorra Oculta en la que Solo Yo Puedo Entrar",
        }
        t_en, t_jp, t_es = resolve_title_cascade(data)
        self.assertEqual(t_en, "The Hidden Dungeon Only I Can Enter")
        self.assertEqual(t_jp, "Ore dake Haireru Kakushi Dungeon")
        self.assertEqual(t_es, "La Mazmorra Oculta en la que Solo Yo Puedo Entrar")

    def test_resolve_title_cascade_identical_titles_deduplication(self):
        data = {
            "english_title": "Sword Art Online",
            "romaji_title": "Sword Art Online",
            "spanish_title": "Sword Art Online",
        }
        t_en, t_jp, t_es = resolve_title_cascade(data)
        self.assertEqual(t_en, "Sword Art Online")
        self.assertIsNone(t_jp)
        self.assertIsNone(t_es)


if __name__ == "__main__":
    unittest.main()
