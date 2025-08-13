import fcntl
import json
import os
import threading
from datetime import datetime
from typing import Dict, Optional

# 全局配置
SESSION_DIR = "_SESSION_DATA"
CONFIG_DIR = "config"

# 确保会话目录存在
os.makedirs(SESSION_DIR, exist_ok=True)

# 线程锁用于保护文件操作
file_locks = {}
lock_creation_lock = threading.Lock()


def get_file_lock(session_id: str) -> threading.Lock:
    """获取特定会话的文件锁"""
    with lock_creation_lock:
        if session_id not in file_locks:
            file_locks[session_id] = threading.Lock()
        return file_locks[session_id]


class SessionManager:
    """会话管理器"""

    @staticmethod
    def get_session_file(session_id: str) -> str:
        """获取会话文件路径，如果session已存在则使用现有路径，否则创建新路径"""
        # 首先尝试查找已存在的会话文件
        existing_file = SessionManager.find_session_file(session_id)
        if existing_file:
            return existing_file

        # 如果不存在，创建新的session目录
        # 获取当前日期
        current_date = datetime.now().strftime("%Y-%m-%d")
        # 获取当前时间戳（精确到毫秒）
        current_timestamp = datetime.now().strftime("%H%M%S_%f")[:-3]  # 精确到毫秒

        # 创建日期目录
        date_dir = os.path.join(SESSION_DIR, current_date)
        os.makedirs(date_dir, exist_ok=True)

        # 创建session目录
        session_dir = os.path.join(date_dir, f"{current_timestamp}_{session_id}")
        os.makedirs(session_dir, exist_ok=True)

        # 构建会话文件路径
        filename = "session.json"
        return os.path.join(session_dir, filename)

    @staticmethod
    def find_session_file(session_id: str) -> Optional[str]:
        """查找现有的会话文件路径"""
        # 遍历所有日期目录
        if not os.path.exists(SESSION_DIR):
            return None

        for date_dir in os.listdir(SESSION_DIR):
            date_path = os.path.join(SESSION_DIR, date_dir)
            if not os.path.isdir(date_path):
                continue

            # 在日期目录中查找匹配的session目录
            for session_dir_name in os.listdir(date_path):
                if session_dir_name.endswith(f"_{session_id}"):
                    session_dir_path = os.path.join(date_path, session_dir_name)
                    session_file = os.path.join(session_dir_path, "session.json")
                    if os.path.exists(session_file):
                        return session_file

        return None

    @staticmethod
    def get_session_dir(session_id: str) -> Optional[str]:
        """获取会话目录路径"""
        # 遍历所有日期目录
        if not os.path.exists(SESSION_DIR):
            return None

        for date_dir in os.listdir(SESSION_DIR):
            date_path = os.path.join(SESSION_DIR, date_dir)
            if not os.path.isdir(date_path):
                continue

            # 在日期目录中查找匹配的session目录
            for session_dir_name in os.listdir(date_path):
                if session_dir_name.endswith(f"_{session_id}"):
                    return os.path.join(date_path, session_dir_name)

        return None

    @staticmethod
    def load_session(session_id: str) -> Dict:
        """加载会话状态，带文件锁保护"""
        # 首先尝试查找已存在的会话文件
        session_file = SessionManager.find_session_file(session_id)
        if not session_file:
            return {}

        file_lock = get_file_lock(session_id)

        with file_lock:
            if os.path.exists(session_file):
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        # 在Unix系统上使用文件锁
                        try:
                            fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # 共享锁
                            data = json.load(f)
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 解锁
                            return data
                        except (AttributeError, OSError):
                            # Windows系统或不支持fcntl的情况
                            return json.load(f)
                except Exception as e:
                    print(f"加载会话失败 {session_id}: {str(e)}")
                    return {}
            return {}

    @staticmethod
    def save_session(session_id: str, session_data: Dict) -> bool:
        """保存会话状态，带文件锁保护"""
        session_file = SessionManager.get_session_file(session_id)
        file_lock = get_file_lock(session_id)

        with file_lock:
            try:
                session_data["last_updated"] = datetime.now().isoformat()
                with open(session_file, "w", encoding="utf-8") as f:
                    # 在Unix系统上使用文件锁
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 独占锁
                        json.dump(session_data, f, ensure_ascii=False, indent=2)
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 解锁
                    except (AttributeError, OSError):
                        # Windows系统或不支持fcntl的情况
                        json.dump(session_data, f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                print(f"保存会话失败 {session_id}: {str(e)}")
                return False

    @staticmethod
    def create_new_session(session_id: str) -> bool:
        """创建新会话"""
        initial_data = {"session_id": session_id, "created_at": datetime.now().isoformat(), "history": []}
        return SessionManager.save_session(session_id, initial_data)

    @staticmethod
    def session_exists(session_id: str) -> bool:
        """检查会话是否存在"""
        return SessionManager.find_session_file(session_id) is not None

    @staticmethod
    def get_session_question_and_background(session_id: str) -> tuple:
        """从会话中获取最初的问题和背景信息"""
        session_data = SessionManager.load_session(session_id)
        history = session_data.get("history", [])

        # 找到第一个planning请求，获取问题和背景信息
        for record in history:
            if record.get("mode") == "planning" and record.get("request"):
                request_data = record["request"]
                return (request_data.get("question", ""), request_data.get("background_info", ""))

        return "", ""

    @staticmethod
    def get_latest_plan(session_id: str) -> Optional[str]:
        """获取会话中最新的plan"""
        session_data = SessionManager.load_session(session_id)
        history = session_data.get("history", [])

        # 从最新的记录开始查找
        for record in reversed(history):
            if record.get("status") and "plan" in record:
                return json.dumps(record["plan"], ensure_ascii=False, indent=2)

        return ""
