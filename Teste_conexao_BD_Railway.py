import psycopg2

try:
    conn = psycopg2.connect(
        dbname="railway",
        user="postgres",
        password="novasenha123",
        host="autorack.proxy.rlwy.net",
        port="36680",
        sslmode="require"  # Teste também com "disable"
    )
    print("Conexão bem-sucedida!")
except Exception as e:
    print(f"Erro ao conectar: {e}")
