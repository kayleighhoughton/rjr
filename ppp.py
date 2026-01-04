import asyncio
import random
import requests
import aiohttp
from aiohttp_socks import ProxyConnector
from concurrent.futures import ThreadPoolExecutor

def load_proxies():
    proxies = []


    # ---- Source 1.1: Proxifly ----
    try:
        r = requests.get("https://raw.githubusercontent.com/dpangestuw/Free-Proxy/main/allive.txt", timeout=10)
        r.raise_for_status()
        for line in r.text.splitlines():
            if line.strip():
                proxies.append(line.strip())
    except Exception as e:
        print("Failed to load Proxifly:", e)

    # ---- Source 1: Proxifly ----
    try:
        r = requests.get("https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt", timeout=10)
        r.raise_for_status()
        for line in r.text.splitlines():
            if line.strip():
                proxies.append(line.strip())
    except Exception as e:
        print("Failed to load Proxifly:", e)

    # ---- Source 2: Fresh-Proxy-List ----
    FRESH_PROXY_BASE = "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/"
    FRESH_PROXY_FILES = {
        "http": "http.txt",
        "https": "https.txt",
        "socks4": "socks4.txt",
        "socks5": "socks5.txt"
    }

    for proto, filename in FRESH_PROXY_FILES.items():
        url = FRESH_PROXY_BASE + filename
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            for line in r.text.splitlines():
                line = line.strip()
                if line:
                    proxies.append(f"{proto}://{line}")
        except Exception as e:
            print(f"Failed to load FreshProxy {proto}:", e)

    # ---- Source 3: ClearProxy ----
    CLEARPROXY_BASE = "https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/"
    CLEARPROXY_PATHS = [
        "http/raw/all.txt",
        "socks4/raw/all.txt",
        "socks5/raw/all.txt"
    ]

    for path in CLEARPROXY_PATHS:
        url = CLEARPROXY_BASE + path
        protocol = path.split("/")[0]
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            for line in r.text.splitlines():
                line = line.strip()
                if line:
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
                if line:
                    proxies.append(f"{proto}://{line}")
        except Exception as e:
            print(f"Failed to load Databay {proto}:", e)

    # ---- Source 5: zebbern Proxy-Scraper ----
    ZEBBERN_BASE = "https://raw.githubusercontent.com/zebbern/Proxy-Scraper/main/"
    ZEBBERN_FILES = {
        "https": "https.txt",
        "socks4": "socks4.txt",
        "socks5": "socks5.txt"
    }

    for proto, filename in ZEBBERN_FILES.items():
        url = ZEBBERN_BASE + filename
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            for line in r.text.splitlines():
                line = line.strip()
                if line:
                    proxies.append(f"{proto}://{line}")
        except Exception as e:
            print(f"Failed to load zebbern {proto}:", e)

    print(f"Loaded total proxies: {len(proxies)}")
    return proxies


SMALL_TEST_URL = "https://speed.cloudflare.com/__down?bytes=50000"
YOUTUBE_URL = "https://www.youtube.com"


# ---------------------------------------------------------
# HTTP/HTTPS TEST (sync, inside threadpool)
# ---------------------------------------------------------

def test_http_proxy(proxy_url, timeout=6):
    proxies = {"http": proxy_url, "https": proxy_url}
    try:
        r = requests.get(SMALL_TEST_URL, proxies=proxies, timeout=timeout, stream=True)
        if r.status_code != 200:
            return False
        _ = next(r.iter_content(1024))
        return True
    except Exception:
        return False


def test_http_youtube(proxy_url, timeout=8):
    proxies = {"http": proxy_url, "https": proxy_url}
    try:
        r = requests.get(YOUTUBE_URL, proxies=proxies, timeout=timeout)
        return r.status_code in (200, 301, 302)
    except Exception:
        return False


# ---------------------------------------------------------
# SOCKS TEST (async)
# ---------------------------------------------------------

async def test_socks_proxy(proxy_url, timeout=6):
    connector = ProxyConnector.from_url(proxy_url)
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(SMALL_TEST_URL, timeout=timeout) as resp:
                if resp.status != 200:
                    return False
                await resp.content.read(1024)
                return True
    except Exception:
        return False


async def test_socks_youtube(proxy_url, timeout=8):
    connector = ProxyConnector.from_url(proxy_url)
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(YOUTUBE_URL, timeout=timeout) as resp:
                return resp.status in (200, 301, 302)
    except Exception:
        return False


# ---------------------------------------------------------
# HYBRID TESTER
# ---------------------------------------------------------

