import os
import shlex
import socket

class ShellEmulator:
    def __init__(self):
        # Получаем реальные данные ОС для приглашения
        self.username = os.getlogin()  # текущий пользователь
        self.hostname = socket.gethostname()  # имя хоста
        self.current_dir = os.getcwd()  # текущая директория
        self.running = True  # флаг работы эмулятора
    
    def get_prompt(self):
        """Формирует приглашение к вводу в формате username@hostname:directory$"""
        # Получаем короткое имя текущей директории
        dir_name = os.path.basename(self.current_dir) if self.current_dir != os.path.expanduser("~") else "~"
        return f"{self.username}@{self.hostname}:{dir_name}$ "
    
    def parse_command(self, command_line):
        """Парсит командную строку, корректно обрабатывая кавычки"""
        try:
            # Используем shlex для правильного разбиения строки с учетом кавычек
            parts = shlex.split(command_line)
            if not parts:
                return None, []
            command = parts[0]
            args = parts[1:]
            return command, args
        except ValueError as e:
            print(f"Ошибка парсинга: {e}")
            return None, []
    
    def execute_command(self, command, args):
        """Выполняет команду"""
        if command == "exit":
            # Команда выхода
            self.running = False
            print("Выход из эмулятора")
        
        elif command == "ls":
            # Заглушка для ls - выводит имя команды и аргументы
            print(f"Команда: ls")
            if args:
                print(f"Аргументы: {args}")
            else:
                print("Аргументы отсутствуют")
        
        elif command == "cd":
            # Заглушка для cd - выводит имя команды и аргументы
            print(f"Команда: cd")
            if args:
                print(f"Аргументы: {args}")
                # Здесь будет реальная логика смены директории
            else:
                print("Аргументы отсутствуют")
        
        elif command:
            # Неизвестная команда
            print(f"Команда '{command}' не найдена")
    
    def run(self):
        """Основной цикл REPL (Read-Eval-Print Loop)"""
        print("Добро пожаловать в эмулятор командной строки!")
        print("Доступные команды: ls, cd, exit")
        print("Для выхода введите 'exit'")
        print("-" * 50)
        
        while self.running:
            try:
                # Выводим приглашение и читаем ввод
                prompt = self.get_prompt()
                user_input = input(prompt).strip()
                
                # Пропускаем пустые строки
                if not user_input:
                    continue
                
                # Парсим команду
                command, args = self.parse_command(user_input)
                
                # Выполняем команду
                if command:
                    self.execute_command(command, args)
                else:
                    print("Ошибка: не удалось разобрать команду")
                    
            except KeyboardInterrupt:
                # Обработка Ctrl+C
                print("\nДля выхода используйте команду 'exit'")
            except EOFError:
                # Обработка Ctrl+D
                print("\nВыход из эмулятора")
                break

def main():
    """Точка входа в программу"""
    shell = ShellEmulator()
    shell.run()

if __name__ == "__main__":
    main()