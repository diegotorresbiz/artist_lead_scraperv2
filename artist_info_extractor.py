from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import unquote, urlparse, parse_qs
import time
import re
from typing import Dict

class ArtistInfoExtractor:
    def __init__(self, driver):
        self.driver = driver
    
    def scrape_artist_info(self, artist_url: str) -> Dict:
        """Scrape contact information from an artist's SoundCloud profile."""
        try:
            print(f"Scraping artist info from: {artist_url}")
            
            # Enhanced system page detection
            system_indicators = [
                'terms-of-use', 'pages', 'imprint', 'upload', 'feed', 'charts',
                'privacy', 'copyright', 'security', 'community-guidelines',
                'help', 'jobs', 'developers', 'blog', 'creators', 'advertising'
            ]
            
            if any(indicator in artist_url.lower() for indicator in system_indicators):
                print(f"   ❌ Skipping system page: {artist_url}")
                return None
            
            self.driver.get(artist_url)
            time.sleep(3)
            
            # Check for error pages
            page_text = self.driver.page_source.lower()
            error_indicators = [
                'can\'t find that page', 'page not found', 'not found',
                'user not found', 'profile not found', 'sorry! something went wrong'
            ]
            
            if any(error in page_text for error in error_indicators):
                print(f"   ❌ Page not found: {artist_url}")
                return None
            
            artist_info = {
                'url': artist_url,
                'name': '',
                'email': '',
                'instagram': '',
                'twitter': '',
                'website': '',
                'youtube': '',
                'bio': ''
            }
            
            # Enhanced name extraction
            name_selectors = [
                'h1.profileHeaderInfo__title',
                'h2.profileHeaderInfo__userName', 
                'h1.header__primary',
                '.profileHeader__username',
                '.profileHeaderInfo__displayName',
                '.userItem__username',
                '[data-testid="header-username"]',
                '.profileHeader__usernameTruncated',
                '.profileHeader__usernameWrapper h1',
                'h1[class*="title"]',
                '.profileHeader__displayName',
                '.profileHeaderInfo__usernameButton'
            ]
            
            name_found = False
            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if name_element and name_element.text.strip():
                        name = name_element.text.strip()
                        # Skip system page titles
                        system_titles = [
                            'We can\'t find that page.', 'SoundCloud Terms of Use', 
                            'Company Information', 'First upload to first album',
                            'Page not found', 'User not found', 'Sorry! Something went wrong'
                        ]
                        if name not in system_titles and len(name) > 1:
                            artist_info['name'] = name
                            print(f"Found name: {artist_info['name']}")
                            name_found = True
                            break
                except:
                    continue
            
            if not name_found:
                # Extract from URL as fallback
                url_parts = artist_url.split('/')
                if len(url_parts) > 3:
                    potential_name = url_parts[-1] or url_parts[-2]
                    if potential_name and potential_name not in ['www', 'soundcloud', 'com']:
                        artist_info['name'] = potential_name.replace('-', ' ').replace('_', ' ').title()
                        print(f"Extracted name from URL: {artist_info['name']}")
            
            # Don't process further if no valid name
            if not artist_info['name']:
                print(f"   ❌ No valid artist name found")
                return None
            
            # Enhanced bio extraction with more selectors
            bio_selectors = [
                'div.profileHeaderInfo__bio',
                '.profileHeader__description',
                '.userDescription',
                '.truncatedUserDescription__wrapper',
                '[data-testid="user-description"]',
                '.profileHeaderInfo__description',
                '.profileDescription',
                '.profileHeaderInfo__descriptionText',
                '.userItem__description'
            ]
            
            for selector in bio_selectors:
                try:
                    description_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if description_element and description_element.text.strip():
                        artist_info['bio'] = description_element.text.strip()
                        print(f"Found bio: {artist_info['bio'][:100]}...")
                        break
                except:
                    continue
            
            # Extract email from bio
            if artist_info['bio']:
                email_patterns = [
                    r'[\w\.-]+@[\w\.-]+\.\w+',
                    r'contact[:\s]*[\w\.-]+@[\w\.-]+\.\w+',
                    r'email[:\s]*[\w\.-]+@[\w\.-]+\.\w+',
                    r'business[:\s]*[\w\.-]+@[\w\.-]+\.\w+'
                ]
                for pattern in email_patterns:
                    email_match = re.search(pattern, artist_info['bio'], re.IGNORECASE)
                    if email_match:
                        artist_info['email'] = email_match.group(0)
                        print(f"Found email: {artist_info['email']}")
                        break
            
            # Enhanced social media link extraction
            social_selectors = [
                'a[href*="instagram.com"]',
                'a[href*="twitter.com"]', 
                'a[href*="youtube.com"]',
                '.profileHeader__social a',
                '.socialLinks a',
                'a.sc-social-logo-interactive',
                '.profileHeaderInfo__social a',
                'a[class*="social"]',
                '.profileHeaderInfo__links a',
                '.userLinks a'
            ]
            
            for selector in social_selectors:
                try:
                    social_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in social_links:
                        href = link.get_attribute('href')
                        if not href:
                            continue
                            
                        # Decode SoundCloud redirect URLs
                        real_url = self._decode_soundcloud_redirect(href)
                            
                        if 'instagram.com' in real_url.lower() and not artist_info['instagram']:
                            artist_info['instagram'] = real_url
                            print(f"Found Instagram: {real_url}")
                        elif 'youtube.com' in real_url.lower() and not artist_info['youtube']:
                            artist_info['youtube'] = real_url
                            print(f"Found YouTube: {real_url}")
                        elif 'twitter.com' in real_url.lower() and not artist_info['twitter']:
                            artist_info['twitter'] = real_url
                            print(f"Found Twitter: {real_url}")
                except Exception:
                    continue
            
            # Enhanced social media extraction from bio text
            if artist_info['bio']:
                self._extract_social_from_bio(artist_info)
            
            # Enhanced Instagram extraction from page source
            if not artist_info['instagram']:
                self._extract_instagram_from_page_source(artist_info)
            
            print(f"Final artist info: Name={artist_info['name']}, Instagram={artist_info.get('instagram', 'None')}")
            return artist_info if artist_info['name'] else None
            
        except Exception as e:
            print(f"Error scraping artist info from {artist_url}: {str(e)}")
            return None
    
    def _decode_soundcloud_redirect(self, href: str) -> str:
        """Decode SoundCloud gate.sc redirect URLs."""
        if 'gate.sc' in href or 'exit.sc' in href:
            try:
                parsed = urlparse(href)
                qs = parse_qs(parsed.query)
                if 'url' in qs:
                    return unquote(qs['url'][0])
            except:
                pass
        return href
    
    def _extract_social_from_bio(self, artist_info: Dict):
        """Extract social media links from bio text with enhanced patterns."""
        bio = artist_info['bio'].lower()
        
        # Enhanced Instagram patterns
        if not artist_info['instagram']:
            instagram_patterns = [
                r'instagram\.com/([\w\.-]+)',
                r'@([\w\.-]+)\s*(?:on\s*)?(?:ig|insta|instagram)',
                r'(?:ig|insta|instagram):\s*@?([\w\.-]+)',
                r'(?:ig|insta|instagram)\s*@?([\w\.-]+)',
                r'ig:\s*@?([\w\.-]+)',
                r'follow.*instagram.*@([\w\.-]+)',
                r'instagram.*@([\w\.-]+)',
                r'@([\w\.-]+).*ig\b',
                r'ig\s*-\s*@?([\w\.-]+)',
                r'📷\s*@?([\w\.-]+)',  # Camera emoji often used for Instagram
                r'📸\s*@?([\w\.-]+)',  # Camera with flash emoji
            ]
            for pattern in instagram_patterns:
                match = re.search(pattern, bio, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    if len(username) > 2 and not any(skip in username.lower() for skip in ['instagram', 'follow', 'like', 'share']):
                        artist_info['instagram'] = f"https://instagram.com/{username}"
                        print(f"Extracted Instagram from bio: {artist_info['instagram']}")
                        break
        
        # Enhanced Twitter patterns
        if not artist_info['twitter']:
            twitter_patterns = [
                r'twitter\.com/([\w\.-]+)',
                r'@([\w\.-]+)\s*(?:on\s*)?(?:tw|twitter)',
                r'(?:tw|twitter):\s*@?([\w\.-]+)',
                r'follow.*twitter.*@([\w\.-]+)',
                r'🐦\s*@?([\w\.-]+)',  # Bird emoji for Twitter
            ]
            for pattern in twitter_patterns:
                match = re.search(pattern, bio, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    if len(username) > 2:
                        artist_info['twitter'] = f"https://twitter.com/{username}"
                        print(f"Extracted Twitter from bio: {artist_info['twitter']}")
                        break
    
    def _extract_instagram_from_page_source(self, artist_info: Dict):
        """Enhanced Instagram extraction from page source."""
        try:
            page_source = self.driver.page_source
            
            # Multiple Instagram patterns in page source
            instagram_patterns = [
                r'instagram\.com/([\w\.-]+)',
                r'"instagram"[^"]*"([^"]+)"',
                r'ig\.com/([\w\.-]+)',
                r'@([\w\.-]+)[^"]*instagram',
            ]
            
            for pattern in instagram_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    if (len(match) > 2 and 
                        match not in ['instagram', 'www', 'help', 'about', 'explore', 'accounts', 'p'] and
                        not artist_info['instagram']):
                        artist_info['instagram'] = f"https://instagram.com/{match}"
                        print(f"Found Instagram in page source: {artist_info['instagram']}")
                        return
        except Exception:
            pass