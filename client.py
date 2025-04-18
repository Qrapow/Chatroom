# Author: QinShenYu
# This code base has been modified using AI assistance.
import socket
import threading
import sys
from datetime import datetime

class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.running = True
        self.lock = threading.Lock()

    def setup_username(self):
        self.username = input("请输入用户名: ").strip()
        while not self.username:
            print("用户名不能为空！")
            self.username = input("请输入用户名: ").strip()
        try:
            self.sock.send(self.username.encode())
        except Exception as e:
            print(f"用户名设置失败: {str(e)}")
            sys.exit(1)

    def connect_to_server(self, host, port):
        try:
            self.sock.connect((host, port))
            self.setup_username()
            self.start_receiver()
            self.print_welcome()
            self.send_loop()
        except Exception as e:
            print(f"\n[System] 连接错误: {str(e)}", flush=True)
            sys.exit(1)

    def print_welcome(self):
        print("\n" + "="*40)
        print(f"You Joined: [{self.username}]")
        print("输入消息开始聊天（输入/q退出）")
        print("="*40 + "\n", flush=True)

    def start_receiver(self):
        def receive_handler():
            while self.running:
                try:
                    data = self.sock.recv(1024).decode()
                    if not data:
                        self.safe_print("\n[System] 连接已中断")
                        self.shutdown()
                        return
                    
                    # 添加消息时间戳
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.safe_print(f"\n[{timestamp}] {data}")
                except Exception as e:
                    self.safe_print(f"\n[Error] 接收失败: {str(e)}")
                    self.shutdown()
                    return
        threading.Thread(target=receive_handler, daemon=True).start()

    def safe_print(self, text):
        with self.lock:
            print(text, flush=True)
            sys.stdout.write("Type Message Here: ")  # 保持输入提示可见
            sys.stdout.flush()

    def send_loop(self):
        try:
            while self.running:
                try:
                    msg = input("Type Message Here:").strip()
                    if not msg:
                        continue
                    if msg == '/q':
                        self.shutdown()
                        return
                    
                    # 添加发送重试机制
                    for attempt in range(3):
                        try:
                            self.sock.send(msg.encode())
                            break
                        except Exception as e:
                            if attempt == 2:
                                raise
                            self.safe_print(f"\n[错误] 发送失败，正在重试({attempt+1}/3)...")
                except Exception as e:
                    self.safe_print(f"\n[严重错误] 消息发送失败: {str(e)}")
                    self.shutdown()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        print("\n连接已关闭")
        sys.exit(0)
def start_client():
    choice = input("创建房间(C) 还是加入房间(J)? ").upper()

    if choice == 'C':
        from server import ChatServer
        port = int(input("输入端口号 (5126): ") or 5126)
        server = ChatServer(port)
        server.load_config()
        print(f"服务端在端口 {port} 启动...")
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        host = '127.0.0.1'
    else:
        host = input("输入服务器地址: ")
        port = int(input("输入端口号: ") or 5126)

    client = ChatClient()
    client.connect_to_server(host, port)
if __name__ == "__main__":
    start_client()