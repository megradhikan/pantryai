import unittest

from services.recipe_matching import ingredient_matches, match_recipes


class RecipeMatchingTests(unittest.TestCase):
    def test_matches_plural_compound_and_minor_typo(self):
        self.assertTrue(ingredient_matches("tomatoes", "tomato"))
        self.assertTrue(ingredient_matches("chicken breast", "chicken"))
        self.assertTrue(ingredient_matches("broccoli", "brocolli"))
        self.assertFalse(ingredient_matches("rice", "spice"))

    def test_scores_required_ingredients_and_prioritizes_expiring_items(self):
        inventory = [
            {"name": "Eggs", "status": "fresh"},
            {"name": "Milk", "status": "expiring_soon"},
        ]
        recipes = [
            {
                "id": "eggs-only",
                "title": "Eggs Only",
                "ingredients": [
                    {"name": "eggs", "quantity": 2, "unit": "count", "required": True}
                ],
            },
            {
                "id": "milk-only",
                "title": "Milk Only",
                "ingredients": [
                    {"name": "milk", "quantity": 1, "unit": "cup", "required": True}
                ],
            },
            {
                "id": "pancakes",
                "title": "Pancakes",
                "ingredients": [
                    {"name": "eggs", "quantity": 1, "unit": "count", "required": True},
                    {"name": "flour", "quantity": 1, "unit": "cup", "required": True},
                ],
            },
        ]

        suggestions = match_recipes(inventory, recipes)

        self.assertEqual(suggestions[0]["recipe_id"], "milk-only")
        self.assertEqual(suggestions[0]["match_score"], 1.0)
        self.assertEqual(suggestions[2]["match_score"], 0.5)
        self.assertEqual(suggestions[2]["missing_ingredients"][0]["name"], "flour")

    def test_returns_no_matches_without_active_inventory(self):
        inventory = [{"name": "Milk", "status": "expired"}]
        self.assertEqual(match_recipes(inventory, []), [])


if __name__ == "__main__":
    unittest.main()
