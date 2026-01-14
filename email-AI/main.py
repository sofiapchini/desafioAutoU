from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pypdf import PdfReader
from openai import OpenAI

#carrega variaveis de ambiente local para obfuscar a api key
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()

#configuração dos templates HTML
templates = Jinja2Templates(directory="templates")

client = OpenAI()

# prompt para classificação e geração de resposta (default: Improdutivo)
def classificar_email_com_ia(texto: str) -> dict:
    prompt = f"""
Você é um assistente responsável por TRIAGEM de emails de suporte.

Definições obrigatórias:
- Email PRODUTIVO: contém pedido de ajuda, problema, erro, dúvida, solicitação, reclamação ou algo que exija ação da equipe.
- Email IMPRODUTIVO: elogios, agradecimentos, mensagens genéricas, marketing, spam ou conteúdos que não exigem ação.

Classifique o email abaixo como Produtivo ou Improdutivo.
Depois, sugira uma resposta curta e educada adequada à categoria.

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
    
    #esses valores são um método de fallback, só são utilizados caso o prompt falhe
    categoria = "Improdutivo"
    resposta = "Agradecemos sua mensagem."

    #check pra categoria, foi a primeira ideia que eu tive (e que funcionou), mas acredito que possa ser melhorado
    for line in texto_saida.splitlines():
        line_lower = line.lower()
        if line_lower.startswith("categoria"):
            if "improdutivo" in line_lower:
                categoria = "Improdutivo"
            elif "produtivo" in line_lower:
                categoria = "Produtivo"

        if line_lower.startswith("resposta"):
            resposta = line.split(":", 1)[-1].strip()

    return {
        "categoria": categoria,
        "resposta": resposta
    }


#endpoint http get
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

#endpoint http post
@app.post("/analyze", response_class=HTMLResponse)
async def analyze_email(
    request: Request,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    email_text = ""

    #arquivos tem preferencia, caso o arquivo exista, é checado sua extensão e é salvo seu filename
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
        #caso o arquivo não tenha a extensão apropriada, um erro é retornado
        else:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "error": "Formato não suportado"}
            )
    #caso file ou filename seja None (arquivo não foi enviado), o programa checa se algum texto foi enviado.
    elif text and text.strip():
        email_text = text.strip()
        
    #caso até o texto não estiver sido enviado, uma mensagem de erro e instrução ao usuário é enviada
    else:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Envie texto ou arquivo"}
        )
    #se o texto não foi extraído com sucesso, então imprima mensagem de erro ao usuário
    if not email_text.strip():
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Não foi possível extrair texto"}
        )

    texto = " ".join(email_text.lower().split())

    # esse bloco try chama a funcao de IA, caso a função funcione, salva o seu diciontario resultante na variavel resultado
    try:
        resultado = classificar_email_com_ia(texto)
        categoria = resultado["categoria"]
        resposta = resultado["resposta"]

    #caso a função não execute é necessário parsar manualmente o texto e checar pelas keywords de emails produtivos
    except Exception as e:

        palavras_produtivas = [
            "status",
            "erro",
            "problema",
            "suporte",
            "ajuda",
            "acesso",
            "chamado",
        ]
        #parsing automatico de cada palavra presente no texto, caso alguma palavra for encontrada o email é classificado como "produtivo"
        if any(p in texto.lower() for p in palavras_produtivas):
            categoria = "Produtivo"
            resposta = "Recebemos sua solicitação e em breve retornaremos."
        else:
            categoria = "Improdutivo"
            resposta = "Agradecemos sua mensagem."

    #retorna pro frontend o resultado
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categoria": categoria,
            "resposta": resposta,
            "preview": email_text[:300],
        },
    )