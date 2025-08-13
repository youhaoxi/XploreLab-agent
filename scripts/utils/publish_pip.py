"""
from @QBAgentsExtension by @charlesshen

see https://mirrors.tencent.com/#/private/pypi/
"""

import os
import subprocess
import sys
import urllib.parse

import requests
import toml


def build_and_publish(username, password):
    """构建和发布项目"""
    print("Syncing dependencies...")
    # backup uv.lock! restore after publish
    os.system("cp uv.lock uv.lock.bak")

    result = subprocess.run(["uv", "sync"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: Failed to sync dependencies\n{result.stderr}")
        return False

    print("Cleaning project...")
    result = subprocess.run(["uv", "clean"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: Failed to clean project\n{result.stderr}")
        return False

    print("Building project...")
    result = subprocess.run(["uv", "build"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: Failed to build project\n{result.stderr}")
        return False

    print("Publishing project...")
    publish_url = "https://mirrors.tencent.com/repository/pypi/tencent_pypi/simple"
    result = subprocess.run(
        ["uv", "publish", "--username", username, "--password", password, "--publish-url", publish_url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error: Project publish failed\n{result.stderr}")
        return False

    # restore uv.lock
    os.system("mv uv.lock uv.lock.publish")
    os.system("mv uv.lock.bak uv.lock")
    result = subprocess.run(["uv", "sync", "--extra", "dev"], capture_output=True, text=True)
    return True


def extract_project_info():
    """从pyproject.toml提取项目信息"""
    pyproject_file = f"pyproject.toml"

    if not os.path.isfile(pyproject_file):
        print(f"Error: {pyproject_file} not found")
        return None, None

    try:
        # 使用toml库解析文件
        with open(pyproject_file, "r") as f:
            pyproject_data = toml.load(f)

        name = pyproject_data.get("project", {}).get("name")
        version = pyproject_data.get("project", {}).get("version")
        authors = pyproject_data.get("project", {}).get("authors")
        description = pyproject_data.get("project", {}).get("description")

        if not name or not version:
            print(f"Error: Failed to extract project information(name version authors) from {pyproject_file}")
            return None, None, None, None

        return name, version, authors, description
    except Exception as e:
        print(f"Error parsing {pyproject_file}: {e}")
        return None, None, None, None


def query_server_config(host, auth_key, project_name):
    """API请求 - 查询服务器配置"""
    filter_value = f'server_name="{project_name}"'
    encoded_filter = urllib.parse.quote(filter_value)
    url = f"{host}/api/object?filter={encoded_filter}&{auth_key}"

    response = requests.get(url)
    return response.json()


def create_server_config(host, auth_key, json_data):
    """API请求 - 创建服务器配置"""
    url = f"{host}/api/object?{auth_key}"
    headers = {"Content-Type": "application/json; charset=UTF-8"}

    response = requests.post(url, headers=headers, json=json_data)
    return response.json()


def main():
    """主函数"""
    # 验证命令行参数
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <project_dir> [username] [password]")
        sys.exit(1)

    # 获取uv版本
    result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
    print(f"uv version: {result.stdout.strip()}")

    project_dir = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) > 2 else os.getenv("TX_PYPI_USERNAME")
    password = sys.argv[3] if len(sys.argv) > 3 else os.getenv("TX_PYPI_PASSWORD")
    print(f"> args:{sys.argv}")
    print(f"> using username:{username}!")

    # 获取Git根目录
    git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode("utf-8").strip()
    print(f"git_root:{git_root} ")

    try:
        print(f"Entering project directory: {git_root}/{project_dir}")
        os.chdir(f"{git_root}/{project_dir}")
    except Exception as e:
        print(f"Failed to enter project directory, exit! excetion:{e}")
        sys.exit(1)

    project_name, project_version, project_authors, project_description = extract_project_info()
    print(
        f"project_name:{project_name}\n"
        f"project_version:{project_version}\n"
        f"project_authors:{project_authors}\n"
        f"project_description:{project_description}"
    )
    if not project_name or not project_version:
        print(f"Failed to get project_name or project_version, exit!")
        sys.exit(1)

    # 构建和发布项目
    if not build_and_publish(username, password):
        print(f"Failed to build_and_publish, exit!")
        sys.exit(1)


if __name__ == "__main__":
    main()
