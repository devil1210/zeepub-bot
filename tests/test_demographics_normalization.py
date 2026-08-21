import unittest

from utils.helpers import (
    CANONICAL_DEMOGRAPHICS,
    is_demographic_tag,
    normalize_demographics_list,
    normalize_demography,
)
from utils.template_engine import apply_publication_template, extract_demography


class TestDemographicsNormalization(unittest.TestCase):
    def test_canonical_demographics(self):
        self.assertIn("Shounen", CANONICAL_DEMOGRAPHICS)
        self.assertIn("Seinen", CANONICAL_DEMOGRAPHICS)
        self.assertIn("Shoujo", CANONICAL_DEMOGRAPHICS)
        self.assertIn("Josei", CANONICAL_DEMOGRAPHICS)
        self.assertIn("Kodomo", CANONICAL_DEMOGRAPHICS)

    def test_normalize_demography_single(self):
        self.assertEqual(normalize_demography("Chicos/shounen"), "Shounen")
        self.assertEqual(normalize_demography("Adultos/Seinen"), "Seinen")
        self.assertEqual(normalize_demography("Chicas/shoujo"), "Shoujo")
        self.assertEqual(normalize_demography("Mujeres/josei"), "Josei")
        self.assertEqual(normalize_demography("Niños/kodomo"), "Kodomo")
        self.assertEqual(normalize_demography("shonen"), "Shounen")
        self.assertEqual(normalize_demography("Shônen"), "Shounen")
        self.assertEqual(normalize_demography("seinen"), "Seinen")
        self.assertEqual(normalize_demography("shoujo"), "Shoujo")
        self.assertEqual(normalize_demography("josei"), "Josei")

    def test_normalize_demography_multiple_prevents_duplication(self):
        # When multiple demographics are present, exactly ONE canonical demographic is returned
        self.assertEqual(normalize_demography(["Chicos/shounen", "Adultos/Seinen"]), "Shounen")
        self.assertEqual(normalize_demography(["Adultos/Seinen", "Chicos/shounen"]), "Seinen")
        self.assertEqual(normalize_demography(["Misterio", "Comedia", "Chicos/shounen"]), "Shounen")

    def test_normalize_demography_empty(self):
        self.assertEqual(normalize_demography(None), "")
        self.assertEqual(normalize_demography([]), "")
        self.assertEqual(normalize_demography(""), "")
        self.assertEqual(normalize_demography(["Acción", "Aventura"]), "")

    def test_normalize_demographics_list(self):
        self.assertEqual(normalize_demographics_list(["Chicos/shounen", "Adultos/Seinen"]), ["Shounen"])
        self.assertEqual(normalize_demographics_list("Adultos/Seinen"), ["Seinen"])
        self.assertEqual(normalize_demographics_list(None), [])
        self.assertEqual(normalize_demographics_list([]), [])

    def test_is_demographic_tag(self):
        self.assertTrue(is_demographic_tag("Chicos/shounen"))
        self.assertTrue(is_demographic_tag("Adultos/Seinen"))
        self.assertTrue(is_demographic_tag("Seinen"))
        self.assertFalse(is_demographic_tag("Acción"))
        self.assertFalse(is_demographic_tag("Misterio"))
        self.assertFalse(is_demographic_tag(""))
        self.assertFalse(is_demographic_tag(None))

    def test_extract_demography(self):
        tags = ["Fantasía", "Acción", "Chicos/shounen", "Adultos/Seinen"]
        self.assertEqual(extract_demography(tags), "Shounen")

    def test_template_engine_single_demography(self):
        template = "[?demography]👥 <b>Demografía:</b> {demography}[/?]"
        data = {
            "demographics": ["Chicos/shounen", "Adultos/Seinen"],
            "tags": ["Fantasía", "Acción"],
        }
        rendered = apply_publication_template(template, data)
        self.assertEqual(rendered, "👥 <b>Demografía:</b> Shounen")
        self.assertNotIn("Adultos/Seinen", rendered)
        self.assertNotIn(",", rendered)


if __name__ == "__main__":
    unittest.main()
