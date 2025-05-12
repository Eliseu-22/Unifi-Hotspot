import logging
import sys
import os
from flask import Flask, render_template, request, redirect, session, send_from_directory
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import urllib3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'SUA_CHAVE_SECRETA_AQUI'

# ================== CONFIGURAÇÕES DO GOOGLE SHEETS ==================
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

if getattr(sys, 'frozen', False):
    json_path = os.path.join(sys._MEIPASS, 'SEU_ARQUIVO_CREDENCIAL.json')
else:
    json_path = os.path.join('caminho', 'para', 'SEU_ARQUIVO_CREDENCIAL.json')

logger.info(f"Carregando credenciais do arquivo JSON: {json_path}")

creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
client = gspread.authorize(creds)

PLANILHA_KEY = 'SUA_PLANILHA_KEY_AQUI'
sheet = client.open_by_key(PLANILHA_KEY).worksheet('creds')

# ============= UNIFI =============
UNIFI_USER = 'SEU_EMAIL_UNIFI'
UNIFI_PASS = 'SUA_SENHA_UNIFI'
unifi_ips = [
    "https://IP_DO_UNIFI_1:PORTA",
    "https://IP_DO_UNIFI_2:PORTA",
    "https://IP_DO_UNIFI_3:PORTA"
]
SITE = 'ID_DO_SITE'

# ============= SMTP para "forgot" =============
EMAIL_HOST = "smtp.seudominio.com"
EMAIL_PORT = 465
EMAIL_USER = "seu_email@seudominio.com"
EMAIL_PASS = "sua_senha_email"

def send_email(to_address, subject, body):
    logger.info(f"Enviando email para {to_address} - Assunto: {subject}")
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        logger.info("Email enviado com sucesso!")
    except Exception:
        logger.exception("Falha ao enviar o email")

def authorize_mac(mac):
    logger.info(f"Autorizando MAC: {mac} no UNIFI (por 60 minutos).")
    session_req = requests.Session()
    session_req.verify = False

    for ip in unifi_ips:
        try:
            logger.info(f"Tentando autenticar no UniFi Controller: {ip}")
            login_resp = session_req.post(f'{ip}/api/login', json={
                'username': UNIFI_USER,
                'password': UNIFI_PASS
            })
            if login_resp.status_code == 200:
                logger.info("Login bem-sucedido!")
                auth_resp = session_req.post(f'{ip}/api/s/{SITE}/cmd/stamgr', json={
                    'cmd': 'authorize-guest',
                    'mac': mac,
                    'minutes': 60
                })
                if auth_resp.status_code == 200:
                    logger.info(f"MAC {mac} autorizado com sucesso em {ip}!")
                    return
                else:
                    logger.warning(f"Falha ao autorizar MAC em {ip}")
        except Exception:
            logger.exception(f"Erro ao autenticar em {ip}")

    logger.error("Não foi possível autenticar/autorizar em nenhum dos IPs disponíveis.")

def gerar_senha(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def update_mac_and_ap(username, dispositivo_mac, ap_mac):
    registros = sheet.get_all_records()
    for i, registro in enumerate(registros):
        if str(registro['username']).strip().lower() == username.strip().lower():
            sheet.update_cell(i+2, 2, ap_mac)
            sheet.update_cell(i+2, 7, dispositivo_mac)
            break

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.static_folder), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def rota_principal():
    try:
        mac = request.args.get('id', '')
        ap = request.args.get('ap', '')
        url = request.args.get('url', '')
        return render_template('index.html', mac=mac, ap=ap, url=url)
    except Exception:
        logger.exception("Erro na rota /")
        return "<script>alert('Erro!'); window.history.back();</script>", 500

@app.route('/guest/s/<site>/')
def rota_site(site):
    try:
        mac = request.args.get('id', '')
        ap = request.args.get('ap', '')
        url = request.args.get('url', '')
        return render_template('index.html', mac=mac, ap=ap, url=url)
    except Exception:
        logger.exception("Erro na rota dinâmica")
        return "<script>alert('Erro!'); window.history.back();</script>", 500

