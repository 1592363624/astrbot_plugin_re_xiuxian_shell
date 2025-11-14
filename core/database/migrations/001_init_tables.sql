-- 修仙插件初始数据库表结构

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,           -- 平台用户ID
    nickname TEXT,                          -- 昵称
    avatar TEXT,                            -- 头像URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 修仙基本属性
    cultivation REAL DEFAULT 0,             -- 修为点数
    realm TEXT DEFAULT '炼气一层',          -- 修仙境界
    talent TEXT,                            -- 灵根
    dao_name TEXT,                          -- 道号
    sect_id INTEGER,                        -- 宗门ID
    sect_position TEXT,                     -- 宗门职位
    
    -- 状态
    is_hermit BOOLEAN DEFAULT FALSE,        -- 是否处于避世状态
    is_in_closing BOOLEAN DEFAULT FALSE,    -- 是否正在闭关
    closing_start_time TIMESTAMP,           -- 闭关开始时间
    closing_duration INTEGER,               -- 闭关时长(秒)
    deep_closing_end_time TIMESTAMP,        -- 深度闭关结束时间
    
    -- 冷却时间
    last_closing_time TIMESTAMP,            -- 上次闭关时间
    last_battle_time TIMESTAMP,             -- 上次斗法时间
    last_sect_roll_call_time TIMESTAMP,     -- 上次宗门点卯时间
    
    -- 统计数据
    total_closing_count INTEGER DEFAULT 0,  -- 总闭关次数
    total_battle_count INTEGER DEFAULT 0,   -- 总斗法次数
    total_battle_win_count INTEGER DEFAULT 0, -- 总斗法胜利次数
    total_exp_gained INTEGER DEFAULT 0      -- 总获得修为
);

-- 物品模板表
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,              -- 物品名称
    type TEXT NOT NULL,                     -- 物品类型 (丹药/法宝/材料等)
    description TEXT,                       -- 描述
    rarity INTEGER DEFAULT 1,               -- 稀有度 (1-5)
    effect TEXT,                            -- 效果描述
    effect_type TEXT,                       -- 效果类型
    effect_value REAL,                      -- 效果数值
    requirement TEXT,                       -- 使用要求
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户物品库存表
CREATE TABLE IF NOT EXISTS user_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);

-- 宗门表
CREATE TABLE IF NOT EXISTS sects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,              -- 宗门名称
    description TEXT,                       -- 宗门描述
    founder_id TEXT,                        -- 创始人ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    member_count INTEGER DEFAULT 1,         -- 成员数量
    contribution REAL DEFAULT 0,            -- 宗门贡献
    is_active BOOLEAN DEFAULT TRUE          -- 是否激活
);

-- 用户宗门贡献表
CREATE TABLE IF NOT EXISTS user_sect_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    sect_id INTEGER NOT NULL,
    contribution REAL DEFAULT 0,            -- 对该宗门的贡献
    last_contribution_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (sect_id) REFERENCES sects(id),
    UNIQUE(user_id, sect_id)
);

-- 日志表
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,                     -- 日志类型 (闭关/斗法/宗门等)
    content TEXT NOT NULL,                  -- 日志内容
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 迁移记录表
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);