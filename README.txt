=== BOT MUSIK DISCORD PYTHON ===

REQUIREMENT:
1. Python 3.8+
2. FFmpeg (download dari https://ffmpeg.org/download.html)
3. Discord Bot Token (buat di https://discord.com/developers/applications)

INSTALASI:

1. Install Python dependencies:
   pip install -r requirements.txt

2. Install FFmpeg:
   - Windows: Download dari ffmpeg.org, extract, tambahkan ke PATH
   - Atau gunakan: choco install ffmpeg (jika gunakan Chocolatey)
   - Linux: sudo apt-get install ffmpeg
   - macOS: brew install ffmpeg

3. Buat Discord Bot:
   - Buka https://discord.com/developers/applications
   - Klik "New Application"
   - Pilih "Bot" tab, klik "Add Bot"
   - Copy token bot
   - Buka file .env, paste token di DISCORD_TOKEN=...
   - Di "OAuth2" > "URL Generator", pilih scopes: bot, applications.commands, permissions: Send Messages, Connect, Speak, Use Voice Activity
   - Generate URL, buka di browser, invite bot ke server Discord

4. Jalankan bot:
   python bot.py

PERINTAH BOT (Slash Commands):
- /join         → Bot masuk ke voice channel Anda
- /play <query> → Putar musik (URL YouTube atau judul)
- /skip         → Lewati lagu
- /pause        → Jeda musik
- /resume       → Lanjutkan musik
- /stop         → Hentikan musik & bot keluar
- /queue        → Lihat antrean lagu

CONTOH PENGGUNAAN:
/play query:https://www.youtube.com/watch?v=dQw4w9WgXcQ
/play query:despacito
/skip
/queue

TROUBLESHOOTING:
- Error "DISCORD_TOKEN tidak ditemukan": Pastikan .env ada dan berisi token yang benar
- Error FFmpeg: Pastikan FFmpeg sudah terinstall dan ada di PATH
- Bot tidak connect ke voice: Pastikan bot punya permission Connect & Speak di server
- Slash command tidak muncul: Pastikan bot di-invite dengan scope "applications.commands" dan butuh waktu beberapa menit untuk sync command ke Discord
