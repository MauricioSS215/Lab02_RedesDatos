class HTTPErrorHandler:
    """
    Clase dedicada para el manejo de errores HTTP en el servidor
    """
    
    @staticmethod
    def bad_request(conn, message="Solicitud mal formada"):
        """400 Bad Request"""
        body = message
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
        return "400 Bad Request"

    @staticmethod
    def not_found(conn, filename):
        """404 Not Found"""
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
        return f"404 Not Found - Archivo {filename} no existe"

    @staticmethod
    def method_not_implemented(conn, method):
        """501 Not Implemented"""
        body = f"Metodo no implementado: {method} (solo GET esta soportado)."
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
        return f"501 Not Implemented - Metodo {method} no soportado"

    @staticmethod
    def http_version_not_supported(conn, version):
        """505 HTTP Version Not Supported"""
        body = f"Version HTTP no soportada: {version}"
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
        return f"505 HTTP Version Not Supported - Version {version}"

    @staticmethod
    def internal_server_error(conn, error_message):
        """500 Internal Server Error"""
        body = f"Error interno del servidor: {error_message}"
        response = (
            "HTTP/1.1 500 Internal Server Error\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body.encode())}\r\n"
            "Connection: close\r\n"
            "\r\n"
            f"{body}"
        )
        conn.sendall(response.encode())
        conn.close()
        return f"500 Internal Server Error - {error_message}"

    @staticmethod
    def success_response(conn, content_type, body_bytes):
        """200 OK - Respuesta exitosa"""
        header = (
            "HTTP/1.1 200 OK\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            "Connection: keep-alive\r\n"
            "\r\n"
        )
        conn.sendall(header.encode() + body_bytes)
        return "200 OK"