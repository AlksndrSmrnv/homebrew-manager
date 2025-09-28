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
import json
import urllib.request
import urllib.parse
from datetime import datetime

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

        # Новый ряд кнопок для анализа
        self.size_analysis_btn = ttk.Button(button_frame, text="Анализ размеров",
                                           command=self.analyze_package_sizes)
        self.size_analysis_btn.grid(row=2, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.security_check_btn = ttk.Button(button_frame, text="Проверка безопасности",
                                           command=self.security_check)
        self.security_check_btn.grid(row=2, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

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
                      self.upgrade_btn, self.list_btn, self.maintenance_btn,
                      self.size_analysis_btn, self.security_check_btn]:
            widget.configure(state='disabled')

    def stop_progress(self):
        """Останавливает индикатор прогресса"""
        self.is_running = False
        self.progress_var.set("Готов к работе")
        self.progress_bar.stop()

        # Включаем кнопки
        for widget in [self.update_btn, self.doctor_btn, self.cleanup_btn,
                      self.upgrade_btn, self.list_btn, self.maintenance_btn,
                      self.size_analysis_btn, self.security_check_btn]:
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

    def analyze_package_sizes(self):
        """Анализирует размеры установленных пакетов"""
        if self.is_running:
            return

        self.start_progress("Анализ размеров пакетов...")
        thread = threading.Thread(target=self.analyze_sizes_thread)
        thread.daemon = True
        thread.start()

    def analyze_sizes_thread(self):
        """Анализирует размеры пакетов в отдельном потоке"""
        try:
            self.output_queue.put("\n📊 Анализ размеров установленных пакетов...\n")

            # Получаем список всех установленных пакетов
            process = subprocess.run(["brew", "list", "--formula"],
                                   capture_output=True, text=True, check=True)
            packages = [pkg.strip() for pkg in process.stdout.strip().split('\n') if pkg.strip()]

            if not packages:
                self.output_queue.put("📦 Нет установленных пакетов\n")
                self.output_queue.put("COMMAND_FINISHED")
                return

            package_sizes = []
            self.output_queue.put(f"🔍 Найдено {len(packages)} пакетов. Анализирую размеры...\n\n")

            # Получаем общий путь к Homebrew
            prefix_process = subprocess.run(["brew", "--prefix"],
                                          capture_output=True, text=True, check=True)
            brew_prefix = prefix_process.stdout.strip()
            cellar_path = f"{brew_prefix}/Cellar"

            for i, package in enumerate(packages):
                try:
                    # Путь к пакету в Cellar
                    package_cellar_path = f"{cellar_path}/{package}"

                    if os.path.exists(package_cellar_path):
                        # Используем более надежный способ подсчета размера
                        size_bytes = self.get_directory_size(package_cellar_path)
                        size_str = self.format_size(size_bytes)
                        package_sizes.append((package, size_str, size_bytes))
                    else:
                        # Попробуем найти пакет через brew --prefix
                        try:
                            path_process = subprocess.run(["brew", "--prefix", package],
                                                        capture_output=True, text=True, check=True)
                            package_path = path_process.stdout.strip()

                            if os.path.exists(package_path):
                                size_bytes = self.get_directory_size(package_path)
                                size_str = self.format_size(size_bytes)
                                package_sizes.append((package, size_str, size_bytes))
                        except subprocess.CalledProcessError:
                            # Пакет может быть симлинком или недоступен
                            continue

                    # Прогресс
                    if (i + 1) % 10 == 0:
                        self.output_queue.put(f"📈 Обработано {i + 1}/{len(packages)} пакетов...\n")

                except subprocess.CalledProcessError:
                    # Пакет может быть недоступен или удален
                    continue
                except Exception as e:
                    self.output_queue.put(f"⚠️ Ошибка при анализе {package}: {str(e)}\n")
                    continue

            # Сортируем по размеру (от большего к меньшему)
            package_sizes.sort(key=lambda x: x[2], reverse=True)

            # Выводим результаты
            self.output_queue.put("\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА РАЗМЕРОВ:\n")
            self.output_queue.put("=" * 60 + "\n")

            total_bytes = sum(size[2] for size in package_sizes)
            self.output_queue.put(f"📦 Всего пакетов: {len(package_sizes)}\n")
            self.output_queue.put(f"💾 Общий размер: {self.format_size(total_bytes)}\n\n")

            # Топ 20 самых больших пакетов
            self.output_queue.put("🔝 ТОП-20 САМЫХ БОЛЬШИХ ПАКЕТОВ:\n")
            self.output_queue.put("-" * 60 + "\n")

            for i, (package, size_str, size_bytes) in enumerate(package_sizes[:20]):
                percentage = (size_bytes / total_bytes) * 100 if total_bytes > 0 else 0
                self.output_queue.put(f"{i+1:2d}. {package:<25} {size_str:>8} ({percentage:.1f}%)\n")

            # Статистика по размерам
            self.output_queue.put("\n📈 СТАТИСТИКА ПО РАЗМЕРАМ:\n")
            self.output_queue.put("-" * 60 + "\n")

            large_packages = [p for p in package_sizes if p[2] > 100 * 1024 * 1024]  # > 100MB
            medium_packages = [p for p in package_sizes if 10 * 1024 * 1024 < p[2] <= 100 * 1024 * 1024]  # 10-100MB
            small_packages = [p for p in package_sizes if p[2] <= 10 * 1024 * 1024]  # <= 10MB

            self.output_queue.put(f"🔴 Большие пакеты (>100MB): {len(large_packages)}\n")
            self.output_queue.put(f"🟡 Средние пакеты (10-100MB): {len(medium_packages)}\n")
            self.output_queue.put(f"🟢 Малые пакеты (<10MB): {len(small_packages)}\n")

            # Рекомендации
            if large_packages:
                self.output_queue.put("\n💡 РЕКОМЕНДАЦИИ:\n")
                self.output_queue.put("-" * 60 + "\n")
                self.output_queue.put("🧹 Рассмотрите возможность удаления неиспользуемых больших пакетов\n")
                self.output_queue.put("📦 Выполните 'brew cleanup' для очистки старых версий\n")
                if len(large_packages) > 5:
                    self.output_queue.put(f"⚠️ У вас {len(large_packages)} пакетов размером более 100MB\n")

        except subprocess.CalledProcessError as e:
            self.output_queue.put(f"❌ Ошибка при получении списка пакетов: {str(e)}\n")
        except Exception as e:
            self.output_queue.put(f"❌ Ошибка анализа размеров: {str(e)}\n")
        finally:
            self.output_queue.put("COMMAND_FINISHED")

    def parse_size(self, size_str):
        """Преобразует строку размера в байты"""
        size_str = size_str.strip().upper()
        multipliers = {
            'B': 1,
            'K': 1024,
            'M': 1024 * 1024,
            'G': 1024 * 1024 * 1024,
            'T': 1024 * 1024 * 1024 * 1024
        }

        try:
            if size_str[-1] in multipliers:
                number = float(size_str[:-1])
                multiplier = multipliers[size_str[-1]]
                return int(number * multiplier)
            else:
                return int(float(size_str))
        except (ValueError, IndexError):
            return 0

    def get_directory_size(self, path):
        """Вычисляет размер директории в байтах"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        if os.path.exists(filepath) and not os.path.islink(filepath):
                            total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        continue
        except (OSError, IOError):
            return 0
        return total_size

    def format_size(self, size_bytes):
        """Форматирует размер в читаемый вид"""
        if size_bytes == 0:
            return "0B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"

    def security_check(self):
        """Проверяет безопасность установленных пакетов"""
        if self.is_running:
            return

        self.start_progress("Проверка безопасности...")
        thread = threading.Thread(target=self.security_check_thread)
        thread.daemon = True
        thread.start()

    def security_check_thread(self):
        """Выполняет проверку безопасности в отдельном потоке"""
        try:
            self.output_queue.put("\n🔒 Проверка безопасности установленных пакетов...\n")

            # Получаем список установленных пакетов
            process = subprocess.run(["brew", "list", "--formula"],
                                   capture_output=True, text=True, check=True)
            packages = [pkg.strip() for pkg in process.stdout.strip().split('\n') if pkg.strip()]

            if not packages:
                self.output_queue.put("📦 Нет установленных пакетов для проверки\n")
                self.output_queue.put("COMMAND_FINISHED")
                return

            self.output_queue.put(f"🔍 Найдено {len(packages)} пакетов для проверки...\n\n")

            # Проверяем устаревшие пакеты
            self.output_queue.put("📅 Проверка устаревших пакетов...\n")
            try:
                outdated_process = subprocess.run(["brew", "outdated"],
                                                capture_output=True, text=True, check=True)
                outdated_packages = [pkg.strip() for pkg in outdated_process.stdout.strip().split('\n') if pkg.strip()]

                if outdated_packages:
                    self.output_queue.put(f"⚠️ Найдено {len(outdated_packages)} устаревших пакетов:\n")
                    for pkg in outdated_packages[:10]:  # Показываем первые 10
                        self.output_queue.put(f"   📦 {pkg}\n")
                    if len(outdated_packages) > 10:
                        self.output_queue.put(f"   ... и еще {len(outdated_packages) - 10} пакетов\n")
                else:
                    self.output_queue.put("✅ Все пакеты актуальны\n")
            except subprocess.CalledProcessError:
                self.output_queue.put("ℹ️ Не удалось проверить устаревшие пакеты\n")

            # Проверяем известные уязвимые пакеты
            self.output_queue.put("\n🛡️ Проверка известных уязвимостей...\n")
            vulnerable_packages = self.check_known_vulnerabilities(packages)

            if vulnerable_packages:
                self.output_queue.put(f"🚨 Найдены потенциально уязвимые пакеты:\n")
                for pkg, risk in vulnerable_packages:
                    risk_emoji = "🔴" if risk == "high" else "🟡" if risk == "medium" else "🟢"
                    self.output_queue.put(f"   {risk_emoji} {pkg} - риск: {risk}\n")
            else:
                self.output_queue.put("✅ Известных уязвимостей не обнаружено\n")

            # Проверяем подозрительные пакеты
            self.output_queue.put("\n🔍 Проверка подозрительных пакетов...\n")
            suspicious_packages = self.check_suspicious_packages(packages)

            if suspicious_packages:
                self.output_queue.put(f"⚠️ Найдены подозрительные пакеты:\n")
                for pkg, reason in suspicious_packages:
                    self.output_queue.put(f"   🔍 {pkg} - {reason}\n")
            else:
                self.output_queue.put("✅ Подозрительных пакетов не найдено\n")

            # Проверяем права доступа
            self.output_queue.put("\n🔐 Проверка прав доступа Homebrew...\n")
            self.check_homebrew_permissions()

            # Итоговый отчет
            self.output_queue.put("\n📋 ИТОГОВЫЙ ОТЧЕТ БЕЗОПАСНОСТИ:\n")
            self.output_queue.put("=" * 60 + "\n")

            total_issues = len(outdated_packages) + len(vulnerable_packages) + len(suspicious_packages)

            if total_issues == 0:
                self.output_queue.put("✅ Серьезных проблем безопасности не обнаружено\n")
            else:
                self.output_queue.put(f"⚠️ Обнаружено проблем: {total_issues}\n")

            # Рекомендации
            self.output_queue.put("\n💡 РЕКОМЕНДАЦИИ ПО БЕЗОПАСНОСТИ:\n")
            self.output_queue.put("-" * 60 + "\n")
            self.output_queue.put("🔄 Регулярно обновляйте пакеты: brew upgrade\n")
            self.output_queue.put("🧹 Удаляйте неиспользуемые пакеты: brew uninstall <package>\n")
            self.output_queue.put("🔍 Проверяйте источники перед установкой новых пакетов\n")
            self.output_queue.put("📊 Используйте 'brew audit' для дополнительных проверок\n")

            if outdated_packages:
                self.output_queue.put(f"⚡ Обновите {len(outdated_packages)} устаревших пакетов\n")

        except subprocess.CalledProcessError as e:
            self.output_queue.put(f"❌ Ошибка при проверке безопасности: {str(e)}\n")
        except Exception as e:
            self.output_queue.put(f"❌ Ошибка проверки безопасности: {str(e)}\n")
        finally:
            self.output_queue.put("COMMAND_FINISHED")

    def check_known_vulnerabilities(self, packages):
        """Проверяет пакеты на известные уязвимости"""
        # Список ТОЧНО уязвимых версий пакетов
        known_vulnerabilities = {
            'openssl@1.0': 'high',  # Старые версии OpenSSL
            'openssl@1.1': 'medium',
            'python@2': 'high',     # Python 2 больше не поддерживается
            'python@2.7': 'high',
            'node@10': 'high',      # Старые версии Node.js EOL
            'node@12': 'medium',
            'node@14': 'low',       # Скоро EOL
            'mysql@5.6': 'medium',  # Старые версии MySQL
            'mysql@5.7': 'low',
            'postgresql@9': 'medium', # Старые версии PostgreSQL
            'postgresql@10': 'low',
            'imagemagick@6': 'medium', # Старые версии ImageMagick
            'git@2.30': 'medium',   # Старые версии Git с уязвимостями
            'curl@7.70': 'medium',  # Старые версии curl
        }

        vulnerable = []
        for package in packages:
            # Проверяем ТОЛЬКО точные совпадения версионных пакетов
            if package in known_vulnerabilities:
                vulnerable.append((package, known_vulnerabilities[package]))

        return vulnerable

    def check_suspicious_packages(self, packages):
        """Проверяет пакеты на подозрительные признаки"""
        suspicious = []

        # Проверяем ТОЧНЫЕ совпадения подозрительных пакетов
        suspicious_packages = {
            'cryptominer': 'возможный криптомайнер',
            'bitcoin-miner': 'майнер биткоинов',
            'monero-miner': 'майнер Monero',
            'proxy-server': 'прокси-сервер',
            'socks-proxy': 'SOCKS прокси',
            'tor-browser': 'анонимизация через Tor',
            'darknet': 'доступ к даркнету',
            'keylogger': 'клавиатурный шпион',
            'backdoor': 'бэкдор',
            'rootkit': 'руткит',
        }

        # Также проверяем пакеты с подозрительными паттернами, но более точно
        suspicious_patterns = [
            ('mining', 'содержит майнинг'),
            ('stealer', 'похож на стилер'),
            ('hijack', 'возможный хайджек'),
            ('exploit', 'содержит эксплойт'),
            ('virus', 'подозрение на вирус'),
        ]

        for package in packages:
            package_lower = package.lower()

            # Проверяем точные совпадения
            if package_lower in suspicious_packages:
                suspicious.append((package, suspicious_packages[package_lower]))
            else:
                # Проверяем паттерны только для явно подозрительных имен
                for pattern, reason in suspicious_patterns:
                    if pattern in package_lower:
                        suspicious.append((package, reason))
                        break

        return suspicious

    def check_homebrew_permissions(self):
        """Проверяет права доступа к Homebrew"""
        try:
            # Получаем путь к Homebrew
            prefix_process = subprocess.run(["brew", "--prefix"],
                                          capture_output=True, text=True, check=True)
            homebrew_prefix = prefix_process.stdout.strip()

            # Проверяем владельца директории Homebrew
            import pwd
            import stat

            current_user = pwd.getpwuid(os.getuid()).pw_name

            try:
                stat_info = os.stat(homebrew_prefix)
                owner = pwd.getpwuid(stat_info.st_uid).pw_name

                if owner == current_user:
                    self.output_queue.put(f"✅ Права доступа корректны (владелец: {owner})\n")
                else:
                    self.output_queue.put(f"⚠️ Предупреждение: владелец Homebrew - {owner}, а не {current_user}\n")
                    self.output_queue.put("💡 Рекомендуется: sudo chown -R $(whoami) $(brew --prefix)/*\n")

            except (OSError, KeyError):
                self.output_queue.put("⚠️ Не удалось проверить права доступа к Homebrew\n")

        except subprocess.CalledProcessError:
            self.output_queue.put("❌ Не удалось получить путь к Homebrew\n")
        except Exception as e:
            self.output_queue.put(f"⚠️ Ошибка при проверке прав доступа: {str(e)}\n")

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