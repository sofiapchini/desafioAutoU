from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pypdf import PdfReader
import os 
import requests
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

templates = Jinja2Templates(directory="templates")

client = OpenAI()

def classificar_email_com_ia(texto: str) -> dict:
    prompt = f"""
Você é um assistente que classifica emails.

Tarefa:
1. Classifique o email como Produtivo ou Improdutivo.
2. Sugira uma resposta curta e educada adequada à categoria.

Email:
{texto}

Responda EXATAMENTE no formato:
Categoria: <Produtivo ou Improdutivo>
Resposta: <texto>
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você classifica emails e sugere respostas automáticas."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=150
    )

    texto_saida = response.choices[0].message.content

    categoria = "Improdutivo"
    resposta = "Agradecemos sua mensagem."

    for line in texto_saida.splitlines():
        if "categoria" in line.lower() and "produtivo" in line.lower():
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

    try:
        resultado = classificar_email_com_ia(texto)
        categoria = resultado["categoria"]
        resposta = resultado["resposta"]

    except Exception as e:
        print("ERRO:", e)

        palavras_produtivas = [
            "status",
            "erro",
            "problema",
            "suporte",
            "ajuda",
            "acesso",
            "chamado",
        ]

        if any(p in texto.lower() for p in palavras_produtivas):
            categoria = "Produtivo"
            resposta = "Recebemos sua solicitação e em breve retornaremos."
        else:
            categoria = "Improdutivo"
            resposta = "Agradecemos sua mensagem."

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categoria": categoria,
            "resposta": resposta,
            "preview": email_text[:300],
        },
    )