from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import stat
import glob
import subprocess
import shutil

class DriverManager:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def check_system_dependencies(self):
        """Check if Chrome and ChromeDriver are available in the system."""
        print("\n🔍 SYSTEM DEPENDENCY CHECK:")
        
        # Check if we're in Railway environment
        is_railway = os.environ.get("RAILWAY_ENVIRONMENT")
        print(f"   Railway Environment: {is_railway}")
        
        # Check Chrome binary locations - including Nixpacks paths
        chrome_paths = [
            # Nixpacks paths (Railway with nixpacks.toml)
            "/nix/store/*/bin/google-chrome",
            "/nix/store/*/bin/google-chrome-stable",
            "/nix/store/*/bin/chromium",
            "/nix/store/*/bin/chromium-browser",
            # Traditional paths
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable", 
            "/usr/bin/chromium-browser",
            "/opt/google/chrome/chrome",
            "/usr/bin/chromium",
            "/snap/bin/chromium"
        ]
        
        chrome_found = None
        for path_pattern in chrome_paths:
            # Handle glob patterns for nixpacks
            if "*" in path_pattern:
                matching_paths = glob.glob(path_pattern)
                for path in matching_paths:
                    if os.path.exists(path) and os.access(path, os.X_OK):
                        print(f"   ✅ Chrome found at: {path}")
                        chrome_found = path
                        break
            else:
                if os.path.exists(path_pattern):
                    print(f"   ✅ Chrome found at: {path_pattern}")
                    chrome_found = path_pattern
                    break
                else:
                    print(f"   ❌ Chrome not found at: {path_pattern}")
            
            if chrome_found:
                break
        
        # Check ChromeDriver locations - including Nixpacks paths
        driver_paths = [
            # Nixpacks paths
            "/nix/store/*/bin/chromedriver",
            # Traditional paths
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
            "/opt/homebrew/bin/chromedriver",
            "/snap/bin/chromedriver"
        ]
        
        driver_found = None
        for path_pattern in driver_paths:
            # Handle glob patterns for nixpacks
            if "*" in path_pattern:
                matching_paths = glob.glob(path_pattern)
                for path in matching_paths:
                    if os.path.exists(path) and os.access(path, os.X_OK):
                        print(f"   ✅ ChromeDriver found at: {path}")
                        driver_found = path
                        break
            else:
                if os.path.exists(path_pattern):
                    print(f"   ✅ ChromeDriver found at: {path_pattern}")
                    # Check if it's executable
                    if os.access(path_pattern, os.X_OK):
                        print(f"   ✅ ChromeDriver is executable")
                        driver_found = path_pattern
                    else:
                        print(f"   ⚠️  ChromeDriver exists but not executable")
                        try:
                            os.chmod(path_pattern, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                            print(f"   ✅ Made ChromeDriver executable")
                            driver_found = path_pattern
                        except Exception as e:
                            print(f"   ❌ Could not make executable: {e}")
                    break
                else:
                    print(f"   ❌ ChromeDriver not found at: {path_pattern}")
            
            if driver_found:
                break
        
        # Try to get Chrome version
        if chrome_found:
            try:
                result = subprocess.run([chrome_found, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"   ✅ Chrome version: {result.stdout.strip()}")
                else:
                    print(f"   ❌ Chrome version check failed: {result.stderr}")
            except Exception as e:
                print(f"   ❌ Chrome version check error: {str(e)}")
        
        # Try to get ChromeDriver version
        if driver_found:
            try:
                result = subprocess.run([driver_found, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"   ✅ ChromeDriver version: {result.stdout.strip()}")
                else:
                    print(f"   ❌ ChromeDriver version check failed: {result.stderr}")
            except Exception as e:
                print(f"   ❌ ChromeDriver version check error: {str(e)}")
        
        return chrome_found, driver_found
    
    def setup_driver(self):
        """Set up the Chrome WebDriver with crash-resistant options."""
        print("\n🚀 SETTING UP CRASH-RESISTANT CHROME WEBDRIVER")
        
        try:
            # Check system dependencies first
            chrome_binary, driver_path = self.check_system_dependencies()
            
            chrome_options = Options()
            
            # Enhanced Railway/Production optimizations
            if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RENDER") or os.environ.get("HEROKU"):
                print("🚂 Production environment detected - applying crash prevention")
                
                # Core stability options - CRITICAL for preventing crashes
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-software-rasterizer")
                
                # CRITICAL: Memory management to prevent crashes
                chrome_options.add_argument("--max_old_space_size=512")
                chrome_options.add_argument("--memory-pressure-off")
                chrome_options.add_argument("--max-memory-usage=512")
                chrome_options.add_argument("--aggressive-cache-discard")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-backgrounding-occluded-windows")
                chrome_options.add_argument("--disable-renderer-backgrounding")
                
                # CRITICAL: Process stability
                chrome_options.add_argument("--single-process")
                chrome_options.add_argument("--no-zygote")
                chrome_options.add_argument("--disable-ipc-flooding-protection")
                chrome_options.add_argument("--disable-web-security")
                
                # CRITICAL: Reduce resource usage to prevent crashes
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-images")  # Save memory
                chrome_options.add_argument("--disable-javascript")  # Save CPU/memory
                chrome_options.add_argument("--disable-default-apps")
                chrome_options.add_argument("--disable-sync")
                chrome_options.add_argument("--disable-translate")
                chrome_options.add_argument("--disable-features=VizDisplayCompositor,TranslateUI")
                
                # CRITICAL: Network and loading optimizations
                chrome_options.add_argument("--disable-background-networking")
                chrome_options.add_argument("--disable-background-mode")
                chrome_options.add_argument("--disable-client-side-phishing-detection")
                chrome_options.add_argument("--disable-component-update")
                chrome_options.add_argument("--disable-domain-reliability")
                chrome_options.add_argument("--disable-field-trial-config")
                
                # CRITICAL: Window and display - smaller to save memory
                chrome_options.add_argument("--window-size=800,600")  # Smaller window
                chrome_options.add_argument("--virtual-time-budget=10000")  # Shorter timeout
                chrome_options.add_argument("--disable-accelerated-2d-canvas")
                chrome_options.add_argument("--disable-accelerated-video-decode")
                
                # CRITICAL: User agent
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                # CRITICAL: Crash recovery options
                chrome_options.add_argument("--disable-crash-reporter")
                chrome_options.add_argument("--disable-logging")
                chrome_options.add_argument("--silent")
                chrome_options.add_argument("--disable-breakpad")
                
                # Additional memory and stability options
                chrome_options.add_argument("--disable-hang-monitor")
                chrome_options.add_argument("--disable-prompt-on-repost")
                chrome_options.add_argument("--disable-client-side-phishing-detection")
                chrome_options.add_argument("--disable-component-extensions-with-background-pages")
                
                if not chrome_binary:
                    # Try alternative Chrome detection methods with nixpacks paths
                    alternative_patterns = [
                        "/nix/store/*/bin/google-chrome-stable",
                        "/nix/store/*/bin/chromium-browser", 
                        "/nix/store/*/bin/chromium",
                        "/usr/bin/google-chrome-stable",
                        "/usr/bin/chromium-browser",
                        "/usr/bin/chromium",
                        "/snap/bin/chromium"
                    ]
                    
                    for alt_pattern in alternative_patterns:
                        if "*" in alt_pattern:
                            matching_paths = glob.glob(alt_pattern)
                            for alt_path in matching_paths:
                                if os.path.exists(alt_path) and os.access(alt_path, os.X_OK):
                                    chrome_binary = alt_path
                                    print(f"   🔄 Using alternative Chrome: {chrome_binary}")
                                    break
                        else:
                            if os.path.exists(alt_pattern):
                                chrome_binary = alt_pattern
                                print(f"   🔄 Using alternative Chrome: {chrome_binary}")
                                break
                        
                        if chrome_binary:
                            break
                
                if not chrome_binary:
                    raise Exception("❌ Chrome binary not found. Make sure nixpacks.toml includes 'google-chrome' in nixPkgs")
                
                if not driver_path:
                    raise Exception("❌ ChromeDriver not found. Make sure nixpacks.toml includes 'chromedriver' in nixPkgs")
                
                chrome_options.binary_location = chrome_binary
                service = Service(driver_path)
                print(f"   Using Chrome: {chrome_binary}")
                print(f"   Using ChromeDriver: {driver_path}")
                
            else:
                # Local development settings
                print("💻 Local development environment detected")
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--window-size=1920,1080")
                
                if driver_path:
                    service = Service(driver_path)
                    print(f"   Using system ChromeDriver: {driver_path}")
                else:
                    # Try webdriver-manager as fallback
                    print("   Attempting to download ChromeDriver...")
                    try:
                        downloaded_path = ChromeDriverManager().install()
                        print(f"   Downloaded ChromeDriver to: {downloaded_path}")
                        
                        # Handle THIRD_PARTY_NOTICES issue
                        if 'THIRD_PARTY_NOTICES' in downloaded_path:
                            dir_path = os.path.dirname(downloaded_path)
                            possible_drivers = glob.glob(os.path.join(dir_path, "*chromedriver*"))
                            for possible in possible_drivers:
                                if 'THIRD_PARTY_NOTICES' not in possible and os.access(possible, os.X_OK):
                                    driver_path = possible
                                    print(f"   Found actual ChromeDriver: {driver_path}")
                                    break
                        else:
                            driver_path = downloaded_path
                        
                        if not driver_path:
                            raise Exception("Could not locate ChromeDriver after download")
                        
                        # Ensure executable permissions
                        os.chmod(driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                        service = Service(driver_path)
                        
                    except Exception as e:
                        print(f"   WebDriver manager failed: {str(e)}")
                        raise Exception(f"ChromeDriver setup failed: {str(e)}")
            
            print("🔧 Initializing crash-resistant WebDriver...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # CRITICAL: Conservative timeouts to prevent hangs/crashes
            self.driver.set_page_load_timeout(15)  # Much shorter timeout
            self.driver.implicitly_wait(5)  # Shorter wait
            print("✅ Crash-resistant Chrome WebDriver initialized successfully")
            
            # Test the driver
            print("🧪 Testing WebDriver functionality...")
            self.driver.get("about:blank")
            print("✅ WebDriver test successful")
            
        except Exception as e:
            error_msg = f"💥 WebDriver setup failed: {str(e)}"
            print(error_msg)
            print(f"   Exception type: {type(e).__name__}")
            
            # Enhanced error diagnostics
            if "Chrome binary" in str(e) or "chrome" in str(e).lower():
                print("\n🔍 CHROME INSTALLATION ISSUE:")
                print("   Try: Make sure nixpacks.toml includes 'google-chrome' in nixPkgs")
                print("   Or: apt-get install -y chromium-browser")
            elif "chromedriver" in str(e).lower():
                print("\n🔍 CHROMEDRIVER ISSUE:")
                print("   Try: Make sure nixpacks.toml includes 'chromedriver' in nixPkgs")
                print("   Check version compatibility between Chrome and ChromeDriver")
            elif "timeout" in str(e).lower():
                print("\n🔍 TIMEOUT ISSUE:")
                print("   Chrome may be taking too long to start")
                print("   Consider increasing timeout or checking system resources")
            elif "disconnected" in str(e).lower() or "renderer" in str(e).lower():
                print("\n🔍 CHROME CRASH ISSUE:")
                print("   Chrome renderer crashed - likely due to resource constraints")
                print("   This is common in containerized environments")
            
            raise Exception(f"WebDriver initialization failed: {str(e)}")
    
    def get_driver(self):
        """Get the WebDriver instance."""
        if not self.driver:
            raise Exception("WebDriver not initialized. Call setup_driver() first.")
        return self.driver
        
    def restart_driver_if_crashed(self):
        """Restart the driver if it has crashed."""
        try:
            # Test if driver is still responsive
            self.driver.current_url
            return True
        except Exception as e:
            print(f"⚠️ Driver appears to have crashed: {str(e)}")
            print("🔄 Attempting to restart driver...")
            try:
                self.close()
                self.setup_driver()
                print("✅ Driver restarted successfully")
                return True
            except Exception as restart_error:
                print(f"❌ Failed to restart driver: {str(restart_error)}")
                return False
    
    def close(self):
        """Close the WebDriver safely."""
        try:
            if hasattr(self, 'driver') and self.driver:
                print("🔒 Closing WebDriver...")
                self.driver.quit()
                self.driver = None
                print("✅ WebDriver closed successfully")
        except Exception as e:
            print(f"⚠️  Error closing WebDriver: {str(e)}")
            # Force cleanup
            try:
                if hasattr(self, 'driver') and self.driver:
                    self.driver = None
            except:
                pass
