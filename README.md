# Redemption RSPS Wiki AI Bot

This project creates a Discord bot that uses OpenAI API to answer questions about Redemption RSPS based on their wiki data.

## What This Does

1. **Scrapes MediaWiki data** from redemptionps.com/wiki
2. **Uses OpenAI API** to answer questions intelligently
3. **Discord bot interface** for customers to ask questions
4. **Responds to mentions** and DMs with relevant wiki information

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Scrape Wiki Data
```bash
python wiki_scraper.py
```
This will create `wiki_training_data.json` with all wiki content.

### 3. Set Environment Variables
Create a `.env` file in the project root:
```bash
DISCORD_TOKEN=your_discord_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Run Locally
```bash
python discord_bot.py
```

## GitHub & Railway Deployment

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/rs-bot.git
git push -u origin main
```

### 2. Deploy to Railway
1. Go to [Railway](https://railway.app/)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Add environment variables in Railway dashboard:
   - `DISCORD_TOKEN` = your Discord bot token
   - `OPENAI_API_KEY` = your OpenAI API key
6. Deploy!

## Usage

### In Discord Servers:
- **Mention the bot**: `@Redemption Bot combat training`
- **Use commands**: `!wikihelp`

### In Private DMs:
- **Any message**: The bot responds to all messages

### Example questions:
- "How do I train combat skills?"
- "What are the best money making methods?"
- "How do I start playing Redemption RSPS?"
- "What gear should I use for boss fights?"

## Environment Variables

### Required for Railway:
- `DISCORD_TOKEN` - Your Discord bot token
- `OPENAI_API_KEY` - Your OpenAI API key

### Local Development:
Create a `.env` file with the same variables.

## Files Explained

- `wiki_scraper.py` - Scrapes all wiki content
- `discord_bot.py` - Main Discord bot with OpenAI integration
- `requirements.txt` - Python dependencies
- `Procfile` - Railway deployment configuration
- `.gitignore` - Excludes sensitive files from Git
- `README.md` - This file

## Security Notes

- ✅ Tokens are stored as environment variables
- ✅ `.env` file is excluded from Git
- ✅ No hardcoded secrets in the code
- ✅ Safe for public GitHub repositories

## Support

If you run into issues:
1. Check that environment variables are set correctly
2. Verify your Discord bot has proper permissions
3. Ensure your OpenAI API key is valid
4. Check Railway logs for deployment issues
