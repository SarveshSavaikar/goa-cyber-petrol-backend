import asyncio
from telethon import TelegramClient
from typing import List, Dict, Optional
import os
from datetime import datetime, timedelta

# Telegram API credentials (will need to be set via environment variables)
API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
API_HASH = os.getenv('TELEGRAM_API_HASH', 'your_api_hash')
SESSION_NAME = 'goa_cyber_patrol'

class TelegramScraper:
    def __init__(self):
        self.client = None
    
    async def initialize(self):
        """Initialize Telegram client"""
        try:
            self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
            if not self.client.is_connected():
                await self.client.start()
            return True
        except Exception as e:
            print(f"Error initializing Telegram client: {e}")
            return False
    
    async def get_messages_from_channels(self, channel_usernames: List[str], limit: int = 50) -> List[Dict]:
        """
        Fetch latest messages from specified Telegram channels
        
        Args:
            channel_usernames: List of channel usernames (without @)
            limit: Number of messages to fetch per channel
            
        Returns:
            List of message dictionaries
        """
        if not self.client:
            await self.initialize()
        
        messages = []
        
        for channel in channel_usernames:
            try:
                # Get channel entity
                entity = await self.client.get_entity(channel)
                
                # Fetch messages
                async for message in self.client.iter_messages(entity, limit=limit):
                    if message.text:
                        message_data = {
                            'platform': 'Telegram',
                            'message_text': message.text,
                            'date': message.date,
                            'author_id': str(message.sender_id) if message.sender_id else 'Unknown',
                            'channel': channel,
                            'message_id': message.id
                        }
                        messages.append(message_data)
                        
            except Exception as e:
                print(f"Error fetching messages from {channel}: {e}")
                continue
        
        return messages
    
    async def search_messages_by_keywords(self, keywords: List[str], limit: int = 100) -> List[Dict]:
        """
        Search for messages containing specific keywords across accessible chats
        
        Args:
            keywords: List of keywords to search for
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        if not self.client:
            await self.initialize()
        
        messages = []
        
        # Search in recent chats
        async for dialog in self.client.iter_dialogs():
            if len(messages) >= limit:
                break
                
            try:
                # Search each keyword in this chat
                for keyword in keywords:
                    async for message in self.client.iter_messages(
                        dialog.entity, 
                        search=keyword, 
                        limit=min(10, limit - len(messages))
                    ):
                        if message.text:
                            message_data = {
                                'platform': 'Telegram',
                                'message_text': message.text,
                                'date': message.date,
                                'author_id': str(message.sender_id) if message.sender_id else 'Unknown',
                                'chat_name': dialog.name,
                                'message_id': message.id,
                                'search_keyword': keyword
                            }
                            messages.append(message_data)
                            
                            if len(messages) >= limit:
                                break
                    
                    if len(messages) >= limit:
                        break
                        
            except Exception as e:
                print(f"Error searching in {dialog.name}: {e}")
                continue
        
        return messages
    
    async def close(self):
        """Close the Telegram client"""
        if self.client:
            await self.client.disconnect()

# Global client instance
telegram_scraper = TelegramScraper()