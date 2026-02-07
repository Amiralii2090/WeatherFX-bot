#!/usr/bin/env python3
"""
Telegram Weather & Currency Bot
Author: [Your Name]
Description: A Telegram bot that provides weather information and currency exchange rates.
Version: 1.0.0
"""

# ============================================================================
# 📦 IMPORT LIBRARIES
# ============================================================================
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
import requests  # For making HTTP requests to APIs
import datetime  # For timestamp and date formatting

# ============================================================================
# ⚙️ CONFIGURATION & CONSTANTS
# ============================================================================
# 🚨 SECURITY WARNING: Never hardcode API keys in production!
# Use environment variables instead for security

# Telegram Bot Token (Get from @BotFather)
BOT_TOKEN = 'YOUR-TOKEN'

# Weather API Key (Get from openweathermap.org)
WEATHER_API_KEY = "YOUR-API-KEY"

# Metals API Key (Get from goldapi.io) - Optional for metal prices
METALS_API_KEY = "YOUR-API-KEY"

# ============================================================================
# 🎭 CONVERSATION STATES
# ============================================================================
# ConversationHandler uses states to manage multi-step conversations
# Each state represents a different point in the user interaction flow
WEATHER_METHOD, CITY_NAME = range(2)
# WEATHER_METHOD: User is choosing how to provide location (GPS or city name)
# CITY_NAME: User is entering city name for weather

# ============================================================================
# 🎹 KEYBOARD LAYOUTS
# ============================================================================
# Main menu keyboard - shown when bot starts
main_keyboard = [
    ["Weather🌦", "Currency💲"]  # Two main options for users
]

# Create keyboard markup with customization options
reply_markup = ReplyKeyboardMarkup(
    main_keyboard,
    resize_keyboard=True,      # Keyboard adjusts to screen size
    one_time_keyboard=True     # Keyboard disappears after use
)

