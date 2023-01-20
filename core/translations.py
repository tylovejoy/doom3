import discord
from discord import app_commands
from core import translations2


class DoomTranslator(app_commands.Translator):

    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> str | None:
        locales = translations.get(string.message, None)
        if locales:
            return locales.get(locale.value)
        return None


translations = {
    "Overwatch share code": {"tr": "Overwatch paylaşım kodu"},
    "User name": {"tr": "Kullanıcı adı"},
    "Creator name": {"tr": "Yaratıcı adı"},
    "Overwatch map": {"tr": "Overwatch haritası"},
    "Type of parkour map": {"tr": "Parkur haritasının tipi"},
    "add": {"tr": "ekle"},
    "remove": {"tr": "sil"},
    "User display name (within bot commands only)": {"tr": "Kullanıcı takma adı (sadece bot komuları için geçerli)"},
    "Record in HH:MM:SS.ss format": {"tr": "Rekor HH:MM:SS.ss formatındadır"},
    "map_code": {"tr": "harita_kodu"},
    "creator": {"tr": "yaratıcı"},
    "new_level_name": {"tr": "yeni_level_adı"},
    "level_name": {"tr": "level_adı"},
    "map_name": {"tr": "harita_adı"},
    "user": {"tr": "kullanıcı"},
    "name": {"tr": "ad"},
    "nickname": {"tr": "takma-ad"},
    "map-maker": {"tr": "map-yaratıcısı"},
    "Map maker only commands": {"tr": "Harita yaratıcısına özel komutlar"},
    "level": {},
    "Edit levels": {"tr": "Levelları düzenle"},
    "Edit creators": {"tr": "Yaratıcıları düzenle"},
    "Remove a creator from your map": {"tr": "Haritandan bir yaratıcı sil"},
    "Add a creator to your map": {"tr": "Haritana bir yaratıcı ekle"},
    "Level name": {"tr": "Level adı"},
    "New level name": {"tr": "Yeni level adı"},
    "Add a level name to your map": {"tr": "Haritana level adı ekle"},
    "Remove a level name from your map": {"tr": "Haritandan level adı sil"},
    "rename": {"tr": "yeniden-adlandır"},
    "Rename a level in your map": {"tr": "Haritandaki bir levelı yeniden adlandır"},
    "submit-map": {"tr": "harita-gönder"},
    "Submit your map to the database": {"tr": "Haritanı veritabanına gönder"},
    "map-search": {"tr": "harita-arama"},
    "Search for maps based on various filters": {"tr": "Çeşitli filtrelere dayanarak haritaları ara"},
    "map_type": {"tr": "harita_tipi"},
    "guide": {"tr": "rehber"},
    "View guide(s) for a specific map": {"tr": "Belirli bir haritanın rehberlerini görüntüle"},
    "add-guide": {"tr": "rehber-ekle"},
    "Add a guide for a specific map": {"tr": "Belirli bir harita için rehber ekle"},
    "url": {},
    "Valid URL to guide (YouTube, Streamable, etc)": {"tr": "Rehber için geçerli URL (Youtube, Streamable vs.)"},
    "mod": {},
    "Mod only commands": {"tr": "Sadece modlar için geçerli komutlar"},
    "keep-alive": {"tr": "canlı-tutma"},
    "Keep threads alive": {"tr": "Alt başlıkları canlı tut"},
    "Add a keep-alive to a thread": {"tr": "Bir alt başlığa canlı-tutma ekle"},
    "Remove a keep-alive from a thread": {"tr": "Bir alt başlıktan canlı-tutma sil"},
    "thread": {"tr": "alt-başlık"},
    "Thread": {"tr": "Alt başlık"},
    "remove-record": {"tr": "rekor-sil"},
    "Remove a record from a user": {"tr": "Bir kullanıcıdan rekor sil"},
    "change-name": {"tr": "ad-değiş"},
    "Change a user's display name": {"tr": "Bir kullanıcının takma adını değiştir"},
    "alerts": {"tr": "alarmlar"},
    "Toggle Doombot verification alerts on/off": {"tr": "Doombot onaylanma alarmlarını aç/kapat"},
    "value": {"tr": "değer"},
    "Alerts on/off": {"tr": "Alarmları aç/kapat"},
    "Change your display name in bot commands": {"tr": "Takma adını bot komutlarından değiştir"},
    "brug-mode": {},
    "Emojify text": {"tr": "Metni Emojileştir"},
    "uwu": {},
    "UwUfy text": {"tr": "Metni UwUlaştır"},
    "text": {"tr": "metin"},
    "Text": {"tr": "Metin"},
    "blarg": {},
    "BLARG": {},
    "u": {},
    "Insult someone": {"tr": "Birine hakaret et"},
    "increase": {},
    "Increase! Beware the knife...": {},
    "decrease": {"tr": None},
    "Decrease! Beware the growth pills...": {},
    "personal-records": {"tr": "kişisel-rekorlar"},
    "world-records": {"tr": "dünya-rekorları"},
    "submit-record": {"tr": "rekor-gönder"},
    "Submit a record to the database. Video proof is required for full verification!": {"tr": "Veritabanına bir rekor gönder. Tam onaylama için video kanıtı gereklidir!"},
    "record": {"tr": "rekor"},
    "screenshot": {"tr": "ekran-görüntüsü"},
    "Screenshot of completion": {"tr": "Tamamlamanın ekran görüntüsü"},
    "video": {},
    "Video of play through. REQUIRED FOR FULL VERIFICATION!": {"tr": "Oynama videosu. TAM ONAYLAMA İÇİN GEREKLİDİR!"},
    "rating": {"tr": "değerlendirme"},
    "What would you rate the quality of this level?": {"tr": "Bu levelın kalitesini nasıl değerlendirirdiniz?"},
    "leaderboard": {"tr": "skor-tahtası"},
    "View leaderboard of any map in the database.": {"tr": "Herhangi bir haritanın skor tahtasını görüntüle"},
    "verified": {"tr": "onaylanmış"},
    "Only show fully verified video submissions": {"tr": "Sadece tamamen onaylanmış video gönderilerini göster"},
    "View your (by default) personal records or another users": {"tr": "Kendinin (varsayılan) ya da başkasının rekorlarını görüntüle"},
    "wr_only": {"tr": "sadece-dr"},
    "Only show world records, if any": {"tr": "Eğer varsa, sadece dünya rekorlarını göster"},
    "tag": {"tr": "etiket"},
    "view": {"tr": "görüntüle"},
    "View a tag": {"tr": "Bir etiketi görüntüle"},
    "Name of the tag": {"tr": "Etiketin adı"},
    "create": {"tr": "oluştur"},
    "Create a tag": {"tr": "Bir etiket oluştur"},
}
