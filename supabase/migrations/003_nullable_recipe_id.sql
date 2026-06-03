-- Allow shopping lists without a recipe_id (for AI-generated recipes)
ALTER TABLE shopping_lists ALTER COLUMN recipe_id DROP NOT NULL;
