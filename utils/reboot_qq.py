import subprocess

def reboot_qq():
    try:
        # Kill existing QQ screen session
        subprocess.run(['screen', '-S', 'qq', '-X', 'quit'], check=False)
        
        # Start new QQ screen session
        subprocess.run([
            'screen', '-S', 'qq', '-dm', 
            'xvfb-run', '-a', 'qq', '--no-sandbox', 
            '-q', '3028251597'
        ], check=False)
        
        return True
    except Exception as e:
        print(f"Error rebooting QQ: {str(e)}")
        return False

if __name__ == "__main__":
    reboot_qq()