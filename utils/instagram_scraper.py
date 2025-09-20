import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
import time
import random

class InstagramScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_hashtag_posts(self, hashtags: List[str], limit_per_hashtag: int = 20) -> List[Dict]:
        """
        Scrape Instagram posts by hashtags
        
        Args:
            hashtags: List of hashtags to search (without #)
            limit_per_hashtag: Maximum posts to scrape per hashtag
            
        Returns:
            List of post dictionaries
        """
        posts = []
        
        for hashtag in hashtags:
            try:
                hashtag_posts = self._scrape_single_hashtag(hashtag, limit_per_hashtag)
                posts.extend(hashtag_posts)
                
                # Add delay between requests to avoid being blocked
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                print(f"Error scraping hashtag #{hashtag}: {e}")
                continue
        
        return posts
    
    def _scrape_single_hashtag(self, hashtag: str, limit: int) -> List[Dict]:
        """
        Scrape posts from a single hashtag
        
        Note: This is a simplified implementation. Instagram's actual scraping
        is more complex and may require additional authentication/techniques.
        """
        posts = []
        
        try:
            # Instagram hashtag URL
            url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            
            response = self.session.get(url)
            if response.status_code != 200:
                print(f"Failed to access #{hashtag}: {response.status_code}")
                return posts
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for script tags containing JSON data
            script_tags = soup.find_all('script', type='text/javascript')
            
            for script in script_tags:
                if script.string and 'window._sharedData' in str(script.string):
                    # Extract JSON data from script
                    json_text = str(script.string)
                    json_start = json_text.find('{')
                    json_end = json_text.rfind('}') + 1
                    
                    if json_start != -1 and json_end != -1:
                        try:
                            data = json.loads(json_text[json_start:json_end])
                            posts.extend(self._extract_posts_from_json(data, hashtag, limit))
                        except json.JSONDecodeError:
                            continue
                    break
            
        except Exception as e:
            print(f"Error scraping hashtag #{hashtag}: {e}")
        
        return posts[:limit]
    
    def _extract_posts_from_json(self, data: dict, hashtag: str, limit: int) -> List[Dict]:
        """
        Extract post data from Instagram's JSON response
        """
        posts = []
        
        try:
            # Navigate through Instagram's JSON structure
            # Note: Instagram's structure changes frequently
            hashtag_data = data.get('entry_data', {}).get('TagPage', [{}])[0]
            graphql_data = hashtag_data.get('graphql', {})
            hashtag_info = graphql_data.get('hashtag', {})
            edge_hashtag_media = hashtag_info.get('edge_hashtag_to_media', {})
            edges = edge_hashtag_media.get('edges', [])
            
            for edge in edges[:limit]:
                node = edge.get('node', {})
                
                # Extract post caption
                caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                caption = ""
                if caption_edges:
                    caption = caption_edges[0].get('node', {}).get('text', "")
                
                if caption:  # Only include posts with captions
                    post_data = {
                        'platform': 'Instagram',
                        'message_text': caption,
                        'date': datetime.fromtimestamp(node.get('taken_at_timestamp', 0)),
                        'author_id': node.get('owner', {}).get('id', 'Unknown'),
                        'hashtag': hashtag,
                        'post_id': node.get('id', ''),
                        'shortcode': node.get('shortcode', ''),
                        'like_count': node.get('edge_liked_by', {}).get('count', 0),
                        'comment_count': node.get('edge_media_to_comment', {}).get('count', 0)
                    }
                    posts.append(post_data)
                    
        except Exception as e:
            print(f"Error extracting posts from JSON: {e}")
        
        return posts
    
    def scrape_goa_related_content(self) -> List[Dict]:
        """
        Scrape Goa-related content using relevant hashtags
        """
        goa_hashtags = [
            'goa', 'goatravel', 'goahotel', 'goaresort', 'goajobs', 
            'goabusiness', 'goatourism', 'goavacation', 'goabeach'
        ]
        
        return self.scrape_hashtag_posts(goa_hashtags, limit_per_hashtag=15)
    
    def search_suspicious_content(self) -> List[Dict]:
        """
        Search for potentially suspicious content using relevant hashtags
        """
        suspicious_hashtags = [
            'easymoney', 'workfromhome', 'earnmoney', 'parttimejob',
            'onlinejob', 'freelancing', 'business', 'investment'
        ]
        
        return self.scrape_hashtag_posts(suspicious_hashtags, limit_per_hashtag=10)

# Global scraper instance
instagram_scraper = InstagramScraper()