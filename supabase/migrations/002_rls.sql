-- Enable RLS on all user-data tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE shopping_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipe_suggestion_log ENABLE ROW LEVEL SECURITY;

-- recipes is a shared read-only corpus — no user_id column, RLS not needed

-- profiles
CREATE POLICY "profiles_select_own" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "profiles_update_own" ON profiles FOR UPDATE USING (auth.uid() = id);

-- receipts
CREATE POLICY "receipts_select_own" ON receipts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "receipts_insert_own" ON receipts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "receipts_update_own" ON receipts FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "receipts_delete_own" ON receipts FOR DELETE USING (auth.uid() = user_id);

-- inventory_items
CREATE POLICY "inventory_select_own" ON inventory_items FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "inventory_insert_own" ON inventory_items FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "inventory_update_own" ON inventory_items FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "inventory_delete_own" ON inventory_items FOR DELETE USING (auth.uid() = user_id);

-- shopping_lists
CREATE POLICY "shopping_select_own" ON shopping_lists FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "shopping_insert_own" ON shopping_lists FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "shopping_update_own" ON shopping_lists FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "shopping_delete_own" ON shopping_lists FOR DELETE USING (auth.uid() = user_id);

-- push_subscriptions
CREATE POLICY "push_select_own" ON push_subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "push_insert_own" ON push_subscriptions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "push_delete_own" ON push_subscriptions FOR DELETE USING (auth.uid() = user_id);

-- recipe_suggestion_log
CREATE POLICY "log_select_own" ON recipe_suggestion_log FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "log_insert_own" ON recipe_suggestion_log FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Verify RLS is active (run after applying this migration):
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- AND tablename IN (
--   'profiles','receipts','inventory_items',
--   'shopping_lists','push_subscriptions','recipe_suggestion_log'
-- );
-- All rows should show rowsecurity = true
