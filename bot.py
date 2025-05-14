import os
import discord
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
from dotenv import load_dotenv

# --- Carrega variáveis de ambiente ---
load_dotenv()
DISCORD_TOKEN       = os.getenv('DISCORD_TOKEN')
SPREADSHEET_ID      = os.getenv('SPREADSHEET_ID')
CHECKIN_CHANNEL_ID  = int(os.getenv('CHECKIN_CHANNEL_ID'))
TIMEZONE            = 'America/Sao_Paulo'

# --- Autenticação Google Sheets ---
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc    = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# --- Configuração do bot Discord ---
intents = discord.Intents.default()
intents.message_content = True  # para ler o conteúdo das mensagens
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'[+] Bot conectado como {client.user}')

@client.event
async def on_message(message):
    # Ignora bots ou mensagens em DM
    if message.author.bot or message.guild is None:
        return

    # Checa canal pelo ID
    if message.channel.id != CHECKIN_CHANNEL_ID:
        return

    # Comando único !presença
    if message.content.strip().lower() != '!presença':
        return

    # Usa o nickname no servidor
    discord_nick = message.author.display_name
    discord_id   = str(message.author.id)

    # Data e hora atuais em São Paulo
    now  = datetime.now(pytz.timezone(TIMEZONE))
    data = now.strftime('%d/%m/%Y')
    hora = now.strftime('%H:%M:%S')

    # Verifica se o usuário já registrou presença hoje
    registros = sheet.get_all_values()
    for row in registros:
        if len(row) >= 3 and row[1] == discord_id and row[2] == data:
            await message.reply('⚠️ Você já registrou sua presença hoje combatente!')
            return

    # Append na planilha: [Discord Nick, Discord ID, Data]
    try:
        sheet.append_row([discord_nick, discord_id, data])
        await message.reply(
            f'✅ Presença registrada :\n'
            f'• Nome: `{discord_nick}`\n'
            f'• ID: `{discord_id}`\n'
            f'• Data: {data}'
        )
    except Exception as e:
        await message.reply(f'❌ Falha ao registrar no Sheets: {e}')

if __name__ == '__main__':
    client.run(DISCORD_TOKEN)
