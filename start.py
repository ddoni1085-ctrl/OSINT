import random
import re
import time
import sys
import os
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import cloudscraper
import phonenumbers
from phonenumbers import carrier, geocoder, number_type

PLATFORMS = {
    "1": {"name": "Facebook", "url": "https://www.facebook.com/{}"},
    "2": {"name": "Instagram", "url": "https://www.instagram.com/{}"},
    "3": {"name": "TikTok", "url": "https://www.tiktok.com/@{}"},
    "4": {"name": "GitHub", "url": "https://github.com/{}"},
    "5": {"name": "Semua Platform", "url": None}
}

checked_usernames = set()
proxy_list = []

def load_proxies():
    global proxy_list
    if os.path.exists("proxies.txt"):
        with open("proxies.txt", "r") as f:
            proxy_list = [line.strip() for line in f if line.strip()]
        print(f"[*] Berhasil memuat {len(proxy_list)} proxy dari proxies.txt")
    else:
        proxy_list = []

def get_random_proxy():
    if proxy_list:
        p = random.choice(proxy_list)
        return {"http": p, "https": p}
    return None

def generate_base_usernames(target_input):
    clean = target_input.replace(" ", "").lower()
    underscore = target_input.replace(" ", "_").lower()
    dot = target_input.replace(" ", ".").lower()
    return [target_input, clean, underscore, dot, f"real_{clean}", f"{clean}.official", f"{underscore}_official"]

def generate_random_usernames(target_input, amount=3):
    clean = target_input.replace(" ", "").lower()
    underscore = target_input.replace(" ", "_").lower()
    new_variations = []
    
    while len(new_variations) < amount:
        patterns = [
            f"{clean}{random.randint(10, 9999)}",
            f"{underscore}_{random.randint(10, 9999)}",
            f"{clean}.{random.randint(10, 999)}",
            f"official_{clean}{random.randint(1, 99)}",
            f"{clean}_{random.choice(['18', '99', '01', '12', '80', '123', '00'])}"
        ]
        cand = random.choice(patterns)
        if cand not in checked_usernames:
            new_variations.append(cand)
            checked_usernames.add(cand)
    return new_variations

def check_username(platform, url_template, username):
    url = url_template.format(username)
    proxy = get_random_proxy()
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    
    try:
        response = scraper.get(url, proxies=proxy, timeout=12, allow_redirects=True)
        text_lower = response.text.lower()
        final_url = response.url.lower()
        is_valid = False

        match = re.search(r'<title>(.*?)</title>', text_lower)
        page_title = match.group(1).strip() if match else ""

        if platform == "Instagram":
            if page_title == "instagram" or "login" in page_title or "not found" in page_title:
                is_valid = False
            elif f"@{username.lower()}" in text_lower or "followers" in text_lower:
                is_valid = True

        elif platform == "Facebook":
            if "profile.php" in final_url or "login" in final_url or "home.php" in final_url:
                is_valid = False
            elif page_title == "facebook" or "log in" in page_title or "tidak tersedia" in page_title:
                is_valid = False
            elif "content_not_found" in text_lower or "halaman ini tidak tersedia" in text_lower:
                is_valid = False
            else:
                if username.lower() in final_url:
                    is_valid = True

        elif platform == "TikTok":
            if page_title in ["tiktok", "tiktok - make your day"] or "not found" in page_title or response.status_code == 404:
                is_valid = False
            elif f"@{username.lower()}" in page_title:
                is_valid = True
            elif f'"uniqueid":"{username.lower()}"' in text_lower.replace(" ", ""):
                is_valid = True

        elif platform == "GitHub":
            if response.status_code == 200 and page_title != "page not found · github":
                is_valid = True

        if is_valid:
            return f"[+] Ditemukan ({platform}): {url}"
        return None 
    except Exception:
        return None

def process_batch(usernames, platforms):
    sys.stdout.write(f"\r[*] Memeriksa batch: {', '.join(usernames)}...   ")
    sys.stdout.flush()

    found_results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(check_username, p_name, p_url, uname) for uname in usernames for p_name, p_url in platforms.items()]
        for future in as_completed(futures):
            result = future.result()
            if result:
                found_results.append(result)
    
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

    for res in found_results:
        print(res)

def run_bruteforce():
    load_proxies()
    print("\n--- PILIH PLATFORM TARGET ---")
    for key, data in PLATFORMS.items():
        print(f"[{key}] {data['name']}")
    
    choice_plat = input("\nMasukkan nomor platform: ").strip()
    if choice_plat not in PLATFORMS:
        print("[!] Pilihan tidak valid!")
        return

    if choice_plat == "5":
        target_platforms = {v['name']: v['url'] for v in PLATFORMS.values() if v['url'] is not None}
    else:
        selected = PLATFORMS[choice_plat]
        target_platforms = {selected['name']: selected['url']}

    target_name = input("Masukkan Username Dasar (Cth: donidamara): ").strip()
    if not target_name: 
        print("[!] Username tidak boleh kosong!")
        return
    
    print("\n" + "="*50)
    print(f"[*] Target Platform : {', '.join(target_platforms.keys())}")
    print(f"[*] Target Username : {target_name}")
    print(f"[*] Mode: Safe + Proxy Rotation")
    print(f"[*] Tekan CTRL + C untuk berhenti.")
    print("="*50 + "\n")

    base_users = generate_base_usernames(target_name)
    checked_usernames.update(base_users)
    process_batch(base_users, target_platforms)

    try:
        while True:
            rand_users = generate_random_usernames(target_name, amount=3)
            process_batch(rand_users, target_platforms)
            time.sleep(random.uniform(2.0, 5.0))
    except KeyboardInterrupt:
        print(f"\n\n[!] PROGRAM DIHENTIKAN OLEH USER.")
        sys.exit(0)

