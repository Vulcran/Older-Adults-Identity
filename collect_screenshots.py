import base64
import json
import mimetypes
import os
import time
from urllib.request import Request, urlopen
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(SCRIPT_DIR, 'adsToLoad.json'), 'r') as f:
    ads_data = json.load(f)

with open(os.path.join(SCRIPT_DIR, 'yahooS.js'), 'r') as f:
    yahoo_js = f.read()

# Org name (key in JSON) -> filename inside /logos
LOGO_FILES = {
    "Amazon": "Amazon-logo-meaning.jpg",
    "Apple": "Apple.png",
    "Bank of America": "Bank-of-America.png",
    "CapitalOne": "CapitalOne.png",
    "Citi": "Citi-Logo.png",
    "Facebook Marketplace": "Facebook_f_logo_(2021).svg.png",
    "Microsoft": "Microsoft_logo.svg.png",
    "PayPal": "PayPal_Logo2014.svg.png",
    "UPS": "UPS-Logo.png",
    "USPS": "USPS.jpg",
    "Venmo": "Venmo_logo.png",
    "eBay": "eBay-Emblem.png",
    "FedEx": "fedex-logo-png_seeklogo-53457.png",
}

PICSUM_URL = "https://picsum.photos/200"


def logo_data_url(org_name):
    """Return a data URL for the local logo so Chrome will render it on Yahoo's HTTPS page."""
    filename = LOGO_FILES.get(org_name)
    if not filename:
        return ""
    abs_path = os.path.join(SCRIPT_DIR, "logos", filename)
    mime_type = mimetypes.guess_type(abs_path)[0] or "image/png"
    with open(abs_path, "rb") as logo_file:
        encoded = base64.b64encode(logo_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def image_response_to_data_url(response):
    content_type = response.headers.get("Content-Type", "image/jpeg").split(";", 1)[0]
    encoded = base64.b64encode(response.read()).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def fetch_picsum_data_url(retries=3):
    for attempt in range(retries):
        try:
            request = Request(PICSUM_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=15) as response:
                return image_response_to_data_url(response)
        except Exception as e:
            print(f"  Warning: picsum fetch attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    return None  # caller handles None


def format_display_url(link):
    if "/" not in link:
        return link

    if "://" in link:
        _, rest = link.split("://", 1)
    else:
        rest = link

    parts = [part for part in rest.split("/") if part]
    if not parts:
        return link

    return parts[0] + " &rsaquo; " + " &rsaquo; ".join(parts[1:])


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--allow-file-access-from-files")
    chrome_options.add_argument("--window-size=1200,900")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def inject_ad_and_screenshot(driver, ad_data, output_path):
    js_data = json.dumps(ad_data)

    script = f"""
    {yahoo_js}
    const removeYahooScout = () => {{
        const injected = document.getElementById('injected-ad-container');
        const scoutNeedle = 'yahoo scout helps you understand more';
        const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').replace(/\\s+/g, ' ').trim();
        const candidates = Array.from(document.body.querySelectorAll('div, section, aside, article'))
            .filter((el) => {{
                if (injected && el.contains(injected)) return false;
                return normalize(el.innerText).includes(scoutNeedle);
            }})
            .sort((a, b) => (a.innerText || '').length - (b.innerText || '').length);

        candidates.forEach((el) => {{
            if (el.isConnected) el.remove();
        }});
    }};

    removeYahooScout();

    const prev = document.getElementById('injected-ad-container');
    if (prev) prev.remove();

    const data = {js_data};
    const html = generateYahooAdHTML(data);
    const container = document.createElement('div');
    container.id = 'injected-ad-container';
    container.style.padding = '20px';
    container.style.backgroundColor = 'white';
    container.style.width = '824px';
    container.style.maxWidth = '824px';
    container.style.boxSizing = 'border-box';
    container.innerHTML = html;

    const target = document.querySelector('#results') || document.body;
    target.insertBefore(container, target.firstChild);
    removeYahooScout();

    return container.getBoundingClientRect();
    """

    driver.execute_script(script)
    driver.execute_script("window.scrollTo(0, 0);")

    # Find the element BEFORE waiting, so we hold a reference to it
    element = driver.find_element(By.ID, 'injected-ad-container')

    driver.execute_async_script("""
        const done = arguments[0];
        const images = Array.from(document.querySelectorAll('#injected-ad-container img'));
        let finished = false;
        const complete = () => {
            if (!finished) {
                finished = true;
                done(true);
            }
        };
        const loaded = () => images.every((img) => img.complete && img.naturalWidth > 0);
        if (!images.length || loaded()) { complete(); return; }
        images.forEach((img) => {
            img.addEventListener('load', () => { if (loaded()) complete(); }, { once: true });
            img.addEventListener('error', complete, { once: true });
        });
        setTimeout(complete, 3000);
        """)
    time.sleep(0.2)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    element.screenshot(output_path)
    print(f"Saved: {output_path}")


def build_variations(org_name, org_data):
    """Return a list of (dir_path, params) tuples for every screenshot to capture for this org."""
    links = org_data["Links"]
    blue = org_data["BlueText"]
    name = org_data["NameOverURL"]
    desc = org_data["Description"]

    normal_logo = logo_data_url(org_name)

    def base_params(link, blue_text, company_name, description, image_src, is_random_image, is_ad, is_official):
        return {
            "searchTerm": org_name,
            "blueText": blue_text,
            "description": description,
            "imagePath": image_src,
            "isRandomImage": is_random_image,
            "companyName": company_name,
            "formattedLink": format_display_url(link),
            "isOfficialSite": is_official,
            "isAd": is_ad,
        }

    # Each entry: (base_dir, subvariant_suffix, link, blue_text, company_name, description, favicon)
    # subvariant_suffix is appended to the filename so multiple sub-flavors of the same category
    # (e.g. URL/Subdomain vs URL/Alt) don't overwrite each other.
    plans = []

    plans.append(("No-Changes", "", links["Normal"], blue["Normal"], name["Normal"], desc["Normal"], normal_logo))

    if links.get("Typo"):
        plans.append(("URL-Typo", "", links["Typo"], blue["Normal"], name["Normal"], desc["Normal"], normal_logo))

    if links.get("Target"):
        plans.append(("URL-Target", "Target", links["Target"], blue["Normal"], name["Normal"], desc["Normal"],
                      normal_logo))

    if links.get("Alt"):
        plans.append(("URL-Alt", "Alt", links["Alt"], blue["Normal"], name["Normal"], desc["Normal"], normal_logo))

    if blue.get("Alt"):
        plans.append(("BigBlueText", "", links["Normal"], blue["Alt"], name["Normal"], desc["Normal"], normal_logo))

    if name.get("Alt"):
        plans.append(("NameOverURL", "", links["Normal"], blue["Normal"], name["Alt"], desc["Normal"], normal_logo))

    # Image: replace favicon with a random picsum photo
    plans.append(("Image", "", links["Normal"], blue["Normal"], name["Normal"], desc["Normal"], PICSUM_URL))

    if links.get("Typo"):
        plans.append(("TypoAndImage", "", links["Typo"], blue["Normal"], name["Normal"], desc["Normal"], PICSUM_URL))

    if desc.get("Alt"):
        plans.append(("Description", "", links["Normal"], blue["Normal"], name["Normal"], desc["Alt"], normal_logo))

    if name.get("Alt") and links.get("Alt"):
        plans.append(("AboveBlueText", "", links["Alt"], blue["Normal"], name["Alt"], desc["Normal"], normal_logo))

    if blue.get("Alt") and desc.get("Alt"):
        plans.append(("BlueTextAndBelow", "", links["Normal"], blue["Alt"], name["Normal"], desc["Alt"], normal_logo))

    variations = []
    for base_dir, subvariant, link, blue_text, company_name, description, favicon in plans:
        filename = f"{org_name}.png"
        is_random_image = base_dir in ("Image", "Typo&Image", "random-image")
        image_src = PICSUM_URL if is_random_image else normal_logo
        for is_ad in (True, False):
            for is_official in (True, False):
                sub = f"{'Sponsored' if is_ad else 'Not-Sponsored'}/{'Official' if is_official else 'Not-Official'}"
                dir_path = f"{base_dir}/{sub}"
                params = base_params(link, blue_text, company_name, description, image_src, is_random_image, is_ad,
                                     is_official)
                variations.append((dir_path, filename, params))

    return variations


def main():
    driver = get_driver()
    try:
        driver.get("https://search.yahoo.com/search?p=test")
        time.sleep(3)

        for org_name, org_data in ads_data.items():
            print(f"Processing {org_name}...")

            for dir_path, filename, params in build_variations(org_name, org_data):
                output_file = os.path.join(SCRIPT_DIR, dir_path, filename)
                if params["isRandomImage"]:
                    data_url = fetch_picsum_data_url()
                    if data_url is None:
                        print(f"  Skipping {output_file} (could not fetch random image)")
                        continue
                    params = dict(params)
                    params["imagePath"] = data_url
                inject_ad_and_screenshot(driver, params, output_file)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
