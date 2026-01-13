from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pypdf import PdfReader

app = FastAPI()

templates = Jinja2Templates(directory="templates")


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

    if file:
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