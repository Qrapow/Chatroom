# Author: QinShenYu
# This code base has been modified using AI assistance.
import socket
import threading
import yaml
from datetime import datetime

class ChatServer:
    def __init__(self, port=5126):
        self.host = '0.0.0.0'
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.banned_ips = set()
        self.muted_users = set()
        self.lock = threading.Lock()

    def load_config(self):
        try:
            with open('config.yml') as f:
                config = yaml.safe_load(f)
                self.port = config.get('port', self.port)
                self.banned_ips = set(config.get('banned_ips', []))
                print(f"Loaded config: Port={self.port}, Banned IPs={self.banned_ips}")
        except FileNotFoundError:
            print('Using default configuration')

    def start(self):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                if addr[0] in self.banned_ips:
                    print(f"Blocked banned IP: {addr[0]}")
                    client_socket.close()
                    continue
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr)
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, addr):
        try:
            # 获取用户名（第一组数据必须是用户名）
            username = client_socket.recv(1024).decode().strip()
            if not username:
                raise ValueError("Empty username")
            
            # 检查用户名是否重复
            with self.lock:
                if username in self.clients.values():
                    client_socket.send("用户名已存在".encode())
                    client_socket.close()
                    return
                self.clients[client_socket] = username
            
            # 广播用户加入
            self.broadcast(f"[Server] {username} Joined.", exclude=client_socket)
            
            # 消息处理循环
            while True:
                try:
                    msg = client_socket.recv(1024).decode()
                    if not msg:
                        break  # 客户端正常断开
                    
                    # 处理命令（示例：/mute）
                    if msg.startswith('/'):
                        # 可扩展命令处理逻辑
                        pass
                    else:
                        # 添加时间戳广播
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        self.broadcast(f"[{timestamp}] {username}: {msg}")
                except ConnectionResetError:
                    break  # 客户端异常断开
        except Exception as e:
            print(f"[服务端错误] {addr} 连接异常: {str(e)}")
        finally:
            # 清理客户端资源
            with self.lock:
                if client_socket in self.clients:
                    left_user = self.clients[client_socket]
                    del self.clients[client_socket]
                    self.broadcast(f"[Server] {left_user} Exited.")
            client_socket.close()
    def broadcast(self, message, exclude=None):
        with self.lock:
            for client in list(self.clients.keys()):  # 转为列表避免字典改变大小异常
                try:
                    if client != exclude:
                        client.send(message.encode())
                except (ConnectionError, OSError):
                    # 自动清理无效连接
                    del self.clients[client]
                    client.close()
    def shutdown_server(self):
        print("\n正在关闭所有客户端连接...")
        with self.lock:
            for client in self.clients.keys():
                try:
                    client.send("SERVER_SHUTDOWN".encode())
                    client.close()
                except:
                    pass
        self.server_socket.close()
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5126)
    args = parser.parse_args()

    server = ChatServer(port=args.port)
    server.load_config()
    server.start()