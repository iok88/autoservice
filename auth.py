from playwright.sync_api import sync_playwright

URL = "https://strim-g4up.glide.page"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    # Чистый новый контекст
    context = browser.new_context()
    page = context.new_page()

    page.goto(URL)

    print("=" * 50)
    print("👉 ВОЙДИ ВРУЧНУЮ (почта + код)")
    print("👉 После полной загрузки страницы нажми Enter")
    print("=" * 50)

    input()

    # Сохраняем ВСЕ состояние (ключевой момент!)
    context.storage_state(path="state.json")

    print("✅ Сессия сохранена в state.json")

    browser.close()
