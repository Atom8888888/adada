from re import match
import nextcord
from nextcord.ext import commands
import requests
import json
import os
import aiohttp
import datetime

from myserver import server_on


config = json.load(open('config.json'))

intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!',intents=intents,help_command=None)

async def logsend(embed):
  async with aiohttp.ClientSession() as session:
    webhook = nextcord.Webhook.from_url(config['webhook'], session=session)
    await webhook.send(embed=embed)

class Topup(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("โดเนทผ่านระบบซองอั่งเปา")  
        self.topup = nextcord.ui.TextInput(
            label="เติมเงินด้วยอังเปา (ห้ามมีตัว # อยู่ในลิงค์)",
            placeholder="กรอกลิงค์ซองอั่งเปา💸💰 | URL",
            required=True
        )
        self.add_item(self.topup)
    async def callback(self, interaction: nextcord.Interaction):
        redeemfaile = nextcord.Embed(title=" ", description=f"`❌ รับเงินไม่สำเร็จ` `|` คุณ <@{interaction.user.id}> \n **{self.topup.value}**",color=0xFF0000)
        redeemfaile.timestamp = datetime.datetime.utcnow()
        if (not match (r"https:\/\/gift\.truemoney\.com\/campaign\/\?v=+[a-zA-Z0-9]{18}", self.topup.value)):
           await interaction.send(f"ตลกหรอไอสัสนรกหมาเย็ดเเม่ควยไรอ่ะสัสจะด่ากะกูปะ", ephemeral = True) 
           await logsend(embed=redeemfaile)
           return
        voucher_code = self.topup.value.split("?v=")[1]
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/8a0.0.3987.149 Safari/537.36'}
        response = requests.post(f'https://gift.truemoney.com/campaign/vouchers/{voucher_code}/redeem', headers=headers, json={"mobile": config['phone'], "voucher_hash": f"{voucher_code}"})
        redeemdata = response.json()
        amount = redeemdata['data']['tickets'][0]['amount_baht']
        if response.status_code == 200 and redeemdata["status"]["code"] == "SUCCESS" :
            f = open('./db/db.json')
            db = json.load(f)
            db["money"] += float(amount)
            db["count"] += 1
            json.dump(db, open("./db/db.json", "w"), indent = 4)
            redeemdone = nextcord.Embed(title=" ", description=f"`✅ รับเงินสำเร็จ` `|` คุณ <@{interaction.user.id}> โดเนทเข้ามาเป็นจำนวนเงิน {amount} บาท\n **{self.topup.value}**\nสร้างซองโดย : `{redeemdata['data']['owner_profile']['full_name']}`",color=0x00FF00)
            redeemdone.timestamp = datetime.datetime.utcnow()
            await logsend(embed=redeemdone)
            if amount >= config['money']:
               if config['addrole'] == 'off':
                pass  
               else:
                role = nextcord.utils.get(interaction.guild.roles, id=int(config['roleid']))
                if role in interaction.user.roles:
                    await interaction.send(f"มียศอยู่แล้ว", ephemeral = True)
                else:
                    role_id = config['roleid']
                    await interaction.send(f"ให้ยศ <@&{role_id}> สำเร็จ", ephemeral = True)
                    role = interaction.guild.get_role(int(role_id))
                    await interaction.user.add_roles(role)
                    await interaction.guild.get_channel(config['notify_channel_id']).send(embed=nextcord.Embed(description=f'{interaction.user.mention} โดเนทสำเร็จ {amount} บาท\n\n**ได้รับยศ**\n• <@&{role_id}>',color=0x00FF00))
        if response.status_code ==  400 or response.status_code == 404:
            await interaction.send(f"ซองอั่งเปานี้ถูกใช้ไปแล้ว หรือ ลิงค์อั่งเปาให้ถูกต้อง ", ephemeral = True)
            await logsend(embed=redeemfaile)

class Button(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label="กดเพื่อซื้อยศ", style=nextcord.ButtonStyle.blurple, emoji="🧧",custom_id="donate")
    async def donate(self, button: nextcord.Button, interaction: nextcord.Interaction):
                await interaction.response.send_modal(Topup())



@bot.event
async def on_ready():
    bot.add_view(Button())
    print(f"BOT NAME : {bot.user}")
    await bot.change_presence(activity=nextcord.Streaming(name="!",url="https://www.twitch.tv/zanexywex"))
    

@bot.command(pass_context = True)
async def topup(ctx):
    if ctx.author.guild_permissions.administrator:
            await ctx.message.delete()
            embed = nextcord.Embed(title="🧧 ซื้อยศผ่านระบบซองอั่งเปา 🧧",color=0xFF6961)
            embed.set_image(url="https://media.discordapp.net/attachments/994249006584692816/998162183894618122/unknown.png")
            await ctx.send(embed=embed, view=Button())
    else:
        await ctx.reply('มึงไม่มีสิทธิ์ใช้ครับไอ้โง่')


@bot.command(pass_context = True)
async def check(ctx):
  if ctx.author.guild_permissions.administrator:
    addrole = ''
    if config['addrole'] == 'on':
        addrole = 'เปิด'
    else: 
        addrole = 'ปิด'
    embed = nextcord.Embed(title="การตั้งค่าบอท",description=f"เบอร์ที่รับเงิน : {config['phone']}\nให้ยศเมื่อโดเนท : {addrole}\nเงินเมื่อโดเนทถึง : {config['money']}\nไอดียศ : {config['roleid']} ( <@&{config['roleid']}> )")
    await ctx.reply(embed=embed)
  else:
        await ctx.reply('มึงไม่มีสิทธิ์ใช้ครับไอ้โง่')

@bot.command()
async def data(ctx):    
  if ctx.author.guild_permissions.administrator:
    d = open('./db/db.json')
    db = json.load(d)
    embed = nextcord.Embed(title=" ",description=f"**มีคนโดเนทมาทั้งหมด `{db['money']}` บาท**\n**มีคนโดเนทมา `{db['count']}` คน**",color=0xFFFF00)
    embed.timestamp = datetime.datetime.utcnow()
    await ctx.send(embed=embed)
  else:
        await ctx.reply('มึงไม่มีสิทธิ์ใช้ครับไอ้โง่')
    
 server_on()    
   
bot.run(os.getenv('token'))