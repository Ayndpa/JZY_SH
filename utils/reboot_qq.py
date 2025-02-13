import subprocess
import time
import threading
import requests
import json
from extensions import config, logger

def check_qq_api():
    try:
        api_url = f"{config['forward_api_url']}"
        headers = {'Authorization': 'Bearer ' + config['forward_api_token']}
        
        response = requests.get(api_url, headers=headers)
        return response.status_code == 200
    except:
        return False

def check_qq_screen():
    result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
    return 'qq' in result.stdout

def qq_monitor():
    while True:
        if check_qq_screen() and check_qq_api():
            logger.info("QQ running normally, monitor thread ending")
            break
        if not check_qq_screen() and not check_qq_api():
            logger.info("QQ abnormal, attempting restart...")
            reboot_qq()
        time.sleep(5)  # Check every 5 seconds

def reboot_qq():
    try:
        # Kill existing QQ screen session
        subprocess.run(['screen', '-S', 'qq', '-X', 'quit'], check=False)

        time.sleep(5)  # Wait 5 seconds before starting new session
        
        # Start new QQ screen session
        subprocess.run([
            'screen', '-S', 'qq', '-dm', 
            'xvfb-run', '-a', 'qq', '--no-sandbox', 
            '-q', '3028251597'
        ], check=False)

        # Start monitor thread on first run
        if threading.active_count() == 1:  # 只有主线程在运行
            monitor_thread = threading.Thread(target=qq_monitor, daemon=True)
            monitor_thread.start()
            logger.info("QQ monitor thread started")
        
        return True
    except Exception as e:
        logger.error(f"Failed to reboot QQ: {str(e)}")
        return False