-- SQL 测试文件

-- 创建表
CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建另一个表
CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT NOT NULL,
    total DECIMAL(10, 2),
    status VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建视图
CREATE VIEW user_orders AS
SELECT u.username, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.username;

-- 创建函数
CREATE FUNCTION get_total_orders(user_id INT)
RETURNS INT
AS $$
BEGIN
    RETURN COUNT(*) FROM orders WHERE user_id = $1;
END;
$$ LANGUAGE plpgsql;

-- 创建存储过程
CREATE PROCEDURE create_user(
    p_username VARCHAR,
    p_email VARCHAR
)
AS $$
BEGIN
    INSERT INTO users (username, email) VALUES (p_username, p_email);
END;
$$ LANGUAGE plpgsql;
