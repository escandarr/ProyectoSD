import sqlite3
import random
import time
import numpy as np

DB_PATH = "eventos.db"
TABLE_NAME = "eventos"

# Configuración
MODO = "poisson"  # "uniforme" o "poisson"
UNIFORME_INTERVALO = 1  # segundos
POISSON_LAMBDA = 2  # promedio 2 eventos por segundo
MAX_CONSULTAS = 10000  # 💥 N° máximo de consultas

def obtener_evento_random():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY RANDOM() LIMIT 1;")
    evento = cursor.fetchone()
    conn.close()
    return evento

def main():
    print(f"🎯 Generador de tráfico iniciado en modo {MODO.upper()}")
    contador = 0

    while contador < MAX_CONSULTAS:
        evento = obtener_evento_random()
        print(f"🚦 [{contador+1}] Consulta evento: {evento}")

        # Aquí: se enviaría al sistema de cache, en el futuro

        if MODO == "uniforme":
            time.sleep(UNIFORME_INTERVALO)
        elif MODO == "poisson":
            intervalo = np.random.exponential(1 / POISSON_LAMBDA)
            time.sleep(intervalo)
        else:
            raise ValueError("Modo no válido. Usa 'uniforme' o 'poisson'.")

        contador += 1

    print(f"🎉 Generador de tráfico terminado después de {contador} consultas.")

if __name__ == "__main__":
    main()
