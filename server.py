import socket
import os
import threading

HOST = "0.0.0.0"
PORT = 8080

# Carpeta donde estarán los archivos a servir
BASE_DIR = "files"

def manejar_cliente(conn, addr):
    print(f"[+] Conexión aceptada desde: {addr}")

    try:
        # Leer request HTTP (solo los primeros 1024 bytes para este lab)
        request = conn.recv(1024).decode(errors="ignore")

        if not request:
            conn.close()
            return

        print("===== REQUEST =====")
        print(request)
        print("===================\n")

        # Primera línea: "GET /index.html HTTP/1.1"
        first_line = request.splitlines()[0]
        parts = first_line.split()

        # Validación básica de formato
        if len(parts) < 3:
            body = "Solicitud mal formada"
            response = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(body.encode())}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{body}"
            )
            conn.sendall(response.encode())
            conn.close()
            return

        method, uri, version = parts[0], parts[1], parts[2]

        # 1) Método distinto de GET → 501
        if method != "GET":
            body = "Método no implementado (solo GET está soportado)."
            response = (
                "HTTP/1.1 501 Not Implemented\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(body.encode())}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{body}"
            )
            conn.sendall(response.encode())
            conn.close()
            return

        # 2) Versión HTTP no soportada → 505
        if version not in ["HTTP/1.0", "HTTP/1.1"]:
            body = "Versión HTTP no soportada."
            response = (
                "HTTP/1.1 505 HTTP Version Not Supported\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(body.encode())}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{body}"
            )
            conn.sendall(response.encode())
            conn.close()
            return

        # 3) Resolver el nombre del archivo pedido
        #    Si piden "/" devolvemos "index.html"
        if uri == "/":
            filename = "index.html"
        else:
            # Quita el "/" inicial: "/prueba.txt" → "prueba.txt"
            filename = uri.lstrip("/")

        filepath = os.path.join(BASE_DIR, filename)

        # 4) Si el archivo no existe → 404
        if not os.path.exists(filepath):
            body = f"Recurso no encontrado: {filename}"
            response = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(body.encode())}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{body}"
            )
            conn.sendall(response.encode())
            conn.close()
            return

        # 5) Determinar Content-Type según extensión
        if filename.endswith(".html"):
            content_type = "text/html; charset=utf-8"
        elif filename.endswith(".txt"):
            content_type = "text/plain; charset=utf-8"
        elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
            content_type = "image/jpeg"
        elif filename.endswith(".png"):
            content_type = "image/png"
        else:
            content_type = "application/octet-stream"

        # 6) Leer el archivo en binario
        with open(filepath, "rb") as f:
            body_bytes = f.read()

        # 7) Construir cabecera 200 OK
        header = (
            "HTTP/1.1 200 OK\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )

        # 8) Enviar cabecera + cuerpo
        conn.sendall(header.encode() + body_bytes)

    except Exception as e:
        print("Error al manejar la solicitud:", e)

    finally:
        conn.close()
        print(f"[-] Conexión cerrada con: {addr}\n")


def main():
    # Crear socket del servidor
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Servidor HTTP MULTIHILO escuchando en {HOST}:{PORT}...")
    print(f"Sirviendo archivos desde la carpeta: {BASE_DIR}")

    # Bucle principal: ahora sí, con hilos
    while True:
        print("Esperando conexión...")
        conn, addr = server.accept()

        # Crear un hilo para este cliente
        thread = threading.Thread(target=manejar_cliente, args=(conn, addr))
        thread.start()
        print(f"[THREAD] Hilo iniciado para {addr}")


if __name__ == "__main__":
    main()
