#!/usr/bin/env python3
"""
Homebrew Manager GUI - Приложение для управления Homebrew на macOS
Позволяет обновлять Homebrew, устанавливать пакеты, диагностировать и исправлять проблемы
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import queue
import re
import sys
import os

class HomebrewManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Homebrew Manager")
        self.root.geometry("800x600")

        # Очередь для обновления GUI из потоков
        self.output_queue = queue.Queue()

        # Переменные состояния
        self.is_running = False

        self.create_widgets()
        self.check_homebrew_installation()

        # Обработка очереди вывода
        self.root.after(100, self.process_queue)

    def create_widgets(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Настройка сетки
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Заголовок
        title_label = ttk.Label(main_frame, text="Homebrew Manager",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))

        # Фрейм для кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        button_frame.columnconfigure((0, 1, 2), weight=1)

        # Кнопки управления
        self.update_btn = ttk.Button(button_frame, text="Обновить Homebrew",
                                    command=self.update_homebrew)
        self.update_btn.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.doctor_btn = ttk.Button(button_frame, text="Диагностика",
                                    command=self.run_doctor)
        self.doctor_btn.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.cleanup_btn = ttk.Button(button_frame, text="Очистка",
                                     command=self.cleanup_homebrew)
        self.cleanup_btn.grid(row=0, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.upgrade_btn = ttk.Button(button_frame, text="Обновить пакеты",
                                     command=self.upgrade_packages)
        self.upgrade_btn.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.list_btn = ttk.Button(button_frame, text="Список пакетов",
                                  command=self.list_packages)
        self.list_btn.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.maintenance_btn = ttk.Button(button_frame, text="Полное обслуживание",
                                         command=self.full_maintenance)
        self.maintenance_btn.grid(row=1, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))

        # Область вывода
        output_frame = ttk.LabelFrame(main_frame, text="Вывод команд", padding="5")
        output_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output_text = scrolledtext.ScrolledText(output_frame, height=20,
                                                    font=("Courier", 10))
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Нижняя панель с прогресс-баром и кнопкой очистки
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        bottom_frame.columnconfigure(1, weight=1)

        # Прогресс-бар
        self.progress_var = tk.StringVar()
        self.progress_var.set("Готов к работе")

        self.progress_bar = ttk.Progressbar(bottom_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, padx=(0, 10))

        self.status_label = ttk.Label(bottom_frame, textvariable=self.progress_var)
        self.status_label.grid(row=0, column=1, sticky=(tk.W))

        # Кнопка очистки
        clear_btn = ttk.Button(bottom_frame, text="Очистить", command=self.clear_output)
        clear_btn.grid(row=0, column=2, padx=(10, 0))

    def check_homebrew_installation(self):
        """Проверяет установку Homebrew"""
        try:
            result = subprocess.run(['brew', '--version'],
                                  capture_output=True, text=True, check=True)
            self.output_text.insert(tk.END, f"✅ Homebrew установлен: {result.stdout}")
            self.output_text.insert(tk.END, f"📦 Homebrew {result.stdout.split()[1]}\n")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.output_text.insert(tk.END, "❌ Homebrew не найден!\n")
            messagebox.showerror("Ошибка", "Homebrew не установлен или не найден в PATH")

    def update_homebrew(self):
        """Обновляет Homebrew"""
        if self.is_running:
            return

        self.start_progress("Обновление Homebrew...")
        thread = threading.Thread(target=self.run_command_thread,
                                 args=(["brew", "update"], "Обновление Homebrew"))
        thread.daemon = True
        thread.start()

    def run_doctor(self):
        """Запускает диагностику Homebrew"""
        if self.is_running:
            return

        self.start_progress("Диагностика Homebrew...")
        thread = threading.Thread(target=self.run_command_thread,
                                 args=(["brew", "doctor"], "Диагностика"))
        thread.daemon = True
        thread.start()

    def cleanup_homebrew(self):
        """Очищает кеш и старые версии Homebrew"""
        if self.is_running:
            return

        self.start_progress("Очистка Homebrew...")
        commands = [
            (["brew", "cleanup", "--prune=all"], "Очистка старых версий"),
            (["brew", "autoremove"], "Удаление неиспользуемых зависимостей")
        ]

        thread = threading.Thread(target=self.run_multiple_commands_thread, args=(commands,))
        thread.daemon = True
        thread.start()

    def upgrade_packages(self):
        """Обновляет все установленные пакеты"""
        if self.is_running:
            return

        self.start_progress("Обновление пакетов...")
        thread = threading.Thread(target=self.run_command_thread,
                                 args=(["brew", "upgrade"], "Обновление пакетов"))
        thread.daemon = True
        thread.start()

    def list_packages(self):
        """Показывает список установленных пакетов"""
        if self.is_running:
            return

        self.start_progress("Получение списка пакетов...")
        commands = [
            (["brew", "list", "--formula"], "Установленные формулы"),
            (["brew", "list", "--cask"], "Установленные cask'и")
        ]

        thread = threading.Thread(target=self.run_multiple_commands_thread, args=(commands,))
        thread.daemon = True
        thread.start()

    def full_maintenance(self):
        """Выполняет полное обслуживание Homebrew"""
        if self.is_running:
            return

        # Спрашиваем подтверждение
        response = messagebox.askyesno(
            "Полное обслуживание",
            "Это выполнит обновление Homebrew, обновление всех пакетов, диагностику и очистку.\n\nПродолжить?"
        )

        if not response:
            return

        self.start_progress("Полное обслуживание...")
        commands = [
            (["brew", "update"], "Обновление Homebrew"),
            (["brew", "upgrade"], "Обновление пакетов"),
            (["brew", "doctor"], "Диагностика"),
            (["brew", "cleanup", "--prune=all"], "Очистка старых версий"),
            (["brew", "autoremove"], "Удаление неиспользуемых зависимостей")
        ]

        thread = threading.Thread(target=self.run_multiple_commands_thread, args=(commands,))
        thread.daemon = True
        thread.start()

    def run_command_thread(self, command, description):
        """Выполняет команду в отдельном потоке"""
        try:
            self.output_queue.put(f"\n🔄 {description}...\n")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Читаем вывод построчно
            for line in process.stdout:
                self.output_queue.put(line)

            process.wait()

            if process.returncode == 0:
                self.output_queue.put(f"✅ {description} завершено успешно\n")
            else:
                self.output_queue.put(f"❌ {description} завершено с ошибкой (код: {process.returncode})\n")
                # Анализируем ошибку
                self.analyze_error(command, process.returncode)

        except Exception as e:
            self.output_queue.put(f"❌ Ошибка выполнения {description}: {str(e)}\n")
        finally:
            self.output_queue.put("COMMAND_FINISHED")

    def run_multiple_commands_thread(self, commands):
        """Выполняет несколько команд последовательно"""
        for command, description in commands:
            try:
                self.output_queue.put(f"\n🔄 {description}...\n")

                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                for line in process.stdout:
                    self.output_queue.put(line)

                process.wait()

                if process.returncode == 0:
                    self.output_queue.put(f"✅ {description} завершено успешно\n")
                else:
                    self.output_queue.put(f"❌ {description} завершено с ошибкой (код: {process.returncode})\n")
                    self.analyze_error(command, process.returncode)

            except Exception as e:
                self.output_queue.put(f"❌ Ошибка выполнения {description}: {str(e)}\n")

        self.output_queue.put("COMMAND_FINISHED")

    def analyze_error(self, command, return_code):
        """Анализирует ошибки и предлагает решения"""
        cmd_str = ' '.join(command)

        suggestions = {
            'brew update': [
                "🔧 Попробуйте очистить кеш: brew cleanup",
                "🌐 Проверьте интернет-соединение",
                "🔄 Попробуйте позже - возможны проблемы с серверами Homebrew"
            ],
            'brew doctor': [
                "🔧 Исправьте права доступа: sudo chown -R $(whoami) $(brew --prefix)/*",
                "🧹 Очистите кеш: brew cleanup",
                "📝 Обратите внимание на предупреждения выше"
            ],
            'brew upgrade': [
                "💾 Освободите место на диске",
                "🔄 Попробуйте обновить пакеты по отдельности",
                "🧹 Выполните очистку: brew cleanup"
            ]
        }

        for cmd_pattern, solutions in suggestions.items():
            if cmd_pattern in cmd_str:
                self.output_queue.put("💡 Возможные решения:\n")
                for solution in solutions:
                    self.output_queue.put(f"   {solution}\n")
                break

    def start_progress(self, message):
        """Запускает индикатор прогресса"""
        self.is_running = True
        self.progress_var.set(message)
        self.progress_bar.start()

        # Отключаем кнопки
        for widget in [self.update_btn, self.doctor_btn, self.cleanup_btn,
                      self.upgrade_btn, self.list_btn, self.maintenance_btn]:
            widget.configure(state='disabled')

    def stop_progress(self):
        """Останавливает индикатор прогресса"""
        self.is_running = False
        self.progress_var.set("Готов к работе")
        self.progress_bar.stop()

        # Включаем кнопки
        for widget in [self.update_btn, self.doctor_btn, self.cleanup_btn,
                      self.upgrade_btn, self.list_btn, self.maintenance_btn]:
            widget.configure(state='normal')

    def process_queue(self):
        """Обрабатывает очередь сообщений от фоновых потоков"""
        try:
            while True:
                message = self.output_queue.get_nowait()
                if message == "COMMAND_FINISHED":
                    self.stop_progress()
                else:
                    self.output_text.insert(tk.END, message)
                    self.output_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def clear_output(self):
        """Очищает область вывода"""
        self.output_text.delete(1.0, tk.END)

def check_platform():
    """Проверяет, что приложение запущено на macOS"""
    if sys.platform != 'darwin':
        messagebox.showerror("Ошибка платформы",
                           "Это приложение предназначено только для macOS")
        return False
    return True

def main():
    if not check_platform():
        return

    root = tk.Tk()
    app = HomebrewManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()