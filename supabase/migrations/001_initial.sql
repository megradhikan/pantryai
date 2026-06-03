-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Profiles (extends Supabase auth.users)
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id) VALUES (NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Receipts
CREATE TABLE receipts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  storage_path TEXT NOT NULL,
  raw_ocr_text TEXT,
  store_name TEXT,
  purchase_date DATE NOT NULL,
  extracted_items JSONB,
  extraction_metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inventory
CREATE TABLE inventory_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  quantity NUMERIC NOT NULL DEFAULT 1,
  unit TEXT,
  purchase_date DATE NOT NULL,
  estimated_expiry DATE NOT NULL,
  is_finished BOOLEAN NOT NULL DEFAULT FALSE,
  receipt_id UUID REFERENCES receipts(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recipes (RAG corpus, seeded once)
CREATE TABLE recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  ingredients JSONB NOT NULL,
  instructions TEXT NOT NULL,
  cuisine TEXT,
  prep_time_mins INT,
  embedding VECTOR(384) NOT NULL
);

CREATE INDEX ON recipes USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 10);

-- Shopping Lists
CREATE TABLE shopping_lists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  recipe_id UUID NOT NULL REFERENCES recipes(id),
  recipe_title TEXT NOT NULL,
  items JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Push Subscriptions
CREATE TABLE push_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  endpoint TEXT NOT NULL UNIQUE,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Eval: recipe suggestion log
CREATE TABLE recipe_suggestion_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  suggested_recipe_ids JSONB NOT NULL,
  avg_match_score NUMERIC,
  led_to_shopping_list BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- pgvector cosine similarity search function
CREATE OR REPLACE FUNCTION match_recipes(query_embedding VECTOR(384), match_count INT)
RETURNS TABLE (
  id UUID,
  title TEXT,
  ingredients JSONB,
  instructions TEXT,
  cuisine TEXT,
  prep_time_mins INT,
  similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
  SELECT id, title, ingredients, instructions, cuisine, prep_time_mins,
    1 - (embedding <=> query_embedding) AS similarity
  FROM recipes
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
