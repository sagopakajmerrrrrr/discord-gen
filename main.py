import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

kullanici_bekleme_sureleri = {}

# ==========================================
# GÖRSEL TEMA VE RENK PALETİ
# ==========================================
THEME_COLOR = 0xFF4655   # Valorant Kırmızısı / Vurgu Rengi
SUCCESS_COLOR = 0x00E676 # Neon Yeşil / Başarı
ERROR_COLOR = 0xFF5252   # Parlak Kırmızı / Hata
DARK_EMBED = 0x1A1C23    # Koyu Arayüz Arka Planı

class GenBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        intents.message_content = True
        
        self.invite_cache = {} 
        
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # await self.tree.sync()
        print(f"⚡ [GEN BOT] {self.user} olarak giriş yapıldı!")

    async def on_ready(self):
        for guild in self.guilds:
            try:
                invites = await guild.invites()
                self.invite_cache[guild.id] = {invite.code: invite.uses for invite in invites}
            except discord.Forbidden:
                print(f"⚠️ [{guild.name}] sunucusunda davetleri okuma iznim yok!")

bot = GenBot()
@bot.event
async def on_invite_create(invite):
    if invite.guild.id in bot.invite_cache:
        bot.invite_cache[invite.guild.id][invite.code] = invite.uses

@bot.event
async def on_invite_delete(invite):
    if invite.guild.id in bot.invite_cache and invite.code in bot.invite_cache[invite.guild.id]:
        del bot.invite_cache[invite.guild.id][invite.code]

# ==========================================
# 1. GELİŞMİŞ KARŞILAMA VE İNVİTE SİSTEMİ
# ==========================================
@bot.event
async def on_member_join(member):
    KARSILAMA_KANALI_ID = 123456789012345678  # Kendi Karşılama Kanal ID'nizi Yazın
    
    kanal = bot.get_channel(KARSILAMA_KANALI_ID)
    if not kanal:
        return

    inviter = None
    invite_uses = 0
    
    try:
        new_invites = await member.guild.invites()
        old_invites = bot.invite_cache.get(member.guild.id, {})
        
        for invite in new_invites:
            if invite.code in old_invites and invite.uses > old_invites[invite.code]:
                inviter = invite.inviter
                invite_uses = invite.uses
                break
        
        bot.invite_cache[member.guild.id] = {invite.code: invite.uses for invite in new_invites}
    except discord.Forbidden:
        pass 
    
    created_time = f"<t:{int(member.created_at.timestamp())}:R>"
    
    if inviter:
        inviter_text = f"{inviter.name} ({invite_uses} Davet)"
    else:
        inviter_text = "Özel URL / Bulunamadı"

    mesaj = (
        f"```md\n# WELCOME TO {member.guild.name.upper()}\n```\n"
        f"✛ **Kullanıcı:** {member.mention}\n"
        f"✛ **Hesap Yaşı:** {created_time}\n"
        f"✛ **Davet Eden:** `{inviter_text}`\n"
        f"✛ **Toplam Üye:** `{member.guild.member_count}`"
    )
    
    await kanal.send(mesaj)

