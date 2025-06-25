import logging
import os
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from hashlib import sha256
import random
from PIL import Image, ImageDraw
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Logger
logging.basicConfig(level=logging.INFO)

# Provably Fair Mines Calculation
def get_mines(client_seed, server_seed, nonce, num_mines):
    combined_seed = f"{server_seed}:{client_seed}:{nonce}"
    hash_bytes = sha256(combined_seed.encode()).digest()
    tiles = list(range(25))
    rng = random.Random(hash_bytes)
    rng.shuffle(tiles)
    return sorted(tiles[:num_mines])

# Generate Image
def draw_grid(mines):
    size = 5
    tile_size = 100
    img = Image.new("RGB", (size * tile_size, size * tile_size), "white")
    draw = ImageDraw.Draw(img)
    for i in range(size * size):
        x = (i % size) * tile_size
        y = (i // size) * tile_size
        fill_color = "red" if i in mines else "green"
        draw.rectangle([x, y, x + tile_size, y + tile_size], fill=fill_color)
        draw.rectangle([x, y, x + tile_size, y + tile_size], outline="black")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        img.save(tmp_file.name)
        return tmp_file.name

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Stake Mines Predictor Bot.\nUse /login <your_passkey>")

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /login <passkey>")
        return
    if context.args[0] == API_SECRET_KEY:
        context.user_data["logged_in"] = True
        await update.message.reply_text("✅ Logged in! Use /predict <client_seed> <server_seed> <nonce> <num_mines>")
    else:
        await update.message.reply_text("❌ Wrong passkey.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("logged_in"):
        await update.message.reply_text("🔒 You are not logged in. Use /login first.")
        return
    if len(context.args) != 4:
        await update.message.reply_text("Usage: /predict <client_seed> <server_seed> <nonce> <num_mines>")
        return
    client_seed, server_seed, nonce_str, num_mines_str = context.args
    try:
        nonce = int(nonce_str)
        num_mines = int(num_mines_str)
        if not (1 <= num_mines <= 24):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Nonce and num_mines must be integers (1-24).")
        return
    mines = get_mines(client_seed, server_seed, nonce, num_mines)
    image_path = draw_grid(mines)
    await update.message.reply_photo(photo=open(image_path, 'rb'), caption=f"Mines: {mines}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Begin\n/login <passkey>\n/predict <client_seed> <server_seed> <nonce> <num_mines>")

# App Setup
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("help", help_command))
    app.run_polling()

if __name__ == "__main__":
    main()