def generate_search_links(keyword):
    url_keyword = urllib.parse.quote_plus(keyword)
    print(f"\n[*] HASIL PENCARIAN UNTUK: '{keyword}'")
    print(f"[Facebook People] : https://www.facebook.com/search/people/?q={url_keyword}")
    print(f"[TikTok Users]    : https://www.tiktok.com/search/user?q={url_keyword}")
    print(f"[Facebook Posts]  : https://www.facebook.com/search/posts/?q={url_keyword}")
    print(f"[TikTok Videos]   : https://www.tiktok.com/search/video?q={url_keyword}\n")

def generate_email_patterns(target_input):
    clean = target_input.replace(" ", "").lower()
    parts = target_input.split()
    emails = {f"{clean}@gmail.com", f"{clean}@yahoo.com", f"{clean}@outlook.com"}
    if len(parts) >= 2:
        first, last = parts[0].lower(), parts[-1].lower()
        emails.update({f"{first}.{last}@gmail.com", f"{first}{last}@gmail.com", f"{first}_{last}@gmail.com"})
    
    print(f"\n[*] Kemungkinan Email untuk '{target_input}':")
    for em in sorted(emails):
        print(f" - {em}")

# ==========================================
# FITUR 5: SMART PHONE CROSS-PLATFORM CHECKER
# ==========================================
def smart_phone_lookup(phone_input):
    print(f"\n[*] Menganalisis nomor ponsel: {phone_input}...")
    
    try:
        parsed_number = phonenumbers.parse(phone_input, "ID")
        if not phonenumbers.is_possible_number(parsed_number):
            print("[!] Format nomor tidak valid.")
            return

        intl_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        e164_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        raw_digits = e164_format.replace("+", "")
        
        country_location = geocoder.description_for_number(parsed_number, "id")
        provider = carrier.name_for_number(parsed_number, "id")
        n_type = number_type(parsed_number)
        type_str = "Seluler (Mobile)" if n_type == phonenumbers.PhoneNumberType.MOBILE else "Telepon Rumah"

        print("\n" + "="*50)
        print("📊 LAPORAN INTELIJEN NOMOR PONSEL")
        print("="*50)
        print(f" [+] Nomor Asli        : {intl_format}")
        print(f" [+] Jenis & Provider  : {type_str} ({provider if provider else 'Unknown'})")
        print(f" [+] Wilayah Asal      : {country_location if country_location else 'Indonesia'}")
        
        print("\n=== 🔗 URL AKUN & JALUR PENGHUBUNG SOSMED ===")
        print(f" [✓] WhatsApp Account  : https://wa.me/{raw_digits}")
        print(f" [✓] Telegram Account  : https://t.me/+{raw_digits}")
        print(f" [✓] Truecaller Direct : https://www.truecaller.com/search/id/{raw_digits}")
        
        print("\n=== 🔎 PENCARIAN JEJAK NOMOR DI PLATFORM SOSIAL ===")
        # Membuat URL pencarian spesifik di platform utama agar script yang meracik link pencariannya
        print(f" [🌐] Cari di Facebook   : https://www.facebook.com/search/top/?q={e164_format}")
        print(f" [🌐] Cari di Instagram  : https://www.google.com/search?q=site:instagram.com+\"{raw_digits}\"")
        print(f" [🌐] Cari di TikTok     : https://www.google.com/search?q=site:tiktok.com+\"{raw_digits}\"")
        print(f" [🌐] Jejak Global Web   : https://www.google.com/search?q=\"{e164_format}\"")
        print("="*50)

    except Exception as e:
        print(f"[!] Gagal menganalisis nomor: {e}")

def main():
    load_proxies()
    while True:
        print("\n=== ULTIMATE OSINT TOOLKIT (SMART & PRO) ===")
        print("[1] Bruteforce Username (Mencari Kombinasi Acak)")
        print("[2] Cari Berdasarkan NAMA ASLI")
        print("[3] Cari Keyword di POSTINGAN / VIDEO")
        print("[4] Cari / Generate Kombinasi Email (Gmail OSINT)")
        print("[5] Lacak Nomor Ponsel & Cross-Platform Link Generator")
        print("[0] Keluar")
        
        choice = input("Pilih Menu (0-5): ").strip()
        
        if choice == "1":
            run_bruteforce()
        elif choice in ["2", "3"]:
            keyword = input("Masukkan Nama/Keyword: ").strip()
            if keyword: generate_search_links(keyword)
        elif choice == "4":
            keyword = input("Masukkan Nama/Username Target: ").strip()
            if keyword: generate_email_patterns(keyword)
        elif choice == "5":
            phone = input("Masukkan Nomor Ponsel (Cth: 08123456789): ").strip()
            if phone: smart_phone_lookup(phone)
        elif choice == "0":
            print("Keluar dari program. Mantap coy!")
            sys.exit(0)
        else:
            print("[!] Pilihan tidak valid!")

if __name__ == "__main__":
    main()
