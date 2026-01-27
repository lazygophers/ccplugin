-- SQL 测试文件 - 包含表、索引、视图、存储过程、触发器

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户资料表
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    bio TEXT,
    avatar_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 会话表
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文章表
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 评论表
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_comments_post_id ON comments(post_id);

-- 创建视图：用户及其文章统计
CREATE VIEW user_post_stats AS
SELECT
    u.id,
    u.username,
    u.email,
    COUNT(p.id) as post_count,
    SUM(p.view_count) as total_views
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id, u.username, u.email;

-- 存储过程：创建用户
CREATE OR REPLACE FUNCTION create_user(
    p_username VARCHAR(50),
    p_email VARCHAR(100),
    p_password_hash VARCHAR(255)
) RETURNS INTEGER AS $$
DECLARE
    v_user_id INTEGER;
BEGIN
    INSERT INTO users (username, email, password_hash)
    VALUES (p_username, p_email, p_password_hash)
    RETURNING id INTO v_user_id;

    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql;

-- 存储过程：创建会话
CREATE OR REPLACE FUNCTION create_session(
    p_user_id INTEGER,
    p_token VARCHAR(255),
    p_expires_in INTERVAL DEFAULT INTERVAL '24 hours'
) RETURNS INTEGER AS $$
DECLARE
    v_session_id INTEGER;
BEGIN
    INSERT INTO sessions (user_id, token, expires_at)
    VALUES (p_user_id, p_token, CURRENT_TIMESTAMP + p_expires_in)
    RETURNING id INTO v_session_id;

    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql;

-- 函数：检查会话是否有效
CREATE OR REPLACE FUNCTION is_session_valid(p_token VARCHAR(255))
RETURNS BOOLEAN AS $$
DECLARE
    v_is_valid BOOLEAN;
BEGIN
    SELECT expires_at > CURRENT_TIMESTAMP
    INTO v_is_valid
    FROM sessions
    WHERE token = p_token;

    RETURN COALESCE(v_is_valid, FALSE);
END;
$$ LANGUAGE plpgsql;

-- 触发器：更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_posts_updated_at
    BEFORE UPDATE ON posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 触发器：增加文章浏览次数
CREATE OR REPLACE FUNCTION increment_post_view_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE posts
    SET view_count = view_count + 1
    WHERE id = NEW.post_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_views_on_comment
    AFTER INSERT ON comments
    FOR EACH ROW
    EXECUTE FUNCTION increment_post_view_count();

-- 事务示例：创建用户并创建默认文章
BEGIN;

DO $$
DECLARE
    v_user_id INTEGER;
BEGIN
    -- 创建用户
    v_user_id := create_user('johndoe', 'john@example.com', 'hash_here');

    -- 创建用户资料
    INSERT INTO user_profiles (user_id, first_name, last_name)
    VALUES (v_user_id, 'John', 'Doe');

    -- 创建默认文章
    INSERT INTO posts (user_id, title, content, status)
    VALUES (
        v_user_id,
        'Welcome to my blog',
        'This is my first post!',
        'published'
    );

    RAISE NOTICE 'User created with ID: %', v_user_id;
END $$;

COMMIT;

-- 复杂查询示例：获取热门文章及其作者信息
SELECT
    p.id,
    p.title,
    p.content,
    p.view_count,
    u.username as author_name,
    u.email as author_email,
    COUNT(c.id) as comment_count,
    COUNT(DISTINCT c.user_id) as unique_commenters
FROM posts p
JOIN users u ON p.user_id = u.id
LEFT JOIN comments c ON p.id = c.post_id
WHERE p.status = 'published'
GROUP BY p.id, p.title, p.content, p.view_count, u.username, u.email
ORDER BY p.view_count DESC
LIMIT 10;

-- CTE (Common Table Expression) 示例
WITH user_stats AS (
    SELECT
        user_id,
        COUNT(*) as post_count,
        SUM(view_count) as total_views
    FROM posts
    WHERE status = 'published'
    GROUP BY user_id
)
SELECT
    u.username,
    COALESCE(us.post_count, 0) as post_count,
    COALESCE(us.total_views, 0) as total_views
FROM users u
LEFT JOIN user_stats us ON u.id = us.user_id
ORDER BY total_views DESC;

-- 窗口函数示例：获取用户文章排名
SELECT
    username,
    title,
    view_count,
    RANK() OVER (PARTITION BY user_id ORDER BY view_count DESC) as rank_in_user_posts,
    ROW_NUMBER() OVER (ORDER BY view_count DESC) as overall_rank
FROM posts p
JOIN users u ON p.user_id = u.id
WHERE status = 'published';
