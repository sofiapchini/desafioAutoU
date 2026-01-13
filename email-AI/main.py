from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional
from pypdf import PdfReader

app = FastAPI()


@app.post("/analyze")
async def analyze_email(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    email_text = ""
    if text and text.strip():
        email_text = text.strip()

    elif file:
        filename = file.filename.lower()
        if filename.endswith(".txt"):
            content = await file.read()
            email_text = content.decode("utf-8")

        elif filename.endswith(".pdf"):
            reader = PdfReader(file.file)
            email_text = ""

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    email_text += page_text

        else:
            return {"error": "Formato de arquivo não suportado"}

    else:
        return {"error": "Envie um texto ou um arquivo"}

    if not email_text.strip():
        return {"error": "Não foi possível extrair texto do email"}
    texto = " ".join(email_text.lower().split())
    palavras_produtivas = [
    "status",
    "erro",
    "problema",
    "suporte",
    "ajuda",
    "acesso",
    "chamado"
]
    if any(p in texto for p in palavras_produtivas):
        categoria = "Produtivo"
        resposta = "Email produtivo detectado"
    else:
        categoria = "Improdutivo"
        resposta = "Email improdutivo detectado"

    return {
        "categoria": categoria,
        "resposta_sugerida": resposta,
        "preview": email_text[:300]
    }