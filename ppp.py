import requests
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from colorama import Fore, Style, init
from seleniumbase import SB
import random
import base64
import requests
# Initialize colorama
init(autoreset=True)

# -------------------------
# Proxy sources
# -------------------------

SOURCE_1 = "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt"

FRESH_PROXY_BASE = "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/"
FRESH_PROXY_FILES = {
    "http": "http.txt",
    "https": "https.txt",
    "socks4": "socks4.txt",
    "socks5": "socks5.txt"
}


# -------------------------
# Load proxies from all sources
# -------------------------
def load_proxies():
    proxies = []

    # ---- Source 1: Proxifly ----
    try:
        r = requests.get(SOURCE_1, timeout=10)
        r.raise_for_status()
        for line in r.text.splitlines():
            if line.strip():
                proxies.append(line.strip())
    except Exception as e:
        print("Failed to load source 1:", e)

    # ---- Source 2: Fresh-Proxy-List ----
    for proto, filename in FRESH_PROXY_FILES.items():
        url = FRESH_PROXY_BASE + filename
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            for line in r.text.splitlines():
                line = line.strip()
                if not line:
                    continue
                proxies.append(f"{proto}://{line}")
        except Exception as e:
            print(f"Failed to load {filename}:", e)

    # ---- Source 3: ClearProxy ----
    CLEARPROXY_BASE = "https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/"
    CLEARPROXY_PATHS = [
        "http/raw/all.txt",
        "socks4/raw/all.txt",
        "socks5/raw/all.txt"
    ]

    for path in CLEARPROXY_PATHS:
        url = CLEARPROXY_BASE + path
        protocol = path.split("/")[0].strip()

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()

            for line in r.text.splitlines():
                line = line.strip()
                if not line:
                    continue
                proxies.append(f"{protocol}://{line}")

        except Exception as e:
            print(f"Failed to load ClearProxy {protocol}:", e)

    # ---- Source 4: Databay Labs ----
    DATABAY_BASE = "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/"
    DATABAY_FILES = {
        "http": "http.txt",
        "https": "https.txt",
        "socks5": "socks5.txt"
    }

    for proto, filename in DATABAY_FILES.items():
        url = DATABAY_BASE + filename
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()

            for line in r.text.splitlines():
                line = line.strip()
                if not line:
                    continue
                proxies.append(f"{proto}://{line}")

        except Exception as e:
            print(f"Failed to load Databay {proto}:", e)

    print(f"Loaded total proxies: {len(proxies)}")
    return proxies


def load_proxieso():
    proxies = []

    # Source 1
    try:
        r = requests.get(SOURCE_1, timeout=10)
        r.raise_for_status()
        for line in r.text.splitlines():
            if line.strip():
                proxies.append(line.strip())
    except Exception as e:
        print("Failed to load source 1:", e)

    # Source 2
    for proto, filename in FRESH_PROXY_FILES.items():
        url = FRESH_PROXY_BASE + filename
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            for line in r.text.splitlines():
                line = line.strip()
                if not line:
                    continue
                proxies.append(f"{proto}://{line}")
        except Exception as e:
            print(f"Failed to load {filename}:", e)

    print(f"Loaded total proxies: {len(proxies)}")
    return proxies


# -------------------------
# Proxy tester (YouTube)
# -------------------------

def check_proxy(args):
    index, total, raw_proxy = args
    raw_proxy = raw_proxy.strip()

    # Detect protocol
    if raw_proxy.startswith("socks5://"):
        protocol = "socks5"
        ip_port = raw_proxy.replace("socks5://", "")
    elif raw_proxy.startswith("socks4://"):
        protocol = "socks4"
        ip_port = raw_proxy.replace("socks4://", "")
    elif raw_proxy.startswith("https://"):
        protocol = "https"
        ip_port = raw_proxy.replace("https://", "")
    elif raw_proxy.startswith("http://"):
        protocol = "http"
        ip_port = raw_proxy.replace("http://", "")
    else:
        result = f"{Fore.YELLOW}[{index}/{total}] ⚠ Unknown format: {raw_proxy}{Style.RESET_ALL}"
        return (result, None)

    proxy_url = f"{protocol}://{ip_port}"
    proxies = {"http": proxy_url, "https": proxy_url}

    try:
        r = requests.get("https://www.youtube.com", proxies=proxies, timeout=1, allow_redirects=True)
        if r.status_code in (200, 301, 302):
            result = f"{Fore.GREEN}[{index}/{total}] ✅ {proxy_url}{Style.RESET_ALL}"
            return (result, proxy_url)
        else:
            result = f"{Fore.RED}[{index}/{total}] ❌ {proxy_url}{Style.RESET_ALL}"
            return (result, None)

    except Exception:
        result = f"{Fore.RED}[{index}/{total}] ❌ {proxy_url}{Style.RESET_ALL}"
        return (result, None)

    finally:
        sleep(0.2)  # avoid hammering YouTube


# -------------------------
# Main
# -------------------------
import random
if __name__ == "__main__":
    proxies_list = load_proxies()

    # Randomize order before testing
    random.shuffle(proxies_list)

    total = len(proxies_list)
    valid_proxies = []

    # Prepare arguments for workers
    args_list = [(i, total, proxy) for i, proxy in enumerate(proxies_list, start=1)]

    print("\nStarting proxy testing with 5 workers...\n")

    # Use ThreadPoolExecutor with 5 workers
    with ThreadPoolExecutor(max_workers=9) as executor:
        for result, valid in executor.map(check_proxy, args_list):
            print(result)

            if valid:
                valid_proxies.append(valid)

                # Stop early when 5 working proxies are found
                if len(valid_proxies) >= 5:
                    print("\nFound 5 working proxies. Stopping early.\n")
                    break

    print("----------------------------------")
    print("Working proxies:")
    name = "YnJ1dGFsbGVz"

    name_d = base64.b64decode(name)
    fulln = name_d.decode("utf-8")
    urlt = f"https://www.twitch.tv/{fulln}"
    urlt = f"https://www.youtube.com/@{fulln}/live"
    urlt = "https://www.youtube.com/watch?v=Lju1aI6P8o0"
    for p in valid_proxies:
        with SB(uc=True, locale="en",ad_block=True,chromium_arg='--disable-webgl',proxy = p) as peono:
            rnd = random.randint(4,9)
            
            peono.activate_cdp_mode(urlt)

            peono.sleep(30)
            if peono.is_element_present('button:contains("Accept")'):
                peono.cdp.click('button:contains("Accept")', timeout=4)
                peono.sleep(10)
            else:
                peono.sleep(10)
                peono.cdp.gui_press_key('K')
            peono.sleep(120)
        print(p)
    print("----------------------------------\n")

