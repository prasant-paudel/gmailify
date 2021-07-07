import requests
import threading
import queue
import argparse
import re
import sys
import time
from shutil import get_terminal_size

TERM_WIDTH = get_terminal_size()[0]
total_emails = queue.Queue()
valid_emails = []
threads = []

def argsParser():
    parser = argparse.ArgumentParser(description="Validate google emails without being authenticated")
    parser.add_argument("file", type=argparse.FileType('r'), help="File containing an email per line")
    parser.add_argument("-o", "--output", help="Output valid emails in a file", type=argparse.FileType('w'))
    parser.add_argument("-e", "--email", help="pass an email")
    parser.add_argument("-n", "--nossl", help="Disable SSL",action="store_false")
    parser.add_argument("-p", "--proxy", help="Proxy server to pass requests through -p http://127.0.0.1:8080")
    return parser.parse_args()

def check(args):

    proxies={}
    if args.proxy is not None:
        proxies = {"http":args.proxy,"https":args.proxy}

    _num_of_emails = total_emails.qsize()
    while not total_emails.empty():
        show_progress(_num_of_emails, _num_of_emails - total_emails.qsize())
        try:
            email = total_emails.get(False)
            requests.packages.urllib3.disable_warnings()
            email = re.sub(r'\+.*@', '@', email)
            resp = requests.get(f'https://mail.google.com/mail/gxlu', params={'email': email} , proxies=proxies , verify=args.nossl)
            for cookie in resp.cookies:
                if cookie.name == "COMPASS":
                    valid_emails.append(email)
                    clear_line()
                    print(email)
        except requests.exceptions.SSLError as e:
            print("SSL Error. Consider using -n flag to disable SSL errors")
        time.sleep(0.03)

def clear_line() -> None:
    print(f"\r{TERM_WIDTH*' '}\r", end="", flush=True)
    
def show_progress(total:int, progress:int) -> None:
    clear_line()
    percentile = progress/total*100
    bar = "\u2588" * int(percentile/5) + " "* (20 - int(percentile/5))
    print(f"Progress: {progress}/{total} --|{bar}|-- ({percentile:.2f}%)", end="\r")

def main():
    args = argsParser()


    with args.file as emails:
        for email in emails:
            email = email.rstrip("\n")
            total_emails.put(email)

    for i in range(10):
        t = threading.Thread(target=check,args=(args,))
        t.daemon = True
        t.start()
        threads.append(t)
      
    for t in threads:
        t.join()

    if total_emails.empty():
        if args.output is not None:
            for i in valid_emails:
                args.output.write(i + "\n")
                args.output.flush()

if __name__ == "__main__":
	main() 
