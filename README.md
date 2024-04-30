# Project WorldSearchHotelsBot

WorldSearchHotelsBot is a Telegram bot. It searches for hotels around the world based on the parameters entered by the user
and outputs the hotels filtered by the user. The search is performed based on the API of the service Hotels.com.
The API to the specified site is taken from the service RapidAPI.com.

### Commands:

1. /lowprice - search for the lowest cost hotels
2. /highprice - search for the highest cost hotels
3. /bestdeal - search for hotels by a given price range and a distance from the center of the location
4. /history - search history

### Installation:

1. Clone the repository from GitHub
2. Create a virtual environment
3. Install dependencies
pip install -r requirements.txt
4. Create the .env file
5. Enter the bot token and API key in .env as shown in .env.template
6. Launch the bot
