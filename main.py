import requests
import os
import json
import logging
from datetime import datetime
import time
from typing import Optional, Dict, Any

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def mask_username(username: str, index: Optional[int] = None) -> str:
    """
    Masks a username for logging purposes.
    
    Args:
        username (str): The username to mask
        index (Optional[int]): The index of the username in the list
        
    Returns:
        str: The masked username identifier
    """
    if index is not None:
        return f"SECRET_USER_{index + 1}"
    return "SECRET_USER"

# Load environment variables
if not load_dotenv():
    logging.error("No .env file found!")

# Configuration
TWITTER_USERS = os.environ.get('TWITTER_USERNAMES', '').split(',') if os.environ.get('TWITTER_USERNAMES') else []
if not TWITTER_USERS:
    logging.warning("No Twitter usernames configured in TWITTER_USERNAMES environment variable")

STATE_FILE = "state.json"

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def get_latest_tweet(username: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Fetch the latest tweet from a given username.
    
    Args:
        username (str): Twitter username without @ symbol
        retry_count (int): Number of retries attempted
        
    Returns:
        Optional[Dict[str, Any]]: Tweet data or None if not found/error
    """
    # Remove @ symbol if present in username
    username = username.lstrip('@')
    if retry_count >= 3:  # Maximum retry attempts
        logging.error(f"Maximum retry attempts reached for {mask_username(username)}")
        return None
        
    token = os.environ.get('TWITTER_BEARER_TOKEN')
    if not token:
        logging.error("Twitter Bearer Token not found in environment variables")
        return None
    
    logging.info(f"Using Twitter Bearer Token: {token[:10]}... (truncated)")
        
    # Use tweets endpoint instead of search
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # First get the user ID
        logging.info(f"Getting user ID for {mask_username(username)}")
        user_resp = requests.get(url, headers=headers, timeout=10)
        
        if user_resp.status_code == 400:
            logging.error(f"Invalid username {mask_username(username)}")
            return None
            
        # Log full response for debugging with masked username and display name
        response_data = user_resp.json()
        if 'data' in response_data:
            if 'username' in response_data['data']:
                response_data['data']['username'] = mask_username(response_data['data']['username'])
            if 'name' in response_data['data']:
                response_data['data']['name'] = '[MASKED_NAME]'
        logging.info(f"User lookup response: {json.dumps(response_data, indent=2)}")
        
        if user_resp.status_code == 404:
            logging.error(f"User {mask_username(username)} not found")
            return None
            
        user_resp.raise_for_status()
        user_data = user_resp.json()
        
        if not user_data.get('data', {}).get('id'):
            logging.error(f"Could not find user ID for @{username}. This might be due to account privacy settings or suspension.")
            return None
            
        user_id = user_data['data']['id']
        
        # Then get their tweets
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {
            "max_results": 5,
            "tweet.fields": "created_at"
        }
        
        logging.info(f"Getting tweets for {mask_username(username)}")
        resp = requests.get(tweets_url, headers=headers, params=params, timeout=10)
        
        logging.info(f"Twitter API Response Status Code: {resp.status_code}")
        
        # Check for rate limiting
        if resp.status_code == 429:
            reset_time = resp.headers.get("x-rate-limit-reset")
            if reset_time:
                wait_time = int(reset_time) - int(time.time()) + 5  # Add 5 seconds buffer
                if wait_time > 0:
                    if wait_time > 300:  # If wait time is more than 5 minutes
                        logging.warning(f"Rate limit too long ({wait_time} seconds), terminating current run")
                        return None
                    logging.warning(f"Rate limit reached. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    return get_latest_tweet(username, retry_count + 1)

            # If no reset time available, use a shorter exponential backoff
            backoff_time = min(60 * (2 ** retry_count), 300)  # Max 5 minutes
            if backoff_time > 300:  # If backoff would be too long
                logging.warning("Rate limit backoff would be too long, terminating current run")
                return None
            logging.warning(f"Rate limit reached. Using exponential backoff: {backoff_time} seconds")
            time.sleep(backoff_time)
            return get_latest_tweet(username, retry_count + 1)
            
        resp.raise_for_status()
        
        data = resp.json()
        # Mask sensitive information in the response data
        if 'data' in data and isinstance(data['data'], list):
            for tweet in data['data']:
                if 'author' in tweet:
                    if 'name' in tweet['author']:
                        tweet['author']['name'] = '[MASKED_NAME]'
                    if 'username' in tweet['author']:
                        tweet['author']['username'] = mask_username(tweet['author']['username'])
        logging.info(f"Twitter API Response Data: {json.dumps(data, indent=2)}")
        
        if not data.get('data'):
            logging.info(f"No recent tweets found for {mask_username(username)}")
            return None
            
        return data['data'][0]
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Twitter API error for {mask_username(username)}: {str(e)}")
        return None
    except (KeyError, IndexError) as e:
        logging.error(f"Unexpected Twitter API response format: {str(e)}")
        return None

def send_telegram_message(text: str) -> bool:
    """
    Send a message via Telegram bot.
    
    Args:
        text (str): Message text to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    # Log environment variable presence
    for key in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']:
        if key not in os.environ:
            logging.error(f"Missing {key} in environment variables")
        else:
            logging.info(f"{key} is present in environment variables")
        
    url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage"
    payload = {
        "chat_id": os.environ['TELEGRAM_CHAT_ID'],
        "text": text,
        "disable_web_page_preview": True,
        "parse_mode": "HTML"  # Enable HTML formatting
    }
    
    try:
        resp = requests.post(url, data=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Telegram API error: {str(e)}")
        return False

def main():
    """Main function to check for new tweets and send notifications."""
    try:
        start_time = datetime.now()
        logging.info(f"Bot started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add a delay at start to avoid immediate rate limits
        time.sleep(5)
        
        # Validate environment variables
        required_vars = ['TWITTER_BEARER_TOKEN', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return
            
        # Send a test message to verify Telegram integration
      #  test_message = "🔄 Bot is running - Test Message"
      #  if send_telegram_message(test_message):
      #      logging.info("Test message sent successfully to Telegram")
      #  else:
      #      logging.error("Failed to send test message to Telegram")
        
        state = load_state()
        updates_made = False
        
        for index, user in enumerate(TWITTER_USERS):
            masked_user = mask_username(user, index)
            logging.info(f"Checking tweets for {masked_user}")
            tweet = get_latest_tweet(user)
            
            if not tweet:
                continue
                
            tweet_id = tweet["id"]
            last_id = state.get(user)
            
            if last_id != tweet_id:
                # Format tweet with HTML
                created_at = tweet.get('created_at', 'Unknown time')
                link = f"https://twitter.com/{user}/status/{tweet_id}"
                message = (
                    f"🕊 <b>New Tweet from @{user}</b>\n\n"
                    f"{tweet['text']}\n\n"
                    f"🕒 {created_at}\n"
                    f"🔗 <a href='{link}'>View Tweet</a>"
                )
                
                if send_telegram_message(message):
                    logging.info(f"Successfully sent notification for {masked_user}'s tweet")
                    state[user] = tweet_id
                    updates_made = True
                else:
                    logging.error(f"Failed to send notification for {masked_user}'s tweet")
        
        if updates_made:
            save_state(state)
            logging.info("State file updated successfully")
            
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        logging.error(error_msg)
        # Try to send error message to Telegram
        send_telegram_message(error_msg)
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        raise