import discord
from discord.ext import commands
import sqlite3

# ====== KONFIGURASI BOT ======
TOKEN = "MASUKKAN_TOKEN_DISCORD_ANDA"  # Ganti dengan token bot Anda
PREFIX = "!"
INTENTS = discord.Intents.default()
INTENTS.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=INTENTS)

# ====== DATABASE SETUP ======
DB_NAME = "sampah.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabel riwayat pengecekan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS riwayat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            sampah TEXT NOT NULL,
            kategori TEXT NOT NULL
        )
    """)
    # Tabel data sampah
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_sampah (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT UNIQUE NOT NULL,
            kategori TEXT NOT NULL
        )
    """)
    # Tabel poin user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poin_user (
            user TEXT PRIMARY KEY,
            poin INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ====== FUNGSI DATABASE ======
def klasifikasi_sampah(nama):
    nama = nama.lower()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT kategori FROM data_sampah WHERE LOWER(nama) = ?", (nama,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Tidak diketahui"

def simpan_riwayat(user, sampah, kategori):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO riwayat (user, sampah, kategori) VALUES (?, ?, ?)",
                   (user, sampah, kategori))
    conn.commit()
    conn.close()

def tambah_data_sampah(nama, kategori):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO data_sampah (nama, kategori) VALUES (?, ?)", (nama.lower(), kategori.capitalize()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def tambah_poin(user, jumlah):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO poin_user (user, poin) VALUES (?, ?) ON CONFLICT(user) DO UPDATE SET poin = poin + ?",
                   (user, jumlah, jumlah))
    conn.commit()
    conn.close()

def get_poin(user):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT poin FROM poin_user WHERE user = ?", (user,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

# ====== COMMAND BOT ======
@bot.command(name="info")
async def info_bot(ctx):
    embed = discord.Embed(
        title=" Bot Pemilah Sampah",
        description="Bot ini membantu memilah sampah menjadi **Organik** atau **Anorganik**, menyimpan data, dan memberikan poin untuk kontribusi Anda.",
        color=0x00ff00
    )
    embed.add_field(name=" Perintah Utama", value=(
        "`!cek <nama_sampah>` → Mengecek kategori sampah\n"
        "`!tambah <nama_sampah> <organik/anorganik>` → Menambahkan data sampah baru (+10 poin)\n"
        "`!riwayat` → Melihat riwayat pengecekan Anda\n"
        "`!poin` → Melihat total poin Anda\n"
        "`!info` → Melihat informasi bot"
    ), inline=False)
    embed.add_field(name=" Sistem Poin", value="Setiap menambahkan data sampah baru, Anda mendapat **+10 poin**.", inline=False)
    embed.add_field(name=" Tujuan Bot", value="Meningkatkan kesadaran memilah sampah dan mengajak pengguna berkontribusi dalam menjaga lingkungan.", inline=False)
    embed.set_footer(text="Dikembangkan oleh Arkan Syawal Nuvadin • Gunakan dengan bijak dan bertanggung jawab")
    
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    print(f" Bot {bot.user} sudah online!")

@bot.command(name="cek")
async def cek_sampah(ctx, *, nama_sampah: str = None):
    if not nama_sampah:
        await ctx.send(" Harap masukkan nama sampah. Contoh: `!cek plastik`")
        return

    kategori = klasifikasi_sampah(nama_sampah)
    simpan_riwayat(str(ctx.author), nama_sampah, kategori)
    await ctx.send(f" Sampah **{nama_sampah}** termasuk kategori **{kategori}**.")

@bot.command(name="riwayat")
async def lihat_riwayat(ctx):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT sampah, kategori FROM riwayat WHERE user = ?", (str(ctx.author),))
    data = cursor.fetchall()
    conn.close()

    if not data:
        await ctx.send(" Belum ada riwayat pengecekan.")
        return

    riwayat_str = "\n".join([f"- {s} → {k}" for s, k in data])
    await ctx.send(f" **Riwayat pengecekan Anda:**\n{riwayat_str}")

@bot.command(name="tambah")
async def tambah_sampah(ctx, nama_sampah: str = None, kategori: str = None):
    if not nama_sampah or not kategori:
        await ctx.send(" Format salah. Gunakan: `!tambah <nama_sampah> <organik/anorganik>`")
        return

    kategori = kategori.lower()
    if kategori not in ["organik", "anorganik"]:
        await ctx.send(" Kategori hanya boleh `organik` atau `anorganik`.")
        return

    if tambah_data_sampah(nama_sampah, kategori):
        tambah_poin(str(ctx.author), 10)  # Tambah 10 poin
        total_poin = get_poin(str(ctx.author))
        await ctx.send(f" Data sampah **{nama_sampah}** ({kategori}) berhasil ditambahkan.\n Anda mendapat **+10 poin**! Total poin: **{total_poin}**")
    else:
        await ctx.send(f" Sampah **{nama_sampah}** sudah ada di database.")

@bot.command(name="poin")
async def cek_poin(ctx):
    total_poin = get_poin(str(ctx.author))
    await ctx.send(f" {ctx.author.mention}, total poin Anda: **{total_poin}**")

# ====== JALANKAN BOT ======
if __name__ == "__main__":
    if TOKEN == "TOKEN":
        print(" Harap masukkan token bot Discord Anda di variabel TOKEN.")
    else:
        bot.run(TOKEN)
