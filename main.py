# Импорт необходимых модулей Python
import os  # для работы с операционной системой (файлы, директории, пути)
import shlex  # для корректного разбиения командной строки с учетом кавычек
import socket  # для получения информации о сетевых параметрах (имя хоста)
import argparse  # для парсинга аргументов командной строки
import sys  # для работы с системными параметрами (не используется явно, но может потребоваться)
import json  # для работы с JSON-файлами VFS
import base64  # для декодирования base64 данных

class VFS:
    """
    Класс для работы с виртуальной файловой системой (VFS)
    Все операции производятся в памяти на основе JSON-файла
    """
    
    def __init__(self, vfs_path=None):
        """
        Инициализация виртуальной файловой системы
        
        Args:
            vfs_path (str): Путь к JSON-файлу с описанием VFS
        """
        self.vfs_path = vfs_path
        self.file_system = {}  # Словарь для хранения структуры файловой системы
        self.current_vfs_path = "/"  # Текущий путь в VFS
        
        if vfs_path and os.path.exists(vfs_path):
            self.load_vfs(vfs_path)
        else:
            # Создаем минимальную VFS по умолчанию
            self.create_default_vfs()
    
    def load_vfs(self, vfs_path):
        """
        Загружает VFS из JSON-файла
        """
        try:
            with open(vfs_path, 'r', encoding='utf-8') as f:
                self.file_system = json.load(f)
            print(f"VFS загружена из {vfs_path}")
        except Exception as e:
            print(f"Ошибка загрузки VFS: {e}")
            self.create_default_vfs()
    
    def create_default_vfs(self):
        """Создает минимальную VFS по умолчанию"""
        self.file_system = {
            "/": {
                "type": "directory",
                "content": {
                    "home": {
                        "type": "directory", 
                        "content": {
                            "user": {
                                "type": "directory",
                                "content": {
                                    "documents": {
                                        "type": "directory",
                                        "content": {
                                            "readme.txt": {
                                                "type": "file",
                                                "content": "Добро пожаловать в VFS!"
                                            }
                                        }
                                    },
                                    "file1.txt": {
                                        "type": "file", 
                                        "content": "Содержимое file1.txt"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        print("Создана VFS по умолчанию")
    
    def decode_content(self, content):
        """
        Декодирует содержимое файла из base64 если необходимо
        """
        if isinstance(content, str) and content.startswith('base64:'):
            try:
                base64_data = content[7:]  # Убираем префикс 'base64:'
                decoded = base64.b64decode(base64_data).decode('utf-8')
                return decoded
            except Exception as e:
                return f"Ошибка декодирования: {e}"
        return content
    
    def get_path_parts(self, path):
        """
        Разбивает путь на части, обрабатывая относительные пути и символы . и ..
        """
        if path.startswith('/'):
            # Абсолютный путь
            parts = [p for p in path.split('/') if p]
            parts.insert(0, '/')
        else:
            # Относительный путь - начинаем с текущего
            current_parts = [p for p in self.current_vfs_path.split('/') if p]
            if current_parts and current_parts[0] == '':
                current_parts = current_parts[1:]
            
            new_parts = [p for p in path.split('/') if p]
            
            # Обрабатываем . и ..
            result_parts = []
            for part in new_parts:
                if part == '.':
                    continue
                elif part == '..':
                    if result_parts:
                        result_parts.pop()
                    elif current_parts:
                        current_parts.pop()
                else:
                    result_parts.append(part)
            
            parts = ['/'] + current_parts + result_parts
        
        return parts
    
    def resolve_path(self, path):
        """
        Преобразует путь в абсолютный путь VFS
        """
        parts = self.get_path_parts(path)
        return '/' + '/'.join(parts[1:]) if len(parts) > 1 else '/'

    def path_exists(self, path):
        """
        Проверяет существование пути в VFS
        """
        if path == "/":
            return True
        
        parts = [p for p in path.split('/') if p]  # Убираем пустые элементы
        current = self.file_system.get("/", {})
        
        for part in parts:
            content = current.get('content', {})
            if part not in content:
                return False
            current = content[part]
        
        return True

    def get_directory_listing(self, path):
        """
        Получает список содержимого директории
        """
        if not self.path_exists(path):
            return None
        
        if path == "/":
            content = self.file_system.get("/", {}).get('content', {})
            return list(content.keys())
        
        parts = [p for p in path.split('/') if p]
        current = self.file_system.get("/", {})
        
        for part in parts:
            content = current.get('content', {})
            current = content[part]
        
        if current.get('type') != 'directory':
            return None
        
        return list(current.get('content', {}).keys())

    def get_node(self, path):
        """
        Получает узел VFS по указанному пути
        """
        if not self.path_exists(path):
            return None
        
        if path == "/":
            return self.file_system.get("/")
        
        parts = [p for p in path.split('/') if p]
        current = self.file_system.get("/", {})
        
        for part in parts:
            content = current.get('content', {})
            if part not in content:
                return None
            current = content[part]
        
        return current  

    def read_file(self, path):
        """
        Читает содержимое файла из VFS
        """
        node = self.get_node(path)
        if node is None or node.get('type') != 'file':
            return None
        
        content = node.get('content', '')
        return self.decode_content(content)

    def get_file_size(self, path):
        """
        Получает размер файла в VFS
        """
        content = self.read_file(path)
        if content is None:
            return None
        return len(content.encode('utf-8'))

    def count_file_stats(self, path):
        """
        Подсчитывает статистику файла (строки, слова, байты)
        """
        content = self.read_file(path)
        if content is None:
            return None, None, None
        
        lines = content.splitlines()
        line_count = len(lines)
        word_count = sum(len(line.split()) for line in lines)
        byte_count = len(content.encode('utf-8'))
        
        return line_count, word_count, byte_count

    def get_directory_size(self, path):
        """
        Рекурсивно вычисляет общий размер всех файлов в директории
        """
        if not self.path_exists(path):
            return None
        
        total_size = 0
        
        if path == "/":
            content = self.file_system.get("/", {}).get('content', {})
        else:
            node = self.get_node(path)
            if node.get('type') != 'directory':
                return None
            content = node.get('content', {})
        
        for name, item in content.items():
            item_path = path + '/' + name if path != '/' else '/' + name
            if item.get('type') == 'file':
                file_size = self.get_file_size(item_path)
                if file_size is not None:
                    total_size += file_size
            elif item.get('type') == 'directory':
                dir_size = self.get_directory_size(item_path)
                if dir_size is not None:
                    total_size += dir_size
        
        return total_size

    def get_tree_structure(self, path, prefix="", is_last=True, is_root=True):
        """
        Рекурсивно строит древовидную структуру директории
        """
        if not self.path_exists(path):
            return None
        
        node = self.get_node(path)
        if node.get('type') != 'directory':
            return None
        
        if is_root:
            result = path + "\n"
        else:
            result = prefix + ("└── " if is_last else "├── ") + os.path.basename(path) + "\n"
        
        content = node.get('content', {})
        items = list(content.items())
        
        for i, (name, item) in enumerate(items):
            item_path = path + '/' + name if path != '/' else '/' + name
            is_last_item = i == len(items) - 1
            
            if item.get('type') == 'directory':
                new_prefix = prefix + ("    " if is_last else "│   ")
                subtree = self.get_tree_structure(item_path, new_prefix, is_last_item, False)
                if subtree:
                    result += subtree
            else:
                result += prefix + ("    " if is_last else "│   ")
                result += ("└── " if is_last_item else "├── ") + name + "\n"
        
        return result

class ShellEmulator:
    """
    Основной класс эмулятора командной строки.
    Реализует функциональность REPL (Read-Eval-Print Loop) цикла.
    """
    
    def __init__(self, vfs_path=None, startup_script=None):
        """
        Конструктор класса. Инициализирует эмулятор.
        
        Args:
            vfs_path (str, optional): Путь к виртуальной файловой системе
            startup_script (str, optional): Путь к стартовому скрипту для автоматического выполнения
        """
        
        # Получаем имя текущего пользователя ОС для отображения в приглашении
        self.username = os.getlogin()
        
        # Получаем сетевое имя компьютера для отображения в приглашении
        self.hostname = socket.gethostname()
        
        # Получаем текущую рабочую директорию для отображения в приглашении
        self.current_dir = os.getcwd()
        
        # Флаг работы эмулятора. Когда становится False - программа завершается
        self.running = True
        
        # Инициализируем VFS
        self.vfs = VFS(vfs_path)
        self.startup_script = startup_script
        
        # Выводим отладочную информацию о конфигурации эмулятора
        print("КОНФИГУРАЦИЯ ЭМУЛЯТОРА")
        # Выводим путь к VFS или сообщение, что путь не указан
        print(f"VFS путь: {vfs_path or 'Не указан (используется VFS по умолчанию)'}")
        # Выводим путь к стартовому скрипту или сообщение, что скрипт не указан
        print(f"Стартовый скрипт: {self.startup_script or 'Не указан'}")
        # Рисуем разделительную линию для визуального отделения конфигурации
        print("=" * 40)
    
    def get_prompt(self):
        """
        Формирует строку приглашения к вводу в формате username@hostname:directory$
        
        Returns:
            str: Строка приглашения для пользователя
        """
        
        # Используем VFS путь вместо реального пути ОС
        vfs_dir = self.vfs.current_vfs_path
        if vfs_dir == "/":
            dir_name = "/"
        else:
            dir_name = os.path.basename(vfs_dir) if vfs_dir != "/" else "/"
        
        # Формируем и возвращаем строку приглашения
        return f"{self.username}@{self.hostname}:{dir_name}$ "
    
    def parse_command(self, command_line):
        """
        Разбивает строку команды на имя команды и аргументы с учетом кавычек.
        
        Args:
            command_line (str): Строка, введенная пользователем
            
        Returns:
            tuple: (command, args) где command - имя команды, args - список аргументов
                   или (None, []) если строка пустая или произошла ошибка парсинга
        """
        
        try:
            # Используем shlex.split для корректного разбиения строки
            # Этот метод правильно обрабатывает кавычки и экранирование
            parts = shlex.split(command_line)
            
            # Если после разбиения получили пустой список (пользователь ввел пустую строку)
            if not parts:
                return None, []  # Возвращаем None и пустой список аргументов
            
            # Первый элемент - это имя команды
            command = parts[0]
            # Все остальные элементы - это аргументы команды
            args = parts[1:]
            
            return command, args
            
        except ValueError as e:
            # Обрабатываем ошибки парсинга (например, незакрытые кавычки)
            print(f"Ошибка парсинга: {e}")
            return None, []  # Возвращаем None и пустой список при ошибке
    
    def execute_command(self, command, args):
        """
        Выполняет команду эмулятора.
        """
        
        # Проверяем команду exit - завершение работы эмулятора
        if command == "exit":
            # Устанавливаем флаг работы в False для остановки основного цикла
            self.running = False
            print("Выход из эмулятора")
        
        # Обрабатываем команду ls (list directory) - теперь работает с VFS
        elif command == "ls":
            target_path = args[0] if args else self.vfs.current_vfs_path
            
            listing = self.vfs.get_directory_listing(target_path)
            if listing is not None:
                for item in listing:
                    print(item)
            else:
                print(f"ls: невозможно получить доступ к '{target_path}': Нет такого файла или каталога")
        
        # Обрабатываем команду cd (change directory) - теперь работает с VFS
        elif command == "cd":
            if not args:
                # cd без аргументов - переход в корень VFS
                self.vfs.current_vfs_path = "/"
            else:
                target_path = args[0]
                new_path = self.vfs.resolve_path(target_path)
                
                if self.vfs.path_exists(new_path):
                    # Получаем узел по пути
                    node = self.vfs.get_node(new_path)
                    if node.get('type') == 'directory':
                        self.vfs.current_vfs_path = new_path
                    else:
                        print(f"cd: {target_path}: Не каталог")
                else:
                    print(f"cd: {target_path}: Нет такого файла или каталога")
        
        # Новая команда cat для чтения файлов из VFS
        elif command == "cat":
            if not args:
                print("cat: отсутствует операнд")
                return
            
            for file_path in args:
                content = self.vfs.read_file(self.vfs.resolve_path(file_path))
                if content is not None:
                    print(content)
                else:
                    print(f"cat: {file_path}: Нет такого файла или каталога")
        
        # Новая команда pwd для показа текущего пути в VFS
        elif command == "pwd":
            print(self.vfs.current_vfs_path)
        
        # Команда echo для демонстрации работы с аргументами
        elif command == "echo":
            print(f"echo: {' '.join(args)}")
        
        # Новая команда wc для подсчета строк, слов и байтов
        elif command == "wc":
            if not args:
                print("wc: отсутствует операнд")
                return
            
            for file_path in args:
                line_count, word_count, byte_count = self.vfs.count_file_stats(self.vfs.resolve_path(file_path))
                if line_count is not None:
                    print(f"  {line_count}  {word_count}  {byte_count} {file_path}")
                else:
                    print(f"wc: {file_path}: Нет такого файла или каталога")
        
        # Новая команда du для показа размера файлов и директорий
        elif command == "du":
            if not args:
                # Если аргументов нет, показываем размер текущей директории
                target_path = self.vfs.current_vfs_path
            else:
                target_path = self.vfs.resolve_path(args[0])
            
            size = self.vfs.get_directory_size(target_path)
            if size is not None:
                print(f"{size}\t{target_path}")
            else:
                print(f"du: невозможно получить доступ к '{target_path}': Нет такого файла или каталога")
        
        # Новая команда tree для показа древовидной структуры
        elif command == "tree":
            if not args:
                target_path = self.vfs.current_vfs_path
            else:
                target_path = self.vfs.resolve_path(args[0])
            
            tree_structure = self.vfs.get_tree_structure(target_path)
            if tree_structure is not None:
                print(tree_structure)
            else:
                print(f"tree: {target_path} [ошибка открытия каталога]")
        
        # Обрабатываем неизвестные команды
        elif command:
            print(f"Команда '{command}' не найдена")

    def run_script(self, script_path):
        """
        Выполняет команды из файла скрипта.
        
        Args:
            script_path (str): Путь к файлу скрипта
        """
        
        # Проверяем существует ли файл скрипта
        if not os.path.exists(script_path):
            print(f"Ошибка: скрипт '{script_path}' не найден")
            return  # Выходим из функции если файл не существует
        
        # Сообщаем о начале выполнения скрипта
        print(f"\nВЫПОЛНЕНИЕ СКРИПТА: {script_path}")
        
        try:
            # Открываем файл скрипта для чтения с кодировкой UTF-8
            with open(script_path, 'r', encoding='utf-8') as file:
                # Читаем все строки файла в список
                lines = file.readlines()
            
            # Проходим по всем строкам скрипта, нумеруя их начиная с 1
            for line_num, line in enumerate(lines, 1):
                # Убираем пробельные символы в начале и конце строки
                line = line.strip()
                
                # Пропускаем пустые строки и строки-комментарии (начинающиеся с #)
                if not line or line.startswith('#'):
                    continue  # Переходим к следующей строке
                
                # Имитируем интерактивный ввод: показываем приглашение и команду
                prompt = self.get_prompt()  # Получаем текущее приглашение
                print(f"{prompt}{line}")  # Выводим как будто пользователь ввел эту команду
                
                # Парсим команду из строки скрипта
                command, args = self.parse_command(line)
                
                # Если команда распаршена успешно - выполняем ее
                if command:
                    self.execute_command(command, args)
                else:
                    # Если произошла ошибка парсинга - сообщаем и пропускаем строку
                    print(f"Строка {line_num}: ошибка парсинга - пропускаем")
                
                # Печатаем пустую строку для визуального разделения команд
                print()
            
            # Сообщаем о завершении выполнения скрипта
            print("ВЫПОЛНЕНИЕ СКРИПТА ЗАВЕРШЕНО")
            
        except Exception as e:
            # Обрабатываем любые исключения при работе с файлом скрипта
            print(f"Ошибка при выполнении скрипта: {e}")
    
    def run(self):
        """
        Основной метод запуска эмулятора.
        Реализует главный цикл программы.
        """
        
        # Сначала выполняем стартовый скрипт, если он был указан
        if self.startup_script:
            self.run_script(self.startup_script)
        
        # Затем переходим в интерактивный режим работы с пользователем
        print("\nИНТЕРАКТИВНЫЙ РЕЖИМ")
        print("Доступные команды: ls, cd, cat, pwd, echo, wc, du, tree, exit")  # Список поддерживаемых команд
        print("Для выхода введите 'exit'")  # Подсказка как выйти
        print("-" * 50)  # Разделительная линия
        
        # Главный цикл программы - работает пока self.running = True
        while self.running:
            try:
                # Получаем текущее приглашение для ввода
                prompt = self.get_prompt()
                # Ждем ввода от пользователя и убираем пробелы по краям
                user_input = input(prompt).strip()
                
                # Если пользователь ввел пустую строку - пропускаем итерацию
                if not user_input:
                    continue  # Переходим к следующей итерации цикла
                
                # Парсим введенную команду на имя и аргументы
                command, args = self.parse_command(user_input)
                
                # Если команда успешно распарсена - выполняем ее
                if command:
                    self.execute_command(command, args)
                else:
                    # Если не удалось разобрать команду - сообщаем об ошибке
                    print("Ошибка: не удалось разобрать команду")
                    
            except KeyboardInterrupt:
                # Обрабатываем нажатие Ctrl+C - не выходим, а только сообщаем
                print("\nДля выхода используйте команду 'exit'")
            except EOFError:
                # Обрабатываем нажатие Ctrl+D (конец файла) - выходим из цикла
                print("\nВыход из эмулятора")
                break  # Прерываем цикл

def parse_arguments():
    """
    Парсит аргументы командной строки при запуске программы.
    
    Returns:
        argparse.Namespace: Объект с распарсенными аргументами
    """
    
    # Создаем парсер аргументов с описанием программы
    parser = argparse.ArgumentParser(description='Эмулятор командной строки UNIX')
    
    # Добавляем аргумент для пути к VFS
    # --vfs-path - имя аргумента в командной строке
    # help - текст справки который покажется при --help
    # default=None - значение по умолчанию если аргумент не указан
    parser.add_argument('--vfs-path', 
                       help='Путь к физическому расположению VFS',
                       default=None)
    
    # Добавляем аргумент для пути к стартовому скрипту
    parser.add_argument('--startup-script',
                       help='Путь к стартовому скрипту',
                       default=None)
    
    # Парсим аргументы командной строки и возвращаем результат
    return parser.parse_args()

def main():
    """
    Главная функция программы - точка входа.
    Координирует весь процесс работы эмулятора.
    """
    
    # Парсим аргументы командной строки
    args = parse_arguments()

    
    # Создаем экземпляр эмулятора с переданными параметрами
    shell = ShellEmulator(
        vfs_path=args.vfs_path,  # Путь к VFS из аргументов
        startup_script=args.startup_script  # Путь к скрипту из аргументов
    )
    
    # Запускаем основной цикл эмулятора
    shell.run()

# Стандартная конструкция для точки входа в Python программу
if __name__ == "__main__":
    main()  # Вызываем главную функцию при прямом запуске файла