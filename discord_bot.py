import discord
from discord.ext import commands
import json
import asyncio
import os
import schedule
import time
import threading
from typing import Optional
from openai import OpenAI
from wiki_scraper import AsyncWikiScraper

class WikiBot:
    def __init__(self, token: str, openai_api_key: str):
        self.token = token
        self.openai_api_key = openai_api_key
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.wiki_data = {}
        
        # Configure OpenAI
        self.client = OpenAI(api_key=openai_api_key)
        
        # Load wiki data for context
        self.load_wiki_data()
        
        # Setup scheduled scraping
        self.setup_scheduled_scraping()
        
        # Setup bot commands
        self.setup_commands()
    
    def load_wiki_data(self):
        """Load wiki data for context"""
        try:
            with open('wiki_training_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for page in data:
                    self.wiki_data[page['title'].lower()] = page['content']
            print(f"Loaded {len(self.wiki_data)} wiki pages")
        except FileNotFoundError:
            print("Warning: wiki_training_data.json not found. Run wiki_scraper.py first.")
    
    def setup_scheduled_scraping(self):
        """Setup daily wiki scraping at 2 AM"""
        schedule.every().day.at("02:00").do(self.daily_scrape)
        
        # Start the scheduler in a separate thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("Scheduled daily wiki scraping at 2:00 AM")
    
    def daily_scrape(self):
        """Run daily wiki scraping"""
        print("Starting daily wiki scrape...")
        try:
            # Run the scraper
            asyncio.run(self.run_scraper())
            # Reload the data
            self.load_wiki_data()
            print("Daily wiki scrape completed successfully!")
        except Exception as e:
            print(f"Error during daily scrape: {e}")
    
    async def run_scraper(self):
        """Run the wiki scraper"""
        async with AsyncWikiScraper() as scraper:
            training_data = await scraper.scrape_all_content()
            scraper.save_training_data(training_data)
    
    def find_relevant_context(self, question: str) -> str:
        """Find relevant wiki content for the question"""
        question_lower = question.lower()
        relevant_content = []
        
        # Simple keyword matching
        keywords = question_lower.split()
        for title, content in self.wiki_data.items():
            score = 0
            for keyword in keywords:
                if keyword in title or keyword in content:
                    score += 1
            if score > 0:
                # Limit content length to avoid token limits
                limited_content = content[:2000] + "..." if len(content) > 2000 else content
                relevant_content.append((score, limited_content))
        
        # Sort by relevance and take top 2 (reduced from 3)
        relevant_content.sort(reverse=True)
        combined_content = "\n\n".join([content for _, content in relevant_content[:2]])
        
        # Further limit total context length
        if len(combined_content) > 3000:
            combined_content = combined_content[:3000] + "..."
        
        return combined_content
    
    def generate_response(self, question: str) -> str:
        """Generate response using OpenAI API"""
        try:
            # Get relevant context
            context = self.find_relevant_context(question)
            
            # Create system message
            system_message = f"""You are a helpful assistant for Redemption RSPS (RuneScape Private Server). 
Answer questions based on the wiki information provided. Be helpful, accurate, and concise.

Wiki Context:
{context}"""
            
            # Create user message
            user_message = f"Question: {question}"
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Sorry, there was an error generating the response. Please try again."
    
    def setup_commands(self):
        """Setup bot commands"""
        
        @self.bot.event
        async def on_ready():
            print(f'{self.bot.user} has connected to Discord!')
            print(f'Bot is in {len(self.bot.guilds)} guilds')
        
        @self.bot.event
        async def on_message(message):
            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                return
            
            # Handle commands first
            await self.bot.process_commands(message)
            
            # Only respond if the bot is mentioned or if it's a DM
            bot_mentioned = self.bot.user.mentioned_in(message)
            is_dm = isinstance(message.channel, discord.DMChannel)
            
            if (bot_mentioned or is_dm) and not message.content.startswith('!'):
                async with message.channel.typing():
                    response = self.generate_response(message.content)
                    
                    # Split long responses
                    if len(response) > 2000:
                        chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                        for i, chunk in enumerate(chunks):
                            await message.channel.send(f"Response {i+1}/{len(chunks)}:\n{chunk}")
                    else:
                        await message.channel.send(response)
        
        @self.bot.command(name='wikihelp')
        async def wikihelp_cmd(ctx):
            """Show help information"""
            help_text = """
**Redemption RSPS Wiki Bot Commands:**

Just type any message and the bot will respond with Redemption RSPS information!

**Example messages:**
- How do I train combat skills?
- What are the best money making methods?
- How do I start playing Redemption RSPS?
- What gear should I use for boss fights?
- Combat training
- Money making
- Boss fights
- Any topic about Redemption RSPS

The bot will automatically respond with relevant information from the official Redemption RSPS wiki data.

**Commands:**
`!wikihelp` - Show this help message
            """
            await ctx.send(help_text)
    
    def run(self):
        """Run the Discord bot"""
        print("Starting Discord bot...")
        self.bot.run(self.token)

if __name__ == "__main__":
    # Get tokens from environment variables
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set")
        print("Please set your Discord bot token as an environment variable")
        exit(1)
    
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key as an environment variable")
        exit(1)
    
    bot = WikiBot(DISCORD_TOKEN, OPENAI_API_KEY)
    bot.run()
