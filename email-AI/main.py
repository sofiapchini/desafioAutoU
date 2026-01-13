from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

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

        else:
            return {"error": "Formato de arquivo não suportado"}

    else:
        return {"error": "Envie um texto ou um arquivo"}
    texto = email_text.lower()

    if any(p in texto for p in ["status", "erro", "problema", "suporte", "ajuda"]):
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