# ============================================================================
# 🎯 BOT COMMAND HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /start command - First interaction with bot
    Sends welcome message and shows main menu keyboard
    """
    welcome_message = (
        "Hi welcome to the Weather & Currency Bot 🤖👋\n\n"
        "I'm your friendly bot to keep you updated on:\n"
        "🌦 Weather in your city\n"
        "💱 Currency exchange rates\n\n"
        "Please choose an option from the buttons below to get started.\n"
        "For more information, use /help"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup  # Show main menu buttons
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /help command - Provides usage instructions
    """
    help_text = (
        "ℹ️ Help Guide\n\n"
        "🌦 Weather:\n"
        "- Tap 'Weather' button\n"
        "- Send your location OR enter city name\n\n"
        "💱 Currency:\n"
        "- Tap 'Currency' button to get latest prices\n"
        "- Includes major fiat currencies, cryptocurrencies and metals\n\n"
        "📋 Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this message\n"
        "/cancel - Cancel current operation"
    )
    
    await update.message.reply_text(help_text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /cancel command - Cancels current conversation
    Returns to main menu
    """
    await update.message.reply_text(
        "Operation cancelled. Use /start to begin again.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END  # Exit conversation state


# ============================================================================
# 🖱️ BUTTON CLICK HANDLERS
# ============================================================================

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all button clicks in the bot
    Routes to appropriate functionality based on button text
    """
    text = update.message.text  # Get which button was clicked

    if text == "Weather🌦":
        # User wants weather - Show location options
        location_keyboard = KeyboardButton(
            text="📍 Send location",
            request_location=True  # Special button that requests GPS location
        )
        manual_button = KeyboardButton("🏘 Enter city name")

        # Create weather method selection keyboard
        weather_keyboard = ReplyKeyboardMarkup(
            [[location_keyboard], [manual_button]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await update.message.reply_text(
            "How would you like to share your location?",
            reply_markup=weather_keyboard
        )
        return WEATHER_METHOD  # Move to weather method selection state

    elif text == "🏘 Enter city name":
        # User chose to enter city name manually
        await update.message.reply_text("Please enter your city name:")
        return CITY_NAME  # Move to city name input state
        
    elif text == "Currency💲":
        # User wants currency rates
        currency_text = await get_currency_rates()  # Fetch rates from APIs
        await update.message.reply_text(currency_text, reply_markup=reply_markup)
        return ConversationHandler.END  # Return to main menu


# ============================================================================
# 🌦 WEATHER FUNCTIONALITY
# ============================================================================

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles GPS location sent by user
    Gets weather for coordinates and returns to main menu
    """
    location = update.message.location
    latitude = location.latitude
    longitude = location.longitude

    # Get weather using coordinates
    weather_text = await get_weather_by_coords(latitude, longitude)
    await update.message.reply_text(weather_text, reply_markup=reply_markup)
    return ConversationHandler.END  # Conversation complete


async def handle_city_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles city name entered by user
    Gets weather for city and returns to main menu
    """
    city = update.message.text.strip()  # Remove extra spaces
    
    weather_text = await get_weather_by_city(city)
    await update.message.reply_text(weather_text, reply_markup=reply_markup)
    return ConversationHandler.END  # Conversation complete


async def get_weather_by_coords(lat: float, lon: float) -> str:
    """
    Fetches weather data from OpenWeatherMap API using coordinates
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Formatted weather information string
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": WEATHER_API_KEY,
        "units": "metric"  # Celsius instead of Kelvin
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return "❌ Location not found. Please try again."
    data = response.json()
    city = data.get("name", "Unknown location")
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    description = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]

    # Format weather information
    weather_info = (
        f"🌦 Weather in {city}\n"
        f"🌡 Temperature: {temp}°C\n"
        f"🤔 Feels like: {feels_like}°C\n"
        f"📖 Description: {description}\n"
        f"💧 Humidity: {humidity}%\n"
        f"💨 Wind Speed: {wind_speed} m/s"
    )

    return weather_info


async def get_weather_by_city(city: str) -> str:
    """
    Fetches weather data from OpenWeatherMap API using city name
    
    Args:
        city: City name
    
    Returns:
        Formatted weather information string
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return "❌ City not found. Please try again."

    data = response.json()
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    description = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]

    # Format weather information
    weather_info = (
        f"🌦 Weather in {city}\n"
        f"🌡 Temperature: {temp}°C\n"
        f"🤔 Feels like: {feels_like}°C\n"
        f"📖 Description: {description}\n"
        f"💧 Humidity: {humidity}%\n"
        f"💨 Wind Speed: {wind_speed} m/s"
    )

    return weather_info


# ============================================================================
# 💱 CURRENCY FUNCTIONALITY
# ============================================================================

async def get_currency_rates() -> str:
    """
    Fetches and formats currency exchange rates from multiple APIs
    Includes: Fiat currencies, cryptocurrencies, and precious metals
    
    Returns:
        Formatted string with all rates
    """
    # ========================================================================
    # 🏦 FIAT CURRENCIES CONFIGURATION
    # ========================================================================
    # Dictionary mapping currency codes to display names with flags
    target_currencies = {
        'GBP': '🇬🇧 British Pound',
        'EUR': '🇪🇺 Euro', 
        'USD': '🇺🇸 US Dollar',
        'CAD': '🇨🇦 Canadian Dollar',
        'AUD': '🇦🇺 Australian Dollar',
        'AED': '🇦🇪 UAE Dirham',
        'JPY': '🇯🇵 Japanese Yen'
    }
    
    # ========================================================================
    # 🪙 FETCH CRYPTOCURRENCY PRICES
    # ========================================================================
    crypto_url = "https://api.coingecko.com/api/v3/simple/price"
    crypto_params = {
        "ids": "bitcoin,ethereum,cardano",
        "vs_currencies": "usd"
    }
    
    try:
        crypto_response = requests.get(crypto_url, params=crypto_params, timeout=10)
        crypto_data = crypto_response.json()
    except:
        crypto_data = {}  # Empty dict if API fails
    
    # ========================================================================
    # 💵 FETCH FIAT CURRENCY EXCHANGE RATES
    # ========================================================================
    fiat_rates = {}  # Dictionary to store formatted rates
    
    try:
        # Using Frankfurter API - Free, reliable, no API key needed
        fiat_url = "https://api.frankfurter.app/latest?from=USD"
        fiat_response = requests.get(fiat_url, timeout=10)
        
        if fiat_response.status_code == 200:
            fiat_data = fiat_response.json()
            base_rates = fiat_data.get('rates', {})
            
            # Add USD with rate 1.0 (base currency)
            base_rates['USD'] = 1.0
            
            # Format each requested currency
            for currency_code, currency_name in target_currencies.items():
                rate = base_rates.get(currency_code, 'N/A')
                if rate != 'N/A':
                    # Different formatting for JPY (large numbers, 1 decimal)
                    if currency_code == 'JPY':
                        fiat_rates[currency_name] = f"{rate:.1f}"
                    else:
                        fiat_rates[currency_name] = f"{rate:.3f}"
                else:
                    fiat_rates[currency_name] = "N/A"
        else:
            # If API fails, mark all as N/A
            for currency_name in target_currencies.values():
                fiat_rates[currency_name] = "N/A"
    except Exception as e:
        # Log error and set all rates to N/A
        print(f"Error fetching fiat rates: {e}")
        for currency_name in target_currencies.values():
            fiat_rates[currency_name] = "N/A"
    
    # ========================================================================
    # 🥇 FETCH PRECIOUS METALS PRICES
    # ========================================================================
    metals = {"XAU": "🥇 Gold", "XAG": "🥈 Silver"}
    metals_prices = {}
    
    for code, name in metals.items():
        url = f"https://www.goldapi.io/api/{code}/USD"
        headers = {"x-access-token": METALS_API_KEY}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                price = data.get("price", "N/A")
                if price != "N/A":
                    metals_prices[name] = f"${float(price):,.2f}"
                else:
                    metals_prices[name] = "N/A"
            else:
                metals_prices[name] = "N/A"
        except:
            metals_prices[name] = "N/A"

    # ========================================================================
    # 📝 FORMAT FINAL MESSAGE
    # ========================================================================
    message = "💱 Latest Currency & Commodity Rates\n\n"
    
    # 1. FIAT CURRENCIES SECTION
    message += "💰 Fiat Currencies (1 USD =):\n"
    for currency_name, rate in fiat_rates.items():
        message += f"  {currency_name}: {rate}\n"
    message += "\n"
    
    # 2. CRYPTOCURRENCIES SECTION
    message += "🪙 Cryptocurrencies:\n"
    btc_price = crypto_data.get('bitcoin', {}).get('usd', 'N/A')
    eth_price = crypto_data.get('ethereum', {}).get('usd', 'N/A')
    ada_price = crypto_data.get('cardano', {}).get('usd', 'N/A')
    
    # Format each cryptocurrency with appropriate decimal places
    if btc_price != 'N/A':
        message += f"  • Bitcoin: ${float(btc_price):,.2f}\n"
    else:
        message += "  • Bitcoin: N/A\n"
        
    if eth_price != 'N/A':
        message += f"  • Ethereum: ${float(eth_price):,.2f}\n"
    else:
        message += "  • Ethereum: N/A\n"
        
    if ada_price != 'N/A':
        message += f"  • Cardano: ${float(ada_price):,.6f}\n"
    else:
        message += "  • Cardano: N/A\n"
    message += "\n"
    
    # 3. METALS SECTION
    message += "⚪ Metals (per ounce):\n"
    for metal_name, price in metals_prices.items():
        message += f"  {metal_name}: {price}\n"
    
    # 4. TIMESTAMP SECTION
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    message += f"\n⏰ Last updated: {current_time}"

    return message


# ============================================================================
# 🚀 BOT SETUP & MAIN EXECUTION
# ============================================================================

def main():
    """
    Main function to set up and run the Telegram bot
    """
    # Create bot application with your token
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # ========================================================================
    # 🎪 CONVERSATION HANDLER SETUP
    # ========================================================================
    # ConversationHandler manages multi-step conversations with users
    conv_handler = ConversationHandler(
        # Entry points - How conversations start
        entry_points=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons)
        ],
        
        # States - Different points in conversation
        states={
            WEATHER_METHOD: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons)
            ],
            CITY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_name)
            ]
        },
        
        # Fallbacks - What happens if something goes wrong
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.TEXT & filters.Regex("^Currency💲$"), handle_buttons)
        ]
    )

    # ========================================================================
    # 📞 REGISTER COMMAND HANDLERS
    # ========================================================================
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv_handler)  # Add conversation handler last

    # ========================================================================
    # ▶️ START THE BOT
    # ========================================================================
    print("🤖 Bot is starting...")
    print("📡 Listening for messages...")
    print("❌ Press Ctrl+C to stop the bot")
    
    # Start polling for updates from Telegram
    app.run_polling()


# ============================================================================
# 🎬 ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    # This ensures the script only runs when executed directly
    # (not when imported as a module)
    main()
        