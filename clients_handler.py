import threading
import time
import json

class ClientsHandler:
    """
    Clase para gestionar todas las conexiones de clientes del servidor
    """
    
    def __init__(self):
        self.clients = {}  # {client_id: {'conn': socket, 'addr': address, 'name': str, 'connected': bool}}
        self.client_counter = 0
        self.lock = threading.Lock()
    
    def add_client(self, conn, addr):
        """Agrega un nuevo cliente al handler"""
        with self.lock:
            self.client_counter += 1
            client_id = self.client_counter
            client_name = f"Cliente-{client_id}"
            
            self.clients[client_id] = {
                'conn': conn,
                'addr': addr,
                'name': client_name,
                'connected': True,
                'request_count': 0,
                'last_activity': time.time()
            }
            
            print(f"[{client_name}] CONEXION AGREGADA al handler")
            return client_id, client_name
    
    def update_client_activity(self, client_id):
        """Actualiza la última actividad del cliente"""
        with self.lock:
            if client_id in self.clients:
                self.clients[client_id]['last_activity'] = time.time()
                self.clients[client_id]['request_count'] += 1
    
    def get_client_info(self, client_id):
        """Obtiene información de un cliente específico"""
        with self.lock:
            if client_id in self.clients:
                return self.clients[client_id].copy()
            return None
    
    def get_all_clients(self):
        """Obtiene información de todos los clientes"""
        with self.lock:
            return {cid: info.copy() for cid, info in self.clients.items()}
    
    def get_connected_clients(self):
        """Obtiene solo los clientes conectados"""
        with self.lock:
            connected = {cid: info for cid, info in self.clients.items() if info['connected']}
            return connected
    
    def disconnect_client(self, client_id):
        """Desconecta un cliente específico"""
        with self.lock:
            if client_id in self.clients and self.clients[client_id]['connected']:
                client_info = self.clients[client_id]
                try:
                    client_info['conn'].close()
                    client_info['connected'] = False
                    print(f"[{client_info['name']}] Desconectado por el handler")
                    return True
                except:
                    return False
        return False
    
    def disconnect_all_clients(self):
        """Desconecta todos los clientes conectados"""
        with self.lock:
            disconnected_count = 0
            clients_to_disconnect = []
            
            # Primero recolectar los clientes a desconectar
            for client_id, client_info in self.clients.items():
                if client_info['connected']:
                    clients_to_disconnect.append(client_id)
            
            # Luego desconectarlos
            for client_id in clients_to_disconnect:
                if self.disconnect_client(client_id):
                    disconnected_count += 1
            
            print(f"[CLIENTS_HANDLER] Desconectados {disconnected_count} clientes")
            return disconnected_count
    
    def broadcast_message(self, message):
        """Envía un mensaje a todos los clientes conectados"""
        with self.lock:
            sent_count = 0
            for client_id, client_info in self.clients.items():
                if client_info['connected']:
                    try:
                        # Formato de mensaje de broadcast
                        broadcast_msg = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(message)}\r\n\r\n{message}"
                        client_info['conn'].sendall(broadcast_msg.encode())
                        sent_count += 1
                    except:
                        client_info['connected'] = False
            return sent_count
    
    def get_stats(self):
        """Obtiene estadísticas de los clientes"""
        with self.lock:
            total_clients = len(self.clients)
            connected_clients = len([c for c in self.clients.values() if c['connected']])
            total_requests = sum(client['request_count'] for client in self.clients.values())
            
            stats = {
                'total_clients': total_clients,
                'connected_clients': connected_clients,
                'disconnected_clients': total_clients - connected_clients,
                'total_requests': total_requests,
                'clients_info': []
            }
            
            for client_id, client_info in self.clients.items():
                stats['clients_info'].append({
                    'client_id': client_id,
                    'name': client_info['name'],
                    'address': f"{client_info['addr'][0]}:{client_info['addr'][1]}",
                    'connected': client_info['connected'],
                    'request_count': client_info['request_count'],
                    'last_activity': time.strftime('%H:%M:%S', time.localtime(client_info['last_activity']))
                })
            
            return stats
    
    def print_stats(self):
        """Imprime estadísticas de los clientes"""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("ESTADISTICAS DE CLIENTES")
        print("=" * 60)
        print(f"Clientes totales: {stats['total_clients']}")
        print(f"Clientes conectados: {stats['connected_clients']}")
        print(f"Clientes desconectados: {stats['disconnected_clients']}")
        print(f"Total de requests: {stats['total_requests']}")
        print("\nClientes detallados:")
        
        for client_info in stats['clients_info']:
            status = "CONECTADO" if client_info['connected'] else "DESCONECTADO"
            print(f"  {client_info['name']} ({client_info['address']}) - {status}")
            print(f"    Requests: {client_info['request_count']}, Ultima actividad: {client_info['last_activity']}")
        
        print("=" * 60)