# ==========================================
# 2. MODERASYON KOMUTLARI
# ==========================================
@bot.tree.command(name="ban", description="Belirtilen kullanıcıyı sunucudan yasaklar.")
@app_commands.checks.has_permissions(ban_members=True)
async def ban_command(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
    await kullanici.ban(reason=sebep)
    embed = discord.Embed(
        title="🔨 Kullanıcı Yasaklandı",
        description=f"**Hedef:** {kullanici.mention} (`{kullanici.id}`)\n**Sebep:** {sebep}",
        color=ERROR_COLOR,
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text=f"Yetkili: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="mute", description="Belirtilen kullanıcıyı belirli bir süre susturur.")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute_command(interaction: discord.Interaction, kullanici: discord.Member, dakika: int, sebep: str = "Sebep belirtilmedi"):
    sure = datetime.timedelta(minutes=dakika)
    await kullanici.timeout(sure, reason=sebep)
    embed = discord.Embed(
        title="🔇 Kullanıcı Susturuldu",
        description=f"**Hedef:** {kullanici.mention}\n**Süre:** {dakika} dakika\n**Sebep:** {sebep}",
        color=THEME_COLOR,
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text=f"Yetkili: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="istatistik", description="Sunucudaki aktif, çevrimdışı ve toplam üye sayısını gösterir.")
async def istatistik_command(interaction: discord.Interaction):
    guild = interaction.guild
    toplam_uye = guild.member_count
    aktif_uye = sum(1 for m in guild.members if m.status != discord.Status.offline)
    afk_uye = toplam_uye - aktif_uye
    
    embed = discord.Embed(
        title=f"📊 {guild.name} İstatistik Paneli",
        color=THEME_COLOR,
        timestamp=datetime.datetime.now()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    embed.add_field(name="👥 Toplam Üye", value=f"```yaml\n{toplam_uye}\n```", inline=True)
    embed.add_field(name="🟢 Aktif Üye", value=f"```yaml\n{aktif_uye}\n```", inline=True)
    embed.add_field(name="⚫ AFK / Çevrimdışı", value=f"```yaml\n{afk_uye}\n```", inline=True)
    embed.set_footer(text="Zalorant Account System", icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

# ==========================================
# 3. GELİŞMİŞ GEN SİSTEMİ
# ==========================================
@bot.tree.command(name="gen", description="Yetkinize uygun kategoriden hesap alın")
@app_commands.describe(kategori="Hangi kategoriden veri almak istiyorsunuz?")
@app_commands.choices(kategori=[
    app_commands.Choice(name="🤍 Ücretsiz", value="ucretsiz"),
    app_commands.Choice(name="💜 Booster", value="booster"),
    app_commands.Choice(name="💛 VIP", value="vip")
])
async def gen(interaction: discord.Interaction, kategori: app_commands.Choice[str]):
    
    user_id = interaction.user.id
    now = datetime.datetime.now()
    
    if user_id in kullanici_bekleme_sureleri:
        bitis_zamani = kullanici_bekleme_sureleri[user_id]
        if now < bitis_zamani:
            kalan_sure = bitis_zamani - now
            dakika, saniye = divmod(int(kalan_sure.total_seconds()), 60)
            
            error_embed = discord.Embed(
                title="⏳ Soğuma Süresi Aktif",
                description=f"Bu komutu tekrar kullanabilmek için **{dakika} dakika {saniye} saniye** beklemelisiniz.",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

    BOOSTER_ROL_ID = 1537980520850399272 # Booster Rol ID
    VIP_ROL_ID = 1376577501056340079     # VIP Rol ID
    
    if kategori.value == "ucretsiz":
        durum_uygun = False
        uye = interaction.guild.get_member(interaction.user.id)
        
        for activity in uye.activities:
            if isinstance(activity, discord.CustomActivity):
                if activity.name and "discord.gg/TraVbr8wM4" in activity.name:
                    durum_uygun = True
                    break
        
        if not durum_uygun:
            error_embed = discord.Embed(
                title="❌ Özel Durum Şartı Sağlanmadı",
                description="Ücretsiz kategoriyi kullanabilmek için Discord Özel Durumunuza (Custom Status) aşağıdaki davet bağlantısını eklemelisiniz:\n\n`discord.gg/TraVbr8wM4`",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

    kullanici_rolleri = [rol.id for rol in interaction.user.roles]
    if kategori.value == "booster" and BOOSTER_ROL_ID not in kullanici_rolleri:
        error_embed = discord.Embed(
            title="❌ Yetersiz Yetki",
            description="Bu kategoriden hesap alabilmek için sunucuya **Takviye (Boost)** yapmış olmanız gerekmektedir.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return
        
    if kategori.value == "vip" and VIP_ROL_ID not in kullanici_rolleri:
        error_embed = discord.Embed(
            title="❌ Yetersiz Yetki",
            description="Bu kategoriden hesap alabilmek için **VIP** rolüne sahip olmalısınız.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        return

    dosya_yolu = f"{kategori.value}.txt"
    if not os.path.exists(dosya_yolu):
        with open(dosya_yolu, "w", encoding="utf-8") as f:
            pass
            
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        satirlar = f.readlines()
        
    satirlar = [satir.strip() for satir in satirlar if satir.strip()]
    if not satirlar:
        stok_embed = discord.Embed(
            title="📦 Stok Tükenmiş",
            description=f"Üzgünüz, **{kategori.name}** kategorisinde şu anda kullanılabilir stok bulunmuyor.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=stok_embed, ephemeral=True)
        return
        
    verilen_hesap = satirlar.pop(0)
    kalan_stok = len(satirlar)
    
    with open(dosya_yolu, "w", encoding="utf-8") as f:
        for satir in satirlar:
            f.write(satir + "\n")
            
    # DM İÇİN ÖZEL TESLİMAT EMBED'İ
    dm_embed = discord.Embed(
        title="🎉 Hesabınız Teslim Edildi!",
        description="Teslim edilen hesap bilgileri aşağıda yer almaktadır. Lütfen bilgilerinizi kimseyle paylaşmayın.",
        color=THEME_COLOR,
        timestamp=datetime.datetime.now()
    )
    dm_embed.add_field(name="🔑 Kategori", value=f"`{kategori.name}`", inline=True)
    dm_embed.add_field(name="📦 Kalan Stok", value=f"`{kalan_stok}`", inline=True)
    dm_embed.add_field(name="📋 Hesap Bilgisi (User:Pass)", value=f"```yaml\n{verilen_hesap}\n```", inline=False)
    dm_embed.set_footer(text="Zalorant Account System", icon_url=interaction.user.display_avatar.url)
    
    try:
        await interaction.user.send(embed=dm_embed)
    except discord.Forbidden:
        with open(dosya_yolu, "a", encoding="utf-8") as f:
            f.write(verilen_hesap + "\n")
            
        dm_error = discord.Embed(
            title="❌ DM Gönderilemedi",
            description="DM kutunuz kapalı olduğu için hesabınız iletilemedi. Lütfen sunucu üyelerinden gelen doğrudan mesajlara izin verip tekrar deneyin.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=dm_error, ephemeral=True)
        return

    bekleme_dakikasi = 20 if kategori.value == "vip" else 30
    kullanici_bekleme_sureleri[user_id] = now + datetime.timedelta(minutes=bekleme_dakikasi)

    # SUNUCU KANALINA GÖNDERİLECEK BAŞARI EMBED'İ
    kanal_embed = discord.Embed(
        title="⚡ Hesap Teslimatı Tamamlandı",
        color=SUCCESS_COLOR,
        timestamp=datetime.datetime.now()
    )
    kanal_embed.add_field(name="👤 Kullanıcı", value=interaction.user.mention, inline=True)
    kanal_embed.add_field(name="🏷️ Kategori", value=kategori.name, inline=True)
    kanal_embed.add_field(name="📊 Kalan Stok", value=f"`{kalan_stok}`", inline=True)
    kanal_embed.add_field(name="📬 Teslimat", value="Hesap detayları **DM kutunuza** başarıyla iletildi!", inline=False)
    kanal_embed.set_footer(text="Zalorant Generator System", icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=kanal_embed)

    # ================== GİZLİ LOG KANALI ==================
    GIZLI_LOG_KANALI_ID = 1533546724289806468 
    
    log_kanali = bot.get_channel(GIZLI_LOG_KANALI_ID)
    if log_kanali:
        log_embed = discord.Embed(
            title="🕵️ Hesap Teslimat Günlüğü",
            color=THEME_COLOR,
            timestamp=datetime.datetime.now()
        )
        log_embed.add_field(name="Kullanıcı", value=f"{interaction.user.mention}\n`ID: {interaction.user.id}`", inline=True)
        log_embed.add_field(name="Kategori", value=f"`{kategori.name}`", inline=True)
        log_embed.add_field(name="Kalan Stok", value=f"`{kalan_stok}`", inline=True)
        log_embed.add_field(name="Verilen Veri", value=f"```yaml\n{verilen_hesap}\n```", inline=False)
        log_embed.set_footer(text="Audit Log System")
        await log_kanali.send(embed=log_embed)

bot.run(os.getenv("DISCORD_TOKEN"))

