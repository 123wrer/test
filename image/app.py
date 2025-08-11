import base64
import requests
import os
import sys

# Конфигурация
GITHUB_TOKEN = "1"
REPO_OWNER = "123wrer"
REPO_NAME = "test"
BRANCH = "main"
IMAGE_FOLDER = "image"

def check_repo_access():
    """Проверка доступа к репозиторию"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def ensure_image_folder():
    """Создание папки image если не существует"""
    gitkeep_path = f"{IMAGE_FOLDER}/.gitkeep"
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{gitkeep_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Проверяем существование папки
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f"✅ Папка {IMAGE_FOLDER} уже существует")
        return True
    
    # Создаем .gitkeep для создания папки
    data = {
        "message": f"Create {IMAGE_FOLDER} folder",
        "content": base64.b64encode(b"").decode('utf-8'),
        "branch": BRANCH
    }
    
    response = requests.put(url, headers=headers, json=data)
    if response.status_code in [200, 201]:
        print(f"✅ Папка {IMAGE_FOLDER} создана")
        return True
    else:
        print(f"❌ Ошибка создания папки: {response.status_code}")
        print(response.text)
        return False

def upload_file(filename):
    """Загрузка файла в папку image"""
    local_path = filename
    remote_path = f"{IMAGE_FOLDER}/{os.path.basename(filename)}"
    
    # Проверка локального файла
    if not os.path.exists(local_path):
        print(f"❌ Локальный файл {local_path} не найден")
        return False
    
    # Чтение файла
    with open(local_path, "rb") as file:
        file_content = file.read()
    encoded_content = base64.b64encode(file_content).decode('utf-8')
    
    # API URL
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{remote_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Проверка существования файла
    response = requests.get(api_url, headers=headers)
    sha = response.json().get('sha') if response.status_code == 200 else None
    
    # Данные для запроса
    data = {
        "message": f"Upload {os.path.basename(filename)}",
        "content": encoded_content,
        "branch": BRANCH
    }
    
    if sha:
        data["sha"] = sha
        print(f"🔄 Обновляем существующий файл: {remote_path}")
    else:
        print(f"📤 Загружаем новый файл: {remote_path}")
    
    # Загрузка файла
    response = requests.put(api_url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        content_data = response.json()["content"]
        raw_url = content_data["download_url"]
        print(f"✅ Файл успешно загружен!")
        print(f"🔗 Raw-ссылка: {raw_url}")
        return True
    else:
        print(f"❌ Ошибка загрузки: {response.status_code}")
        print(response.text)
        return False

def delete_file(filename):
    """Удаление файла из папки image"""
    remote_path = f"{IMAGE_FOLDER}/{filename}"
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{remote_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Получаем SHA файла
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Файл {remote_path} не найден")
        return False
    
    sha = response.json()["sha"]
    
    # Удаляем файл
    data = {
        "message": f"Delete {filename}",
        "sha": sha,
        "branch": BRANCH
    }
    
    response = requests.delete(api_url, headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"✅ Файл {remote_path} успешно удален")
        return True
    else:
        print(f"❌ Ошибка удаления: {response.status_code}")
        print(response.text)
        return False

def list_files():
    """Показать файлы в папке image"""
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{IMAGE_FOLDER}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        files = response.json()
        print(f"\n📁 Файлы в папке {IMAGE_FOLDER}:")
        for file in files:
            print(f"- {file['name']} ({file['size']} bytes)")
        return True
    else:
        print(f"❌ Ошибка получения списка файлов: {response.status_code}")
        print(response.text)
        return False

def main():
    print("🚀 GitHub File Manager")
    print(f"Репозиторий: {REPO_OWNER}/{REPO_NAME}")
    print(f"Ветка: {BRANCH}")
    print(f"Папка: {IMAGE_FOLDER}")
    
    # Проверка доступа
    if not check_repo_access():
        print("❌ Нет доступа к репозиторию. Проверьте токен и название репозитория.")
        sys.exit(1)
    
    # Создание папки image
    if not ensure_image_folder():
        print("❌ Не удалось создать папку image")
        sys.exit(1)
    
    # Основной цикл
    while True:
        print("\nДоступные команды:")
        print("1. upload <путь_к_файлу> - загрузить файл")
        print("2. delete <имя_файла> - удалить файл")
        print("3. list - показать файлы в папке")
        print("4. exit - выход")
        
        command = input("\nВведите команду: ").strip().lower()
        
        if command.startswith("upload "):
            filename = command[7:].strip()
            if filename:
                upload_file(filename)
            else:
                print("❌ Укажите путь к файлу")
        
        elif command.startswith("delete "):
            filename = command[7:].strip()
            if filename:
                delete_file(filename)
            else:
                print("❌ Укажите имя файла")
        
        elif command == "list":
            list_files()
        
        elif command == "exit":
            print("👋 До свидания!")
            break
        
        else:
            print("❌ Неизвестная команда")

if __name__ == "__main__":
    main()