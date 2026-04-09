import csv
from playwright.sync_api import sync_playwright

URL = "https://strim-g4up.glide.page"

def pause(msg):
    """Выводит сообщение и ждёт нажатия Enter"""
    input(f"\n🛑 {msg}\n>>> Нажми Enter для продолжения...")


def is_empty_value(value):
    """Возвращает True, если значение пустое или представляет прочерк."""
    return value is None or value.strip() in ("", "-", "—")


def select_complex_dropdown(page, label_text, value):
    """
    Функция выбора из сложных выпадающих списков Glide.
    """
    print(f"   📝 Обработка поля '{label_text}' со значением '{value}'...")
    
    # 1. Клик по лейблу
    page.get_by_label(label_text).click()
    
    # 2. Заполнение лейбла
    try:
        page.get_by_label(label_text).fill(value)
    except Exception:
        pass
        
    # 3. Повторный клик по лейблу
    page.get_by_label(label_text).click()
    
    # 4. Поиск поля ввода внутри выпадающего списка
    # 🔴 ИСПРАВЛЕНО: .first вместо .first()
    search_input = page.locator("input[placeholder='Поиск']:visible").first
    search_input.wait_for(state="visible", timeout=5000) 
    search_input.fill(value)
    
    # 5. Клик по результату
    # 🔴 ИСПРАВЛЕНО: .first вместо .first()
    option = page.get_by_text(value).first
    option.wait_for(state="visible", timeout=5000)
    option.click()
    
    print(f"   ✅ Выбрано: {value}")

