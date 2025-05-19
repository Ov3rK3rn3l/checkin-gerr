import os
import discord
import gspread
from gspread_formatting import CellFormat, Color, format_cell_range
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
from dotenv import load_dotenv
import asyncio

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
intents.message_content = True
client = discord.Client(intents=intents)

# Marcos de promoção
PATENTES = {
    0: "Reservista",
    15: "Recruta",
    20: "Sd 2ª Cl",
    35: "Sd 1ª Cl",
    45: "Cabo",
    55: "Sgt 3ª Cl",
    65: "2º Sgt",
    80: "1º Sgt",
    100: "SubTenente",
    120: "Aluno-Oficial",
    145: "Aspirante a Oficial",
    160: "2º Ten",
    180: "1º Ten",
    250: "Capitão"
}

# Cores por patente
CORES_PATENTES = {
    "Capitão":        CellFormat(backgroundColor=Color(0.4549, 0.1059, 0.2784)),  # #741b47
    "2º Ten":         CellFormat(backgroundColor=Color(0.0431, 0.3255, 0.5804)),  # #0b5394
    "1º Ten":         CellFormat(backgroundColor=Color(0.0431, 0.3255, 0.5804)),  # #0b5394
    "Aluno-Oficial":  CellFormat(backgroundColor=Color(0.0667, 0.3333, 0.8)),     # #1155cc
    "Aspirante a Oficial": CellFormat(backgroundColor=Color(0.0667, 0.3333, 0.8)),# #1155cc
    "1º Sgt":         CellFormat(backgroundColor=Color(0.2196, 0.4627, 0.1137)),  # #38761d
    "2º Sgt":         CellFormat(backgroundColor=Color(0.2196, 0.4627, 0.1137)),  # #38761d
    "Sgt 3ª Cl":      CellFormat(backgroundColor=Color(0.2196, 0.4627, 0.1137)),  # #38761d
    "SubTenente":     CellFormat(backgroundColor=Color(0.2196, 0.4627, 0.1137)),  # #38761d
    "Sd 1ª Cl":       CellFormat(backgroundColor=Color(0.4157, 0.6588, 0.3098)),  # #6aa84f
    "Sd 2ª Cl":       CellFormat(backgroundColor=Color(0.4157, 0.6588, 0.3098)),  # #6aa84f
    "Cabo":           CellFormat(backgroundColor=Color(0.4157, 0.6588, 0.3098)),  # #6aa84f
    "Recruta":        CellFormat(backgroundColor=Color(0.5216, 0.1255, 0.0471)),  # #85200c
    "Reservista":     CellFormat(backgroundColor=Color(0.6, 0, 0))                # #990000
}

COR_PRETA = CellFormat(backgroundColor=Color(0, 0, 0))

# Determina a patente com base na presença
def patente_por_presenca(presencas):
    niveis = sorted(PATENTES.keys())
    for i in reversed(niveis):
        if presencas >= i:
            return PATENTES[i]
    return "Reservista"

async def atualizar_inatividade_periodicamente():
    while True:
        try:
            registros = await asyncio.to_thread(sheet.get_all_values)
            now = datetime.now(pytz.timezone(TIMEZONE)).date()
            for i, row in enumerate(registros[1:], start=2):
                if len(row) >= 5 and row[4]:
                    try:
                        penultima_data = datetime.strptime(row[4], '%d/%m/%Y').date()
                        dias_inativos = max(0, (now - penultima_data).days - 1)
                        await asyncio.to_thread(sheet.update_cell, i, 6, str(dias_inativos))
                    except Exception as e:
                        print(f'[ERRO] Linha {i}: {e}')
        except Exception as e:
            print(f'[ERRO GERAL - ATUALIZAÇÃO INATIVIDADE]: {e}')
        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f'[+] Bot conectado como {client.user}')
    client.loop.create_task(atualizar_inatividade_periodicamente())

