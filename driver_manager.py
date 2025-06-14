
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import stat
import glob

class DriverManager:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        # Railway/Production optimizations
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            # Use system Chrome in production
            if os.environ.get("RAILWAY_ENVIRONMENT"):
                # Railway provides Chrome binary
                chrome_options.binary_location = "/usr/bin/google-chrome"
                service = Service("/usr/bin/chromedriver")
            else:
                # Local development - try different approaches
                print("Setting up ChromeDriver for local development...")
                
                # Try homebrew installation first
                homebrew_paths = [
                    "/opt/homebrew/bin/chromedriver",  # M1 Mac
                    "/usr/local/bin/chromedriver"      # Intel Mac
                ]
                
                driver_path = None
                for path in homebrew_paths:
                    if os.path.exists(path) and os.access(path, os.X_OK):
                        driver_path = path
                        print(f"Found Homebrew ChromeDriver at: {driver_path}")
                        break
                
                if not driver_path:
                    # Try webdriver-manager but fix the path issue
                    try:
                        downloaded_path = ChromeDriverManager().install()
                        print(f"Downloaded ChromeDriver to: {downloaded_path}")
                        
                        # Fix the common THIRD_PARTY_NOTICES issue
                        if downloaded_path.endswith('THIRD_PARTY_NOTICES.chromedriver'):
                            # Look for the actual chromedriver in the same directory
                            dir_path = os.path.dirname(downloaded_path)
                            print(f"Looking for actual chromedriver in: {dir_path}")
                            
                            # Try different possible names
                            possible_names = ['chromedriver', 'chromedriver-mac-arm64', 'chromedriver-mac-x64']
                            for name in possible_names:
                                actual_driver = os.path.join(dir_path, name)
                                if os.path.exists(actual_driver) and not actual_driver.endswith('THIRD_PARTY_NOTICES.chromedriver'):
                                    driver_path = actual_driver
                                    print(f"Found actual ChromeDriver at: {driver_path}")
                                    break
                            
                            # If not found, try glob pattern search
                            if not driver_path:
                                pattern = os.path.join(dir_path, "*chromedriver*")
                                matches = glob.glob(pattern)
                                for match in matches:
                                    if not match.endswith('THIRD_PARTY_NOTICES.chromedriver') and os.access(match, os.X_OK):
                                        driver_path = match
                                        print(f"Found ChromeDriver via glob: {driver_path}")
                                        break
                        else:
                            driver_path = downloaded_path
                        
                        # Make sure it's executable
                        if driver_path and os.path.exists(driver_path):
                            os.chmod(driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                            print(f"Made ChromeDriver executable: {driver_path}")
                        
                    except Exception as e:
                        print(f"WebDriver manager failed: {str(e)}")
                        driver_path = None
                
                if not driver_path:
                    raise Exception("No valid chromedriver found. Please install ChromeDriver using 'brew install chromedriver' or manually download it")
                
                service = Service(driver_path)
                print(f"Using ChromeDriver at: {driver_path}")
                
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            print(f"Error setting up Chrome WebDriver: {str(e)}")
            raise Exception(f"Could not initialize Chrome WebDriver: {str(e)}")
    
    def get_driver(self):
        """Get the WebDriver instance."""
        return self.driver
    
    def close(self):
        """Close the WebDriver."""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
        except:
            pass
