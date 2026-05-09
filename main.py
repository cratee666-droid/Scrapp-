from flask import Flask, request, jsonify
import asyncio
import random
from playwright.async_api import async_playwright

app = Flask(__name__)

async def scrape_google(query, num_results=10):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        await page.goto(f'https://www.google.com/search?q={query}&num={num_results}')
        await asyncio.sleep(random.uniform(1.5, 3.0))

        try:
            await page.click('button:has-text("Accept all")', timeout=3000)
        except:
            pass

        results = []
        items = await page.query_selector_all('.g')

        for item in items:
            try:
                title_el = await item.query_selector('h3')
                link_el  = await item.query_selector('a')
                desc_el  = await item.query_selector('.VwiC3b, .yXK7lf')

                title = await title_el.inner_text() if title_el else None
                link  = await link_el.get_attribute('href') if link_el else None
                desc  = await desc_el.inner_text() if desc_el else ''

                if title and link and link.startswith('http'):
                    results.append({
                        'position': len(results) + 1,
                        'title': title,
                        'url': link,
                        'description': desc
                    })
            except:
                continue

        await browser.close()
    return results

@app.route('/')
def home():
    return '''
    <h2>🔍 Google Scraper</h2>
    <form action="/search">
        <input name="q" placeholder="Enter search query" style="padding:8px;width:300px">
        <input name="num" placeholder="Number of results (default 10)" style="padding:8px;width:250px">
        <button type="submit" style="padding:8px">Search</button>
    </form>
    '''

@app.route('/search')
def search():
    query = request.args.get('q', '')
    num   = int(request.args.get('num', 10))
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    results = asyncio.run(scrape_google(query, num))
    return jsonify({'query': query, 'results': results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)