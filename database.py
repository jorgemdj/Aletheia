import duckdb
import os

DB_PATH = "diario_vibe.db"

def get_connection():
    return duckdb.connect(DB_PATH)

def init_db():
    conn = get_connection()
    # Criando a tabela com suporte a métricas opcionais e tipos complexos
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entradas (
            id INTEGER PRIMARY KEY,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            texto_original TEXT,
            resposta_ia TEXT,
            peso FLOAT,
            agua_ml INTEGER,
            horas_sono FLOAT,
            treino_realizado BOOLEAN,
            sentimento_score INTEGER,
            clima_sentimento VARCHAR,
            vicios_controle JSON,
            status_comprometimento VARCHAR,
            tags VARCHAR[]
        );
        CREATE SEQUENCE IF NOT EXISTS seq_id START 1;
    """)
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Banco de dados inicializado com sucesso.")