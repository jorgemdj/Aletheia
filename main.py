import os
from dotenv import load_dotenv
import json
import google.genai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_connection
from typing import List, Optional

app = FastAPI(title="Diário Vibe API")

load_dotenv()

# Configure sua API Key do Google aqui
client = genai.Client(api_key=os.getenv("API_KEY"))
MODEL_ID = "models/gemini-2.5-flash-lite"

class EntryRequest(BaseModel):
    texto: str

@app.post("/registrar")
async def registrar_entrada(request: EntryRequest):
    conn = get_connection()
    
    # 1. Contexto (Mantemos a lógica SQL)
    historico = conn.execute("""
        SELECT texto_original, resposta_ia, status_comprometimento 
        FROM entradas ORDER BY data DESC LIMIT 3
    """).fetchall()
    
    contexto_str = "\n".join([f"User: {h[0]}\nIA: {h[1]}" for h in historico])
    dias_ausente = sum(1 for h in historico if h[2] == 'ausente')

    prompt = f"""
    Aja como um Mentor Empático.
    Contexto recente: {contexto_str}
    
    Diretrizes:
    1. Extraia métricas em JSON: peso (float), agua (int ml), sono (float), treino (bool), vicios (dict), sentimento_score (1-10).
    2. Nudge: Se faltar peso, água ou sono, pergunte no texto.
    3. Indiferença: Se houver {dias_ausente} falhas, use status_comprometimento 'ausente' e seja firme.
    
    Retorne EXATAMENTE neste formato:
    ---JSON---
    {{ "metrics": {{...}}, "status": "completo|parcial|ausente", "tags": [...] }}
    ---TEXTO---
    Sua resposta aqui.
    """

    try:
        # Nova forma de gerar conteúdo
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"{prompt}\n\nRelato: {request.texto}"
        )
        
        parts = response.text.split("---TEXTO---")
        raw_json = parts[0].replace("---JSON---", "").strip()
        ia_text = parts[1].strip()
        data_json = json.loads(raw_json)

        # 3. Persistência (DuckDB)
        m = data_json['metrics']
        conn.execute("""
            INSERT INTO entradas (id, texto_original, resposta_ia, peso, agua_ml, horas_sono, 
                                 treino_realizado, sentimento_score, status_comprometimento, tags)
            VALUES (nextval('seq_id'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (request.texto, ia_text, m.get('peso'), m.get('agua'), m.get('sono'), 
              m.get('treino'), m.get('sentimento_score'), data_json['status'], data_json['tags']))
        
        return {"resposta": ia_text, "metrics": m}

    except Exception as e:
        # CORREÇÃO AQUI: status_code em vez de status_status
        raise HTTPException(status_code=500, detail=f"Erro na IA: {str(e)}")

# O endpoint /review-semanal também deve ser atualizado para usar client.models.generate_content

@app.get("/review-semanal")
async def review_semanal():
    conn = get_connection()
    stats = conn.execute("""
        SELECT 
            AVG(agua_ml) as avg_agua, 
            AVG(horas_sono) as avg_sono,
            COUNT(CASE WHEN treino_realizado THEN 1 END) as treinos
        FROM entradas 
        WHERE data >= now() - interval '7 days'
    """).fetchone()

    prompt_insight = f"Gere um insight motivador em Markdown para esses dados da semana: Água média {stats[0]}ml, Sono médio {stats[1]}h, Treinos: {stats[2]}."
    response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"{prompt_insight}"
        )
    
    return {"markdown": response.text}