from seleniumbase import SB
import base64
import random
import requests


# ============================================================
# Configuration
# ============================================================

# Proxy configuration (kept exactly as your original logic)
proxy_ip = "127.0.0.1"
proxy_port = "18080"

proxy_str = f"{proxy_ip}:{proxy_port}"
proxy_str = "http://130.185.122.199:8090"
proxy_str = False  # Final override

proxies = {
    "http": proxy_str,
    # "https": proxy_url
}


# ============================================================
# Geolocation Lookup
# ============================================================

def fetch_geolocation(proxy_value: str | bool) -> dict:
    """Retrieve geolocation data, falling back gracefully if proxy fails."""
    try:
        response = requests.get(
            "http://ip-api.com/json/",
            proxies={"http": proxy_value},
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as exc:
        print(f"[WARN] Proxy request failed: {exc}")
        fallback = requests.get("http://ip-api.com/json/")
        return fallback.json()


geo_data = fetch_geolocation(proxy_str)

latitude = geo_data.get("lat")
longitude = geo_data.get("lon")
timezone_id = geo_data.get("timezone")
language_code = geo_data.get("countryCode", "").lower()


# ============================================================
# Target URL Setup
# ============================================================

encoded_name = "YnJ1dGFsbGVz"
decoded_name = base64.b64decode(encoded_name).decode("utf-8")

target_url = f"https://www.twitch.tv/{decoded_name}"
# Alternative:
# target_url = f"https://www.youtube.com/@{decoded_name}/live"


# ============================================================
# Utility Functions
# ============================================================

def handle_consent(driver):
    """Click 'Accept' buttons if present."""
    if driver.is_element_present('button:contains("Accept")'):
        driver.cdp.click('button:contains("Accept")', timeout=4)


def handle_start_watching(driver):
    """Click 'Start Watching' if present."""
    if driver.is_element_present('button:contains("Start Watching")'):
        driver.cdp.click('button:contains("Start Watching")', timeout=4)
        driver.sleep(10)


# ============================================================
# Main Automation Loop
# ============================================================

while True:
    with SB(
        uc=True,
        locale="en",
        ad_block=True,
        chromium_arg="--disable-webgl",
        proxy=proxy_str
    ) as driver:

        random_delay = random.randint(450, 800)

        # Activate CDP with geolocation + timezone
        driver.activate_cdp_mode(
            target_url,
            tzone=str(timezone_id),
            geoloc=(latitude, longitude)
        )

        driver.sleep(2)
        handle_consent(driver)
        driver.sleep(2)
        driver.sleep(12)

        handle_start_watching(driver)
        handle_consent(driver)

        # ------------------------------------------------------------
        # Stream Detected
        # ------------------------------------------------------------
        if driver.is_element_present("#live-channel-stream-information"):

            handle_consent(driver)

            # Spawn secondary driver
            secondary = driver.get_new_driver(undetectable=True)
            secondary.activate_cdp_mode(
                target_url,
                tzone=str(timezone_id),
                geoloc=(latitude, longitude)
            )

            secondary.sleep(10)
            handle_start_watching(secondary)
            handle_consent(secondary)

            driver.sleep(10)
            driver.sleep(random_delay)

        else:
            break
