import requests
import json
import os
from datetime import datetime
import time
import sys
import threading

YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"
SPINNER = ['|', '/', '-', '\\']
mt_status_file = "mt_status.json"

# Ganti dengan token dan chat_id kamu
TOKEN_BOT = os.environ.get("TOKEN_BOT")
CHAT_ID = os.environ.get("CHAT_ID")

def nowstr():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def kirim_telegram(token, chat_id, pesan):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": pesan,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Gagal kirim ke Telegram: {e}")

def cek_mt(print_change=True, token=None, chat_id=None):
    url = "https://indodax.com/api/pairs"
    response = requests.get(url)
    data = response.json()

    mt_now = {}
    for pair in data:
        mt_now[pair['symbol']] = 1 if pair.get("is_maintenance") == 1 else 0

    mt_last = {}
    if os.path.exists(mt_status_file):
        with open(mt_status_file, "r") as f:
            try:
                mt_last = json.load(f)
            except:
                mt_last = {}

    changed = False
    for symbol, status in mt_now.items():
        last_status = mt_last.get(symbol, {}).get("status")
        if last_status is None or last_status != status:
            changed = True
            waktu = nowstr()
            if print_change:
                if status == 1:
                    pesan = f"⚠️ <b>{symbol}</b> masuk maintenance pada {waktu}"
                    print(f"{YELLOW}{symbol} masuk maintenance pada {waktu}{RESET}")
                else:
                    pesan = f"✅ <b>{symbol}</b> keluar dari maintenance pada {waktu}"
                    print(f"{GREEN}{symbol} keluar dari maintenance pada {waktu}{RESET}")
                if token and chat_id:
                    kirim_telegram(token, chat_id, pesan)
            mt_last[symbol] = {"status": status, "last_change": waktu}
        else:
            mt_last[symbol] = mt_last[symbol]

    with open(mt_status_file, "w") as f:
        json.dump(mt_last, f, indent=2)

    return changed

def spinner_animation(stop_event):
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\rMenunggu update berikutnya {SPINNER[i % len(SPINNER)]}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * 40 + "\r")  # Bersihkan baris

def run_maintenance():
    interval = 10  # detik
    try:
        while True:
            changed = cek_mt(print_change=True, token=TOKEN_BOT, chat_id=CHAT_ID)
            stop_event = threading.Event()
            t = threading.Thread(target=spinner_animation, args=(stop_event,))
            t.start()
            try:
                for _ in range(interval * 10):  # 0.1 detik x 10 = 1 detik
                    time.sleep(0.1)
            except KeyboardInterrupt:
                stop_event.set()
                t.join()
                print("\nDihentikan oleh user (Ctrl+C).")
                return
            stop_event.set()
            t.join()
    except KeyboardInterrupt:
        print("\nDihentikan oleh user (Ctrl+C).")

def tampilkan_koin_maintenance():
    if not os.path.exists(mt_status_file):
        print("Belum ada data maintenance. Jalankan menu 1 dulu.")
        return
    with open(mt_status_file, "r") as f:
        mt_last = json.load(f)
    found = False
    print(f"{YELLOW}Koin yang sedang maintenance:{RESET}")
    nomor = 1
    for symbol, info in mt_last.items():
        if info.get("status") == 1:
            found = True
            print(f"{nomor}. {symbol} (sejak {info.get('last_change', '-')})")
            nomor += 1
    if not found:
        print("Tidak ada koin yang sedang maintenance.")

def main_menu():
    while True:
        print("\n\033[94m=== MENU MONITORING MAINTENANCE KOIN INDODAX ===\033[0m")
        print("1. Jalankan program run maintenance (monitor perubahan)")
        print("2. Koin yang sedang maintenance (beserta tanggalnya)")
        print("3. Keluar program")
        pilihan = input("Pilih menu (1/2/3): ").strip()
        if pilihan == "1":
            run_maintenance()
        elif pilihan == "2":
            tampilkan_koin_maintenance()
        elif pilihan == "3":
            print("Keluar dari program.")
            break
        else:
            print("Pilihan tidak valid. Silakan pilih 1, 2, atau 3.")

if __name__ == "__main__":
    run_maintenance()