async def test_proxy(idx, total, proxy, sem, threadpool):
    proxy = proxy.strip()

    # Detect protocol
    if proxy.startswith("socks5://"):
        protocol = "socks5"
    elif proxy.startswith("socks4://"):
        protocol = "socks4"
    elif proxy.startswith("https://"):
        protocol = "https"
    elif proxy.startswith("http://"):
        protocol = "http"
    else:
        # assume http://IP:PORT
        protocol = "http"
        proxy = "http://" + proxy

    async with sem:
        # SOCKS proxies → async
        if protocol in ("socks4", "socks5"):
            ok = await test_socks_proxy(proxy)
            if not ok:
                print(f"[{idx}/{total}] ❌ {proxy}")
                return None

            # YouTube test
            y_ok = await test_socks_youtube(proxy)
            if y_ok:
                print(f"[{idx}/{total}] ✅ {proxy} (SOCKS + YouTube OK)")
                return proxy
            else:
                print(f"[{idx}/{total}] ⚠ {proxy} (SOCKS OK, YouTube FAIL)")
                return None

        # HTTP/HTTPS proxies → threadpool
        else:
            ok = await asyncio.get_event_loop().run_in_executor(
                threadpool, test_http_proxy, proxy
            )
            if not ok:
                print(f"[{idx}/{total}] ❌ {proxy}")
                return None

            # YouTube test (optional)
            y_ok = await asyncio.get_event_loop().run_in_executor(
                threadpool, test_http_youtube, proxy
            )
            if y_ok:
                print(f"[{idx}/{total}] ✅ {proxy} (HTTP + YouTube OK)")
                return proxy
            else:
                print(f"[{idx}/{total}] ⚠ {proxy} (HTTP OK, YouTube FAIL)")
                return None


# ---------------------------------------------------------
# MAIN ASYNC RUNNER
# ---------------------------------------------------------

async def run_balanced_test(proxies, limit=5000, concurrency=200):
    random.shuffle(proxies)
    proxies = proxies[:limit]

    total = len(proxies)
    sem = asyncio.Semaphore(concurrency)
    threadpool = ThreadPoolExecutor(max_workers=50)

    tasks = [
        test_proxy(i, total, proxy, sem, threadpool)
        for i, proxy in enumerate(proxies, start=1)
    ]

    results = await asyncio.gather(*tasks)
    valid = [p for p in results if p]

    print("\n----------------------------------")
    print(f"Valid proxies: {len(valid)}")
    #for p in valid:
    #    print(p)
    print("----------------------------------\n")

    return valid


# ---------------------------------------------------------
# Example usage
# ---------------------------------------------------------
from seleniumbase import SB
import base64
urlt = "https://www.youtube.com/watch?v=Lju1aI6P8o0"
name = "YnJ1dGFsbGVz"

name_d = base64.b64decode(name)
fulln = name_d.decode("utf-8")
urlt = f"https://www.twitch.tv/{fulln}"
urlt = f"https://www.youtube.com/@{fulln}"
if __name__ == "__main__":
    # You already have load_proxies() from earlier
    #proxies = load_proxies()
    #ppp = asyncio.run(run_balanced_test(proxies))
    #print(ppp)
    #random.shuffle(ppp)
    p = "http://127.0.0.1:18080"
    k = 0
    if True:
        with SB(uc=True, locale="en",ad_block=True,chromium_arg='--disable-webgl') as peono:
            rnd = random.randint(4,9)
            #if (k == 1):
                #break
            peono.activate_cdp_mode(urlt)
            peono.sleep(5)
            source = peono.get_page_source()
            #print(source)
            bad_indicators = [ "REMOTE_ADDR", "REQUEST_METHOD", "REQUEST_URI", "HTTP_USER_AGENT", "HTTP_ACCEPT", "HTTP_HOST", ]
            if "<html" not in source:
                continue
            if "unusual traffic" in source.lower() or "about this page" in source.lower():
                continue
            if "ERR_SOCKS_CONNECTION_FAILED" in source:
                continue
            if "REMOTE_ADDR" in source:
                continue
            peono.sleep(30)
            if peono.is_element_present('button:contains("Accept")'):
                peono.cdp.click('button:contains("Accept")', timeout=4)
                peono.sleep(10)
            else:
                peono.sleep(10)
                #peono.cdp.gui_press_key('K')
            c = 0
            rndlink = random.randint(1,5)
            peono.cdp.maximize()
            rndsleep = random.randint(60,600)
            while '@brutalles' in peono.cdp.get_current_url():
                if c == 5:
                    break
                try:
                    peono.cdp.scroll_into_view(f'#items > ytd-grid-video-renderer:nth-child({rndlink})')
                    peono.cdp.gui_click_element(f'#items > ytd-grid-video-renderer:nth-child({rndlink})')
                except:
                    rndsleep = random.randint(6,10)
                    break
                peono.sleep(10)
                c+=1
            
            peono.sleep(rndsleep)
            k+=1
            
            print(p)