@client.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return
    if message.channel.id != CHECKIN_CHANNEL_ID:
        return
    if message.content.strip().lower() != '!presença':
        return

    discord_nick = message.author.display_name
    discord_id   = str(message.author.id)
    now = datetime.now(pytz.timezone(TIMEZONE))
    data_hoje = now.strftime('%d/%m/%Y')
    registros = await asyncio.to_thread(sheet.get_all_values)
    linha_found = None

    for i, row in enumerate(registros, start=1):
        if len(row) >= 2 and row[1] == discord_id:
            linha_found = i
            if len(row) >= 3 and row[2] == data_hoje:
                await message.reply('⚠️ Você já registrou sua presença hoje combatente.')
                return
            break

    try:
        if linha_found:
            linha = registros[linha_found - 1]
            total = int(linha[3]) if len(linha) >= 4 and linha[3].isdigit() else 0
            ultima_data = linha[2] if len(linha) >= 3 else ''
            penultima_data = linha[4] if len(linha) >= 5 else ''
            curso_cib = linha[7].strip().upper() if len(linha) >= 8 else 'NÃO'
            curso_cfo = linha[8].strip().upper() if len(linha) >= 9 else 'NÃO'

            bloquear = False
            mensagem = None

            if (total == 54 and curso_cib != 'SIM') or (total >= 55 and curso_cib != 'SIM' and total < 120):
                mensagem = '🛑 Você atingiu 55 presenças, continue marcando presença, mas para subir de cargo conclua o ESA.'
                bloquear = True
            elif (total == 119 and curso_cfo != 'SIM') or (total >= 120 and curso_cfo != 'SIM'):
                mensagem = '🛑 Você atingiu 120 presenças, continue marcando presença, mas para subir de cargo conclua o CFO.'
                bloquear = True

            await asyncio.to_thread(sheet.update_cell, linha_found, 5, ultima_data)
            await asyncio.to_thread(sheet.update_cell, linha_found, 3, data_hoje)

            if penultima_data:
                data_penultima = datetime.strptime(penultima_data, '%d/%m/%Y').date()
                dias_inativos = max(0, (now.date() - data_penultima).days - 1)
                await asyncio.to_thread(sheet.update_cell, linha_found, 6, str(dias_inativos))
            else:
                await asyncio.to_thread(sheet.update_cell, linha_found, 6, '0')

            if not bloquear:
                total += 1
                await asyncio.to_thread(sheet.update_cell, linha_found, 4, str(total))

                patente_sugerida = patente_por_presenca(total)
                patente_atual = patente_por_presenca(total - 2)

                if total in PATENTES:
                    await asyncio.to_thread(sheet.update_cell, linha_found, 10, patente_sugerida)
                    cor_patente = CORES_PATENTES.get(patente_sugerida, COR_PRETA)
                    await asyncio.to_thread(format_cell_range, sheet, f'J{linha_found}', cor_patente)
                    await asyncio.to_thread(format_cell_range, sheet, f'D{linha_found}', cor_patente)
                elif total - 2 in PATENTES:
                    await asyncio.to_thread(sheet.update_cell, linha_found, 10, '')
                    await asyncio.to_thread(format_cell_range, sheet, f'J{linha_found}', COR_PRETA)
                    await asyncio.to_thread(format_cell_range, sheet, f'D{linha_found}', COR_PRETA)

                await asyncio.to_thread(sheet.update_cell, linha_found, 11, patente_atual)
                await message.reply('✅ Presença registrada com sucesso!')
            else:
                await message.reply(mensagem)

        else:
            nova_linha = [discord_nick, discord_id, data_hoje, '1', '', '0']
            await asyncio.to_thread(sheet.append_row, nova_linha)
            linha_idx = len(registros) + 1
            await message.reply('✅ Presença registrada com sucesso!')

    except Exception as e:
        await message.reply(f'❌ Erro ao registrar presença: {e}')

if __name__ == '__main__':
    client.run(DISCORD_TOKEN)