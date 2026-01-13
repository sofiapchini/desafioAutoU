from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

class EmailInput(BaseModel):
    text: str 

@app.post("/analyze")
def analisar_email(data: EmailInput):
    texto =- data.text.lower()

    if any(p in texto for p in ["suporte", "ajuda", "erro", "problema"]):
        categoria = "Produtivo"
        resp = ("Olá, recebemos sua solicitação e estamos trabalhando para resolvê-la.")
    categoria = "Improdutivo"
    resp = "Olá, recebemos a sua mensagem. Estamos à disposição caso precise de algo"

    return {
        "categoria": categoria,
        "resposta": resp
    }
