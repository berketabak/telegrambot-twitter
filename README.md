# Twitter-Telegram Bot

A Python bot that monitors specified Twitter accounts and forwards their new tweets to Telegram. Running on GitHub Actions, it checks for new tweets hourly while preventing duplicate notifications.

## Features

- 🔄 Monitors multiple Twitter accounts simultaneously
- 📨 Forwards new tweets to Telegram with formatted messages
- 🎯 Prevents duplicate notifications using state management
- ⏱️ Runs automatically every hour via GitHub Actions
- 🔒 Secure credential management using environment variables
- 📝 Comprehensive logging system
- ⚡ Smart rate limit handling for Twitter API
- 🔄 Automatic retries on API failures
- 🗄️ Persistent state storage between runs

## Prerequisites

- Python 3.10 or higher
- Twitter API Bearer Token (from Twitter Developer Portal)
- Telegram Bot Token (from @BotFather)
- Telegram Chat ID
- GitHub account (for deployment)

## Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/twitter-telegram-bot.git
   cd twitter-telegram-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your credentials:
   ```plaintext
   TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here
   TWITTER_USERNAMES=username1,username2,username3
   ```

## GitHub Actions Deployment

1. **Fork this repository**

2. **Add repository secrets**
   - Navigate to your repository's Settings > Secrets and variables > Actions
   - Add these required secrets:
     - `TWITTER_BEARER_TOKEN`
     - `TELEGRAM_BOT_TOKEN`
     - `TELEGRAM_CHAT_ID`
     - `TWITTER_USERNAMES` (comma-separated list of usernames without @ symbol)

3. **Enable GitHub Actions**
   - Go to the Actions tab
   - Enable workflows if not already enabled

## How It Works

1. **Initialization**
   - Loads environment variables
   - Validates required credentials
   - Initializes state management

2. **Twitter Integration**
   - Fetches user IDs for configured usernames
   - Retrieves latest tweets using Twitter API v2
   - Handles rate limits with smart retry logic

3. **State Management**
   - Maintains `state.json` to track processed tweets
   - Prevents duplicate notifications
   - Persists between runs using GitHub Actions cache

4. **Telegram Notification**
   - Formats tweets with HTML styling
   - Includes tweet text, timestamp, and direct link
   - Supports error notifications

## File Structure

```plaintext
twitter-telegram-bot/
├── main.py              # Main bot logic
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── state.json          # Tweet state storage
├── .github/
│   └── workflows/
│       └── bot.yml     # GitHub Actions workflow
└── README.md           # Documentation
```

## Error Handling

The bot includes comprehensive error handling for:
- Twitter API rate limits (with smart retry logic)
- Network issues (with automatic retries)
- Authentication failures
- Missing credentials
- Invalid usernames
- API response parsing errors

## Configuration Options

### Environment Variables

- `TWITTER_BEARER_TOKEN`: Your Twitter API Bearer token
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Target Telegram chat ID
- `TWITTER_USERNAMES`: Comma-separated Twitter usernames to monitor

### Customizable Parameters

In `main.py`:
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `RETRY_DELAY`: Delay between retries (default: 2 seconds)
- `MAX_RESULTS`: Number of tweets to fetch (default: 5)

## Getting Required Tokens

### Twitter Bearer Token
1. Visit [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a project and app (if you haven't already)
3. Navigate to "Keys and Tokens"
4. Generate Bearer Token with read permissions
5. Ensure your app has the required permissions:
   - `tweets.read`
   - `users.read`

### Telegram Bot Token
1. Start a chat with [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Copy the provided HTTP API token

### Telegram Chat ID
1. Add your bot to desired channel/group
2. Make it an admin (for groups/channels)
3. Send a message in the chat
4. Visit: `https://api.telegram.org/bot<YourBOTToken>/getUpdates`
5. Look for `"chat":{"id":XXXXXXXXXX}` in the response

## Troubleshooting

### Common Issues

1. **No notifications received**
   - Check if state.json is being cached correctly
   - Verify Telegram bot permissions
   - Ensure valid chat ID

2. **Rate limit errors**
   - Verify Twitter API token permissions
   - Check if token has correct access level
   - Consider increasing time between checks

3. **Missing tweets**
   - Verify Twitter usernames exist and are public
   - Check for API response errors in logs
   - Ensure proper rate limit handling

4. **GitHub Actions issues**
   - Verify all secrets are properly set
   - Check workflow logs for errors
   - Ensure repository permissions are correct

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Security Note

⚠️ Never commit your `.env` file or expose your tokens. Always use environment variables or GitHub Secrets for sensitive data.
