from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pypdf import PdfReader
import os 
import requests

from dotenv import load_dotenv
load_dotenv()


app = FastAPI()

templates = Jinja2Templates(directory="templates")


HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = "google/flan-t5-large"

def classificar_email_com_ia(texto: str) -> dict:
    prompt = f"""
Classifique o email abaixo como Produtivo ou Improdutivo.
Depois, sugira uma resposta curta e educada.

Email:
{texto}

Responda no formato:
Categoria: <Produtivo ou Improdutivo>
Resposta: <texto>
"""

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 0.2
        }
    }

    response = requests.post(
        f"https://api-inference.huggingface.co/models/{HF_MODEL}",
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    output = response.json()

    texto_saida = output[0]["generated_text"]

    categoria = "Improdutivo"
    resposta = "Agradecemos sua mensagem."

    for line in texto_saida.splitlines():
        if "categoria" in line.lower():
            if "produtivo" in line.lower():
                categoria = "Produtivo"
        if "resposta" in line.lower():
            resposta = line.split(":", 1)[-1].strip()

    return {
        "categoria": categoria,
        "resposta": resposta
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze_email(
    request: Request,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    email_text = ""

    if file and file.filename:
        filename = file.filename.lower()

        if filename.endswith(".txt"):
            content = await file.read()
            email_text = content.decode("utf-8")

        elif filename.endswith(".pdf"):
            reader = PdfReader(file.file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    email_text += page_text
        else:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "error": "Formato não suportado"}
            )

    elif text and text.strip():
        email_text = text.strip()

    else:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Envie texto ou arquivo"}
        )

    if not email_text.strip():
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Não foi possível extrair texto"}
        )

    texto = " ".join(email_text.lower().split())

    palavras_produtivas = [
        "status", "erro", "problema", "suporte",
        "ajuda", "acesso", "chamado"
    ]

    if any(p in texto for p in palavras_produtivas):
        categoria = "Produtivo"
        resposta = "Email produtivo detectado"
    else:
        categoria = "Improdutivo"
        resposta = "Email improdutivo detectado"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categoria": categoria,
            "resposta": resposta,
            "preview": email_text[:300]
        }
    )