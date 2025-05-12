
# 📚 Documentação Técnica do Sistema de Hotspot UniFi + Google Sheets

Este projeto permite o controle de acesso à rede Wi-Fi usando cadastro de usuários e vouchers integrados com Google Sheets, UniFi Controller e autenticação web com Flask.

---

## 🔐 Dados Sensíveis (configurações obrigatórias)

Os seguintes dados não devem ser incluídos diretamente no código. Armazene-os em um arquivo `.env` ou local seguro.

### ✅ Exemplo de `.env`:

```
PLANILHA_KEY=SUA_CHAVE_DA_PLANILHA
GOOGLE_CREDENTIALS_PATH=./credentials/credentials.json

UNIFI_USER=seu_email_unifi
UNIFI_PASS=sua_senha_unifi
UNIFI_IPS=https://ip1:8443,https://ip2:8443
UNIFI_SITE=site_id_unifi

EMAIL_HOST=smtp.seudominio.com
EMAIL_PORT=465
EMAIL_USER=seu_email@dominio.com
EMAIL_PASS=sua_senha_email
```

Adicione também no seu `.gitignore`:

```
.env
*.json
app.log
```

---

## 📁 credentials.json (modelo seguro)

Coloque em `./credentials/credentials.json`:

```json
{
  "type": "service_account",
  "project_id": "SEU_PROJECT_ID",
  "private_key_id": "SUA_PRIVATE_KEY_ID",
  "private_key": "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA\n-----END PRIVATE KEY-----\n",
  "client_email": "seu-email-de-servico@seu-projeto.iam.gserviceaccount.com",
  "client_id": "SEU_CLIENT_ID",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/seu-email-de-servico%40seu-projeto.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

---

## 🧠 Configuração no `app.py` com `python-dotenv`

Instale com:

```
pip install python-dotenv
```

Adicione ao início do seu `app.py`:

```python
from dotenv import load_dotenv
load_dotenv()

import os

PLANILHA_KEY = os.getenv("PLANILHA_KEY")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")
UNIFI_USER = os.getenv("UNIFI_USER")
UNIFI_PASS = os.getenv("UNIFI_PASS")
UNIFI_IPS = os.getenv("UNIFI_IPS").split(",")
SITE = os.getenv("UNIFI_SITE")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
```

---

## ✅ valiform.js — Validação de formulário no frontend

Salve como `static/js/valiform.js`:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    var form = document.querySelector('.login-form');

    if (!form) return;

    function validateForm(event) {
        event.preventDefault();

        var name = form.querySelector('#name')?.value.trim();
        var cpf = form.querySelector('#cpf')?.value.trim();
        var username = form.querySelector('#username')?.value.trim();
        var password = form.querySelector('#password')?.value.trim();
        var cellphone = form.querySelector('#cellphone')?.value.trim();
        var loja = form.querySelector('#loja')?.value;

        if (name && name.length < 3) {
            alert('Nome deve ter pelo menos 3 caracteres.');
            return false;
        }

        if (cpf && cpf.replace(/\D/g, '').length !== 11 && cpf !== '') {
            alert('CPF inválido. Deve conter 11 dígitos.');
            return false;
        }

        var emailPattern = /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/i;
        if (username && !emailPattern.test(username)) {
            alert('Email inválido.');
            return false;
        }

        if (password && password.length < 6) {
            alert('Senha deve ter pelo menos 6 caracteres.');
            return false;
        }

        if (cellphone && cellphone.length < 8) {
            alert('Telefone inválido.');
            return false;
        }

        form.submit();
    }

    form.addEventListener('submit', validateForm);
});
```

---

## 🧾 Resumo dos Campos Sensíveis

| Campo                  | Finalidade                        | Forma Segura de Configurar |
|------------------------|-----------------------------------|-----------------------------|
| `PLANILHA_KEY`         | Acesso à sua planilha             | `.env`                      |
| `GOOGLE_CREDENTIALS`   | Autenticação API Google Sheets    | `credentials.json`          |
| `UNIFI_USER/PASS/IPs`  | Login na controladora UniFi       | `.env`                      |
| `EMAIL_USER/PASS`      | Envio de e-mails (senha nova)     | `.env`                      |

---

## 🚀 Considerações Finais

- Este sistema é ideal para eventos, redes públicas ou igrejas.
- Todo o fluxo é integrado entre formulário → planilha → controle de acesso UniFi.
- A segurança é garantida desde que você mantenha as credenciais fora do código-fonte público.


---

## 🛠️ Tutorial Rápido: Configurar Google Sheets API

### 1. Criar Projeto no Google Cloud

1. Acesse: https://console.cloud.google.com/
2. Clique em **Selecionar projeto** > **Novo Projeto**
3. Dê um nome (ex: `Hotspot-Wifi`) e clique em **Criar**

---

### 2. Ativar a API do Google Sheets

1. Com o projeto selecionado, vá para: https://console.cloud.google.com/apis/library
2. Pesquise por **Google Sheets API**
3. Clique nela e ative.

Repita o processo para:
- **Google Drive API**

---

### 3. Criar credencial de conta de serviço

1. Vá para: https://console.cloud.google.com/apis/credentials
2. Clique em **Criar credenciais > Conta de serviço**
3. Dê um nome e continue até o fim
4. Após criada, vá em "Ações" (ícone de três pontinhos) > **Gerenciar chave**
5. Clique em **Adicionar chave > Criar nova chave > JSON**
6. Salve o arquivo `.json` gerado – este é o que você usa como `credentials.json`

---

### 4. Compartilhar a planilha com a conta de serviço

1. Abra sua planilha do Google Sheets
2. Clique em **Compartilhar**
3. Copie o campo `"client_email"` de dentro do seu `credentials.json`
4. Cole esse e-mail no compartilhamento da planilha com permissão de **editor**

---

✅ Pronto! Agora seu código poderá ler e escrever nessa planilha usando a API do Google Sheets com segurança.