@app.route('/auth', methods=['POST'])
def auth():
    try:
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        dispositivo_mac = request.form.get('id', '')
        ap_mac = request.form.get('ap', '')
        redirect_url = request.form.get('url', '')

        registros = sheet.get_all_records()
        for i, registro in enumerate(registros):
            if str(registro['username']).strip().lower() == username:
                if str(registro['password']).strip() == password:
                    authorize_mac(dispositivo_mac)
                    update_mac_and_ap(username, dispositivo_mac, ap_mac)
                    sheet.update_cell(i+2, 11, f"{datetime.datetime.now():%d/%m/%Y %H:%M:%S}")
                    return """
<html><head><script>
let countdown = 10;
function startCountdown() {
  var display = document.getElementById('countdown');
  var timer = setInterval(function(){
    countdown--;
    display.textContent = countdown;
    if(countdown <= 0){
      clearInterval(timer);
      alert("Sua conexão foi liberada com sucesso!");
      window.location.href = "http://clients3.google.com/generate_204";
    }
  }, 1000);
}
</script></head><body onload="startCountdown()" style="background:#000;color:#fff;text-align:center">
<h1>Login efetuado com sucesso!</h1>
<p>Por favor aguarde <span id="countdown">10</span> segundo(s)...</p>
</body></html>"""
                else:
                    return '<script>alert("Senha incorreta!"); window.history.back();</script>'
        return '<script>alert("Usuário não encontrado!"); window.history.back();</script>'
    except Exception:
        logger.exception("Erro na rota /auth")
        return "<script>alert('Erro durante a autenticação!'); window.history.back();</script>", 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '')
            cpf = request.form.get('cpf', '')
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '').strip()
            cellphone = request.form.get('cellphone', '')
            loja = request.form.get('loja', '')
            data_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            registros = sheet.get_all_records()
            for registro in registros:
                if str(registro['cpf']).strip() == cpf and cpf:
                    return '''<script>
                        if(confirm("CPF já cadastrado. Deseja redefinir a senha?")) {
                            window.location.href="/forgot";
                        } else {
                            window.history.back();
                        }
                    </script>'''

            for registro in registros:
                if str(registro['username']).strip().lower() == username:
                    return '<script>alert("Usuário já existe!"); window.history.back();</script>'

            sheet.append_row(['', '', cellphone, cpf, data_now, loja, '', name, password, username, ''])
            return render_template('registered.html')
        except Exception:
            logger.exception("Erro no cadastro")
            return "<script>alert('Erro ao cadastrar!'); window.history.back();</script>", 500
    else:
        return render_template('register.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            registros = sheet.get_all_records()
            for i, registro in enumerate(registros):
                if str(registro['username']).strip().lower() == email:
                    nova_senha = gerar_senha(8)
                    sheet.update_cell(i+2, 9, nova_senha)
                    send_email(email, "Redefinição de senha", f"Sua nova senha é: {nova_senha}")
                    return "<script>alert('Nova senha enviada!'); window.location.href='/';</script>"
            return '<script>alert("E-mail não encontrado!"); window.history.back();</script>'
        except Exception:
            logger.exception("Erro na redefinição de senha")
            return "<script>alert('Erro ao redefinir senha!'); window.history.back();</script>", 500
    return render_template('forgot.html')

@app.route('/voucher_auth', methods=['POST'])
def voucher_auth():
    try:
        voucher_code = request.form.get('voucher_code', '').strip().upper()
        mac = request.form.get('id', '')
        ap = request.form.get('ap', '')
        url = request.form.get('url', '')
        voucher_sheet = client.open_by_key(PLANILHA_KEY).worksheet('vouchers')
        vouchers_list = voucher_sheet.get_all_records()

        found, found_index = None, None
        for i, row in enumerate(vouchers_list):
            if str(row.get('voucher_code', '')).strip().upper() == voucher_code:
                found = row
                found_index = i + 2
                break
        if not found:
            return "<script>alert('Voucher inválido!'); window.history.back();</script>"

        usage_count = int(str(found.get('usage_count', '0')).strip() or 0)
        create_time_str = str(found.get('create_time', '')).strip()

        if not create_time_str:
            create_time = datetime.datetime.now()
            voucher_sheet.update_cell(found_index, 2, create_time.strftime("%d/%m/%Y %H:%M:%S"))
        else:
            create_time = datetime.datetime.strptime(create_time_str, "%d/%m/%Y %H:%M:%S")
        
        if (datetime.datetime.now() - create_time).total_seconds() > 3600:
            return "<script>alert('Voucher expirado.'); window.history.back();</script>"
        if usage_count >= 10:
            return "<script>alert('Limite de uso atingido.'); window.history.back();</script>"

        voucher_sheet.update_cell(found_index, 3, str(usage_count + 1))
        authorize_mac(mac)

        return """
<html><head><script>
let countdown = 10;
function startCountdown() {
  var display = document.getElementById('countdown');
  var timer = setInterval(function(){
    countdown--;
    display.textContent = countdown;
    if(countdown <= 0){
      clearInterval(timer);
      alert("Sua conexão foi liberada com sucesso!");
      window.location.href = "http://clients3.google.com/generate_204";
    }
  }, 1000);
}
</script></head><body onload="startCountdown()" style="background:#000;color:#fff;text-align:center">
<h1>Voucher válido!</h1>
<p>Aguarde <span id="countdown">10</span> segundo(s)...</p>
</body></html>
"""
    except Exception:
        logger.exception("Erro na autenticação via voucher")
        return "<script>alert('Erro ao validar voucher!'); window.history.back();</script>", 500

@app.errorhandler(Exception)
def handle_all_exceptions(e):
    logger.exception("Exceção global")
    return "<script>alert('Erro inesperado!'); window.history.back();</script>", 500

if __name__ == '__main__':
    logger.info("Iniciando aplicação Flask na porta 80...")
    app.run(host='0.0.0.0', port=80, debug=True)