def run():
    with sync_playwright() as p:
        print("🚀 Запуск браузера...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="state.json", viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        print("🌐 Переход на сайт...")
        page.goto(URL)
        pause("Сайт открылся. Проверь авторизацию.")

        # Читаем CSV
        with open("data_1.csv", "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            fieldnames = reader.fieldnames
            all_rows = list(reader)

        # ⚠️ Обрабатываем ВСЕ строки, пропуская уже добавленные
        for i, row in enumerate(all_rows):
            status = row.get("Статус", "").strip()
            print(f"📋 Строка {i+1}: Статус='{status}' | Шасси={row['Шасси']}")
            if status == "Добавлено":
                print(f"   ⏭️ Уже обработана, пропускаю.")
                continue
            
            # --- ЭТАП 1: Поиск и открытие Самосвала ---
            print("👉 Шаг 1: Клик по кнопке 'Самосвалы'")
            page.get_by_role("button", name="Самосвалы").first.wait_for(state="visible", timeout=5000)
            page.get_by_role("button", name="Самосвалы").first.click()
            page.wait_for_timeout(1000)  # Ждём загрузки раздела
            print("Раздел 'Самосвалы' открыт.")

            # Ввод номера шасси
            print("👉 Шаг 2: Ввод номера шасси")
            chassis_search = page.locator("section").filter(has_text="Самосвалы").get_by_placeholder("Поиск")
            chassis_search.wait_for(state="visible", timeout=5000)
            chassis_search.click()
            chassis_search.fill(row["Шасси"])
            print(f"Ввёл '{row['Шасси']}'. Сейчас скрипт кликнет по первому результату...")

            # Клик по первой видимой карточке
            print("👉 Шаг 3: Открытие карточки самосвала")
            try:
                page.locator("[data-testid='collection-item-0']:visible").first.wait_for(state="visible", timeout=3000)
                page.locator("[data-testid='collection-item-0']:visible").first.click()
                print("Карточка открыта.")
            except:
                print(f"❌ Самосвал с шасси {row['Шасси']} не найден!")
                row["Статус"] = "Шасси не найдено"
                
                # Сохраняем CSV с отметкой о том, что шасси не найдено
                try:
                    with open("data_1.csv", "w", encoding="utf-8-sig", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", extrasaction='ignore')
                        writer.writeheader()
                        writer.writerows(all_rows)
                except Exception as csv_error:
                    print(f"⚠️ Ошибка при сохранении CSV: {csv_error}")
                print(f"⚠️  Строка {i+1} пропущена - шасси не найдено")
                
                # Переходим на главную и начинаем со следующей строки
                page.goto(URL)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                except:
                    pass
                page.wait_for_timeout(1000)
                continue

            # --- ЭТАП 2: Редактирование ---
            print("👉 Шаг 4: Нажатие 'Редактировать'")
            page.get_by_label("Редактировать").click()
            print("Перешёл в режим редактирования.")

            # Заполнение простых полей
            print("👉 Шаг 5: Заполнение Гаражного номера и Моточасов")
            page.get_by_label("Гаражный номер").fill(row["Гаражный номер"])
            page.get_by_label("Моточасы").fill(row["Наработка"])
            print("Заполнил основные поля.")

            # --- ЭТАП 3_iok: Место нахождения ---
            page.get_by_label("Место нахождения").click()
            page.get_by_label("Место нахождения").fill(row["Место"])
            page.get_by_label("Место нахождения").click()
            print("Выбрал 'Место нахождения'.")

            # --- ЭТАП 4_iok: Сервис ---
            service_dropdown = page.get_by_test_id("wc-trigger").nth(1)
            service_text = (service_dropdown.text_content() or "").strip()
            if is_empty_value(row["Сервис"]):
                print("В CSV нет значения сервиса, пропускаю.")
            elif row["Сервис"] not in service_text:
                service_dropdown.click()
                page.wait_for_timeout(500)  # Ждём открытия выпадающего списка
                page.get_by_placeholder("Поиск").fill(row["Сервис"])
                page.wait_for_timeout(1500)  # Ждём загрузки результатов поиска
                service_option = page.get_by_text(row["Сервис"], exact=False).first
                service_option.wait_for(state="visible", timeout=5000)  # Проверяем видимость
                service_option.click()
                page.keyboard.press("Escape")
                print("Выбрал 'Сервис'.")
            else:
                print("Сервисная организация уже выбрана, пропускаю.")

            # --- ЭТАП 5_iok: Эксплуатация ---
            exploitation_dropdown = page.get_by_test_id("wc-trigger").nth(2)
            exploitation_text = (exploitation_dropdown.text_content() or "").strip()
            if is_empty_value(row["Эксплуатация"]):
                print("В CSV нет значения эксплуатации, пропускаю.")
            elif row["Эксплуатация"] not in exploitation_text:
                exploitation_dropdown.click()
                page.wait_for_timeout(500)  # Ждём открытия выпадающего списка
                search = page.get_by_placeholder("Поиск")
                search.fill(row["Эксплуатация"])
                page.wait_for_timeout(1500)  # Ждём загрузки результатов поиска
                option = page.locator("li[role='option']").filter(has_text=row["Эксплуатация"]).first
                option.wait_for(state="visible", timeout=5000)
                option.click()
                page.keyboard.press("Escape")
                print("Выбрал 'Эксплуатация'.")
            else:
                print("Эксплуатирующая организация уже выбрана, пропускаю.")
             

            print("👉 Шаг 6: Нажатие 'Отправить' (основная форма)")
            page.get_by_role("button", name="Отправить").click()
            print("Нажал 'Отправить'. Жду закрытия формы...")
            page.wait_for_timeout(1000)

            # --- ЭТАП 5: Добавление устройства ---
            print("👉 Шаг 7: Повторное открытие карточки")
            page.locator("[data-testid='collection-item-0']:visible").first.click()
            print("Снова открыл карточку.")

            print("👉 Шаг 8: Добавление устройства")
            page.get_by_label("Добавить устройство в шкаф").first.click()
            print("Открыл меню добавления устройства.")

            page.get_by_label("Устройство СТРИМ").click()
            print("Выбрал тип 'Устройство СТРИМ'.")

            page.get_by_test_id("slide-in-content").get_by_label("Новое устройство").click()
            print("Открыл форму нового устройства.")

            # Поиск устройства
            print("👉 Шаг 9: Поиск устройства в списке")
            page.wait_for_timeout(500)
            device_search = page.get_by_placeholder("Любое устройство")
            device_search.click()
            device_search.fill(row["Наименование"])
            print(f"Ввёл '{row['Наименование']}'. Сейчас выберу устройство...")
            
            # Открытие выпадающего списка и выбор устройства
            page.get_by_test_id("wc-trigger").click()
            page.get_by_label("Search through available").fill(row["Наименование"])
            page.get_by_label("Select options").get_by_text(row["Наименование"], exact=True).click()
            print("Выбрал устройство из списка.")

            # Серийный номер
            print("👉 Шаг 10: Ввод серийного номера")
            page.get_by_label("Серийный номер").click()
            page.get_by_label("Серийный номер").fill(row["Серийный номер"])
            print("Ввёл серийный номер.")

            # Финальная отправка
            print("👉 Шаг 11: Финальная отправка")
            page.get_by_label("Отправить").click()
            pause("ВСЁ ГОТОВО! Проверь результат на сайте.")

            # Отмечаем строку как обработанную
            row["Статус"] = "Добавлено"
            print(f"✅ Строка {i+1} успешно обработана и отмечена в CSV.")

            # Сохраняем CSV после каждой строки
            try:
                with open("data_1.csv", "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(all_rows)
                print("💾 CSV обновлён.")
            except Exception as csv_error:
                print(f"⚠️ Ошибка при сохранении CSV: {csv_error}")

            # Возвращаемся на главную страницу для следующей строки
            page.goto(URL)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=10000)
            except:
                print("⚠️ Страница не загрузилась полностью, продолжаю...")
            page.wait_for_timeout(1000)  # Дополнительная задержка для инициализации
            print("🔄 Вернулся на главную страницу.")

        print("\n🏁 Обработка всех строк завершена.")
        browser.close()

if __name__ == "__main__":
    run()
