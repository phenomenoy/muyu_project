"""
木鱼点击计数器 - Flask 后端
功能：
- 连接 MySQL 数据库
- 提供主页路由，显示初始计数
- 提供 API 路由，处理点击事件
"""

from flask import Flask, render_template, jsonify, request
import mysql.connector
from mysql.connector import Error
import logging
import os
from datetime import datetime

# 配置日志（便于调试）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========================================
# MySQL 配置 - 可被环境变量覆盖
# 环境变量：DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_AUTH_PLUGIN
# ========================================
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),        # MySQL 主机
    'user': os.getenv('DB_USER', 'root'),             # MySQL 用户名
    'password': os.getenv('DB_PASSWORD', '123456'),   # ⚠️ 修改为你的密码或通过环境变量设置
    'database': os.getenv('DB_NAME', 'muyu_db'),      # 数据库名
    'port': int(os.getenv('DB_PORT', '3306')),        # MySQL 默认端口
    'charset': 'utf8mb4'                              # 支持中文
}
# 可选认证插件（仅当你的实例需要时设置），例如 mysql_native_password / caching_sha2_password
DB_AUTH_PLUGIN = os.getenv('DB_AUTH_PLUGIN')  # None 表示不显式设置

# ========================================
# 数据库操作函数
# ========================================

def _connect_raw(include_database: bool = True):
    """底层连接封装，可选择是否包含 database 参数，以及可选 auth_plugin。"""
    connect_kwargs = {
        'host': db_config['host'],
        'user': db_config['user'],
        'password': db_config['password'],
        'port': db_config['port'],
        'charset': db_config['charset']
    }
    if include_database:
        connect_kwargs['database'] = db_config['database']
    if DB_AUTH_PLUGIN:
        connect_kwargs['auth_plugin'] = DB_AUTH_PLUGIN
    return mysql.connector.connect(**connect_kwargs)


def ensure_schema():
    """确保数据库与表、初始行存在。需要账户具备相应权限。"""
    try:
        # 先连接到服务器（不指定数据库），以便创建数据库
        server_conn = _connect_raw(include_database=False)
        cursor = server_conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        server_conn.commit()
        cursor.close()
        server_conn.close()
    except Error as e:
        # 若失败，多数是权限不足或认证失败；记录但不中断，让后续连接报错信息更具体
        logger.warning(f"确保数据库存在时出错（可忽略）：{e}")

    try:
        # 连接指定数据库，创建表与初始数据
        database_conn = _connect_raw(include_database=True)
        cursor = database_conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS counter (
                id INT PRIMARY KEY,
                clicks INT NOT NULL DEFAULT 0
            )
            """
        )
        database_conn.commit()
        cursor.execute(
            """
            INSERT INTO counter (id, clicks) VALUES (1, 0)
            ON DUPLICATE KEY UPDATE clicks = clicks
            """
        )
        database_conn.commit()
        cursor.close()
        database_conn.close()
        logger.info("数据库/数据表/初始数据检查完成")
    except Error as e:
        logger.warning(f"确保表与初始数据时出错（可忽略）：{e}")


def get_db_connection():
    """创建数据库连接，必要时尝试确保库表存在。"""
    try:
        ensure_schema()
    except Exception as e:
        # 不中断，让后续连接给出更明确错误
        logger.debug(f"ensure_schema 调用异常：{e}")
    try:
        connection = _connect_raw(include_database=True)
        if connection.is_connected():
            logger.info("成功连接到 MySQL 数据库")
            return connection
    except Error as e:
        logger.error(f"数据库连接失败: {e}")
        return None


def get_clicks():
    """获取当前点击计数"""
    connection = get_db_connection()
    if not connection:
        return 0
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT clicks FROM counter WHERE id = 1")
        result = cursor.fetchone()
        clicks = result[0] if result else 0
        logger.info(f"查询到点击数: {clicks}")
        return clicks
    except Error as e:
        logger.error(f"查询失败: {e}")
        return 0
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def update_clicks():
    """增加点击计数"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE counter SET clicks = clicks + 1 WHERE id = 1")
        connection.commit()
        logger.info("点击计数更新成功")
        return True
    except Error as e:
        logger.error(f"更新失败: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ========================================
# Flask 路由
# ========================================

@app.route('/')
def index():
    """主页路由 - 渲染 HTML 页面"""
    clicks = get_clicks()
    logger.info(f"主页加载，当前点击数: {clicks}")
    return render_template('index.html', clicks=clicks)

@app.route('/click', methods=['POST'])
def click_handler():
    """点击 API - 处理木鱼点击事件"""
    logger.info("收到点击请求")
    
    success = update_clicks()
    if not success:
        return jsonify({'error': '更新计数失败'}), 500
    
    new_clicks = get_clicks()
    response = {
        'success': True,
        'clicks': new_clicks,
        'message': f'已敲击 {new_clicks} 次'
    }
    
    logger.info(f"点击处理完成，新计数: {new_clicks}")
    return jsonify(response)

@app.route('/health')
def health_check():
    """健康检查接口"""
    connection = get_db_connection()
    db_status = "OK" if connection else "Failed"
    if connection and connection.is_connected():
        connection.close()
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

# ========================================
# 启动应用
# ========================================
if __name__ == '__main__':
    logger.info("启动木鱼计数器应用...")
    logger.info(f"数据库配置: {db_config['host']}:{db_config.get('port', 3306)} -> db={db_config.get('database')}")
    app.run(
        debug=True,          # 开发模式，自动重载
        host='127.0.0.1',    # 本地地址
        port=5000            # 端口号
    )