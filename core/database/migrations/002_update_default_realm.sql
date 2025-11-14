-- 将用户表的默认境界从"炼气一层"更新为"凡人"
PRAGMA legacy_alter_table = ON;

-- 创建新表
CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    nickname TEXT,
    avatar TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    cultivation REAL DEFAULT 0,
    realm TEXT DEFAULT '凡人',
    talent TEXT,
    dao_name TEXT,
    sect_id INTEGER,
    sect_position TEXT,
    
    is_hermit BOOLEAN DEFAULT FALSE,
    is_in_closing BOOLEAN DEFAULT FALSE,
    closing_start_time TIMESTAMP,
    closing_duration INTEGER,
    deep_closing_end_time TIMESTAMP,
    
    last_closing_time TIMESTAMP,
    last_battle_time TIMESTAMP,
    last_sect_roll_call_time TIMESTAMP,
    
    total_closing_count INTEGER DEFAULT 0,
    total_battle_count INTEGER DEFAULT 0,
    total_battle_win_count INTEGER DEFAULT 0,
    total_exp_gained INTEGER DEFAULT 0
);

-- 复制数据，将原有的"炼气一层"境界保持不变，只更改默认值
INSERT INTO users_new SELECT * FROM users;

-- 删除旧表
DROP TABLE users;

-- 重命名新表
ALTER TABLE users_new RENAME TO users;

-- 重新创建索引
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_cultivation ON users(cultivation);