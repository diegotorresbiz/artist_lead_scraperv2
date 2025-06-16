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
        
        # Check if we're in production environment
        is_production = (os.environ.get("RAILWAY_ENVIRONMENT") or 
                        os.environ.get("RENDER") or 
                        os.environ.get("HEROKU") or
                        os.environ.get("NODE_ENV") == "production")
        print(f"   Production Environment: {is_production}")
        
        # Check Chrome binary locations
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable", 
            "/usr/bin/chromium-browser",
            "/opt/google/chrome/chrome",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
            "/nix/store/*/bin/google-chrome",
            "/nix/store/*/bin/google-chrome-stable",
            "/nix/store/*/bin/chromium",
            "/nix/store/*/bin/chromium-browser"
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
        
        # Try to get Chrome version
        if chrome_found:
            try:
                result = subprocess.run([chrome_found, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    chrome_version = result.stdout.strip()
                    print(f"   ✅ Chrome version: {chrome_version}")
                    
                    # Extract major version number for ChromeDriver compatibility
                    import re
                    version_match = re.search(r'(\d+)\.\d+\.\d+\.\d+', chrome_version)
                    if version_match:
                        major_version = version_match.group(1)
                        print(f"   📋 Chrome major version: {major_version}")
                        return chrome_found, major_version
                else:
                    print(f"   ❌ Chrome version check failed: {result.stderr}")
            except Exception as e:
                print(f"   ❌ Chrome version check error: {str(e)}")
        
        return chrome_found, None
    
    def find_chromedriver_executable(self, base_path):
        """Find the actual ChromeDriver executable from webdriver-manager download path."""
        print(f"   🔍 Searching for ChromeDriver executable in: {base_path}")
        
        # Common ChromeDriver executable names
        driver_names = ['chromedriver', 'chromedriver.exe']
        
        # First, check if the base_path is already the executable
        if os.path.basename(base_path) in driver_names and os.access(base_path, os.X_OK):
            print(f"   ✅ Direct executable found: {base_path}")
            return base_path
        
        # Get the directory from the base path
        if os.path.isfile(base_path):
            search_dir = os.path.dirname(base_path)
        else:
            search_dir = base_path
        
        print(f"   🔍 Searching in directory: {search_dir}")
        
        # Search in the directory and subdirectories
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file in driver_names:
                    full_path = os.path.join(root, file)
                    if os.access(full_path, os.X_OK):
                        print(f"   ✅ Found ChromeDriver executable: {full_path}")
                        return full_path
        
        # If not found, try to find any file with 'chromedriver' in the name
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if 'chromedriver' in file.lower() and not file.endswith('.txt'):
                    full_path = os.path.join(root, file)
                    # Make it executable if it isn't already
                    try:
                        os.chmod(full_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                        if os.access(full_path, os.X_OK):
                            print(f"   ✅ Found and made executable: {full_path}")
                            return full_path
                    except Exception as e:
                        print(f"   ⚠️ Could not make executable: {full_path} - {str(e)}")
        
        print(f"   ❌ No ChromeDriver executable found in {search_dir}")
        return None
    
    def setup_driver(self):
        """Set up the Chrome WebDriver with crash-resistant options."""
        print("\n🚀 SETTING UP CRASH-RESISTANT CHROME WEBDRIVER")
        
        try:
            # Check system dependencies first
            chrome_binary, chrome_major_version = self.check_system_dependencies()
            
            chrome_options = Options()
            
            # Production/Cloud environment optimizations
            is_production = (os.environ.get("RAILWAY_ENVIRONMENT") or 
                            os.environ.get("RENDER") or 
                            os.environ.get("HEROKU") or
                            os.environ.get("NODE_ENV") == "production")
            
            # Initialize driver_path to None
            driver_path = None
            
            if is_production:
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
                
                # CRITICAL: Process stability
                chrome_options.add_argument("--single-process")
                chrome_options.add_argument("--no-zygote")
                chrome_options.add_argument("--disable-ipc-flooding-protection")
                
                # CRITICAL: Reduce resource usage to prevent crashes
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-images")
                chrome_options.add_argument("--disable-javascript")
                chrome_options.add_argument("--disable-default-apps")
                chrome_options.add_argument("--disable-sync")
                
                # CRITICAL: Window and display - smaller to save memory
                chrome_options.add_argument("--window-size=800,600")
                chrome_options.add_argument("--virtual-time-budget=10000")
                
                # User agent
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                # CRITICAL: Crash recovery options
                chrome_options.add_argument("--disable-crash-reporter")
                chrome_options.add_argument("--disable-logging")
                chrome_options.add_argument("--silent")
                
                if chrome_binary:
                    chrome_options.binary_location = chrome_binary
                    print(f"   Using Chrome: {chrome_binary}")
                else:
                    raise Exception("❌ Chrome binary not found in production environment")
                
                # Download compatible ChromeDriver using webdriver-manager
                print("   🔄 Downloading compatible ChromeDriver...")
                try:
                    # Use webdriver-manager to auto-download compatible version
                    downloaded_path = ChromeDriverManager().install()
                    print(f"   Downloaded ChromeDriver to: {downloaded_path}")
                    
                    # Find the actual executable
                    driver_path = self.find_chromedriver_executable(downloaded_path)
                    
                    if not driver_path:
                        raise Exception("Could not locate ChromeDriver executable after download")
                    
                    # Ensure executable permissions
                    os.chmod(driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                    print(f"   ✅ Using compatible ChromeDriver: {driver_path}")
                    
                    # Verify ChromeDriver version
                    try:
                        result = subprocess.run([driver_path, "--version"], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            print(f"   ✅ ChromeDriver version: {result.stdout.strip()}")
                    except Exception as e:
                        print(f"   ⚠️  ChromeDriver version check failed: {str(e)}")
                    
                except Exception as e:
                    print(f"   ❌ ChromeDriver download failed: {str(e)}")
                    raise Exception(f"ChromeDriver not available: {str(e)}")
                
            else:
                # Local development settings
                print("💻 Local development environment detected")
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--window-size=1920,1080")
                
                # Try webdriver-manager for local development
                print("   Attempting to download compatible ChromeDriver...")
                try:
                    downloaded_path = ChromeDriverManager().install()
                    print(f"   Downloaded ChromeDriver to: {downloaded_path}")
                    
                    # Find the actual executable
                    driver_path = self.find_chromedriver_executable(downloaded_path)
                    
                    if not driver_path:
                        raise Exception("Could not locate ChromeDriver executable after download")
                    
                    # Ensure executable permissions
                    os.chmod(driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                    
                except Exception as e:
                    print(f"   WebDriver manager failed: {str(e)}")
                    raise Exception(f"ChromeDriver setup failed: {str(e)}")
            
            # Ensure we have a valid driver_path before creating the service
            if not driver_path:
                raise Exception("ChromeDriver path not set - setup failed")
            
            service = Service(driver_path)
            
            print("🔧 Initializing crash-resistant WebDriver...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # CRITICAL: Conservative timeouts to prevent hangs/crashes
            self.driver.set_page_load_timeout(15)
            self.driver.implicitly_wait(5)
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
            if "This version of ChromeDriver only supports Chrome version" in str(e):
                print("\n🔍 CHROME/CHROMEDRIVER VERSION MISMATCH:")
                print("   The ChromeDriver version doesn't match your Chrome version")
                print("   webdriver-manager should auto-download compatible version")
                print("   This error suggests the auto-download failed")
            elif "Chrome binary" in str(e) or "chrome" in str(e).lower():
                print("\n🔍 CHROME INSTALLATION ISSUE:")
                print("   Try: Make sure Chrome is installed: apt-get install -y google-chrome-stable")
                print("   Or: Use chromium: apt-get install -y chromium-browser")
            elif "chromedriver" in str(e).lower():
                print("\n🔍 CHROMEDRIVER ISSUE:")
                print("   ChromeDriver will be downloaded automatically")
                print("   Check Chrome and ChromeDriver version compatibility")
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
