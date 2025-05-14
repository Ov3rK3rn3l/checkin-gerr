# Windows

python -m venv venv

.\venv\Scripts\Activate

pip install -r requirements.txt

# Start command Windows:

python bot.py

# Linux

sudo npm install -g pm2

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt


# Start command Linux:
pm2 start venv/bin/python --name checkin -- -m bot.py

pm2 save

pm2 startup

# Criar BOT https://discord.com/developers/applications

Invitar o bot para o discord

https://discord.com/oauth2/authorize?client_id=ID-DO-BOT-AQUI&permissions=68608&scope=bot%20applications.commands

# Acessar o Google Console

Criar uma API para > Google Sheets API

Criar uma conta de Serviço em Credenciais

Gerar uma chave em formato JSON

Renomear o arquivo para credentials.json e colocar na raiz do projeto.

Renomear o arquivo .envexample pra .env e inserir suas credenciais.