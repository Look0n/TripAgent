CREATE TABLE IF NOT EXISTS checklist_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    item_type TEXT NOT NULL,
    category TEXT,
    description TEXT,
    priority TEXT,
    is_completed INTEGER NOT NULL DEFAULT 0
);
