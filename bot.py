import discord
from discord.ext import tasks, commands
import requests
import datetime
import pytz
import os
import random
from dotenv import load_dotenv  # Đọc file .env
import alive  # Giữ bot sống trên Render

# --- CẤU HÌNH HỆ THỐNG ---
load_dotenv() # Nạp biến môi trường

# Lấy Key từ file .env hoặc Render Environment
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

# ID kênh Discord 
CHANNEL_ID = 1447974762717642973

# Kiểm tra Token
if not DISCORD_TOKEN:
    print("Không tìm thấy DISCORD_TOKEN.")
    exit()

# --- CÁC HÀM LẤY DỮ LIỆU (API) ---

def get_trending_movie():
    """Lấy phim hot trong ngày từ TMDB"""
    if not TMDB_API_KEY: 
        print("Thiếu TMDB API Key -> Bỏ qua phần phim.")
        return None
    try:
        url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}&language=vi-VN"
        response = requests.get(url).json()
        if 'results' in response and len(response['results']) > 0:
            movie = response['results'][0] # Lấy phim top 1
            return {
                "title": movie.get('title'),
                "overview": movie.get('overview', 'Chưa có mô tả.'),
                "rating": movie.get('vote_average'),
                "poster": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}"
            }
    except Exception as e:
        print(f"Lỗi lấy phim: {e}")
    return None

def get_top_manga():
    """Lấy manga từ Jikan API"""
    try:
        # Random page để đổi mới mỗi ngày
        page = random.randint(1, 3)
        url = f"https://api.jikan.moe/v4/top/manga?page={page}"
        response = requests.get(url).json()
        if 'data' in response and len(response['data']) > 0:
            manga = random.choice(response['data']) # Chọn ngẫu nhiên
            return {
                "title": manga.get('title'),
                "url": manga.get('url'),
                "score": manga.get('score'),
                "image": manga['images']['jpg']['image_url']
            }
    except Exception as e:
        print(f"Lỗi lấy truyện: {e}")
    return None

# --- LOGIC GỬI TIN ---
async def send_daily_content(channel):
    print("⏳ Đang lấy dữ liệu...")
    
    movie = get_trending_movie()
    manga = get_top_manga()

    # 1. Gửi Phim
    if movie:
        embed = discord.Embed(title=f"🎬 Phim Hot Hôm Nay: {movie['title']}", 
                              description=movie['overview'][:300] + "...", 
                              color=0xE50914) # Đỏ Netflix
        embed.add_field(name="Đánh giá", value=f"⭐ {movie['rating']}/10", inline=True)
        if movie['poster']: embed.set_image(url=movie['poster'])
        await channel.send(embed=embed)
    
    # 2. Gửi Truyện
    if manga:
        embed = discord.Embed(title=f"📖 Truyện Hay Nên Đọc: {manga['title']}", 
                              url=manga['url'], 
                              color=0x3498DB) # Xanh dương
        embed.add_field(name="Điểm số", value=f"⭐ {manga['score']}", inline=True)
        if manga['image']: embed.set_thumbnail(url=manga['image'])
        await channel.send(embed=embed)
        
    print("Đã gửi xong bản tin!")

# --- THIẾT LẬP BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 Bot đã đăng nhập: {bot.user}')
    if not daily_schedule.is_running():
        daily_schedule.start()

@bot.command()
async def test(ctx):
    await ctx.send("Đang chạy thử lệnh Recommend...")
    await send_daily_content(ctx.channel)

# --- HẸN GIỜ (08:00 VN) ---
timezone_vn = pytz.timezone('Asia/Ho_Chi_Minh')
time_to_run = datetime.time(hour=8, minute=0, second=0, tzinfo=timezone_vn)

@tasks.loop(time=time_to_run)
async def daily_schedule():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await send_daily_content(channel)
    else:
        print(f"❌ Không tìm thấy kênh ID: {CHANNEL_ID}")

@daily_schedule.before_loop
async def before_daily_schedule():
    await bot.wait_until_ready()

# --- CHẠY ---
if __name__ == "__main__":
    alive.keep_alive()
    bot.run(DISCORD_TOKEN)