False qilib, loglarda xatolikni ko'rishimiz mumkin
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'quiet': False, 
        'no_warnings': False
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            # 'entries' ro'yxati mavjudligini tekshiramiz
            if 'entries' in info and len(info['entries']) > 0:
                video = info['entries'][0]
                return video.get('webpage_url'), video.get('title')
            return None, "Topilmadi"
        except Exception as e:
            print(f"Xatolik: {e}") # Render loglarida xatoni ko'rsatadi
            return None, str(e)


