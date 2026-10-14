import paramiko

def update_proxy():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('zeepubs.com', port=5004, username='zeepubs', key_filename=r'C:\Users\charl\.ssh\id_ed25519')
    
    nginx_conf = """# ------------------------------------------------------------
# dl.zeepubs.com
# ------------------------------------------------------------

map $scheme $hsts_header {
    https   "max-age=63072000; preload";
}

server {
  set $forward_scheme http;
  set $server         "zeepubs_bot_v6";
  set $port           8001;

  listen 80;
  listen 443 ssl;

  server_name dl.zeepubs.com;
  http2 on;

  include conf.d/include/letsencrypt-acme-challenge.conf;
  include conf.d/include/ssl-cache.conf;
  include conf.d/include/ssl-ciphers.conf;
  ssl_certificate /etc/letsencrypt/live/npm-8/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/npm-8/privkey.pem;

  include conf.d/include/assets.conf;
  include conf.d/include/block-exploits.conf;

  set $trust_forwarded_proto "F";
  include conf.d/include/force-ssl.conf;

  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection $http_connection;
  proxy_http_version 1.1;

  access_log /data/logs/proxy-host-7_access.log proxy;
  error_log /data/logs/proxy-host-7_error.log warn;

  location /api/ {
    proxy_pass http://172.18.0.1:8001/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /dl/ {
    proxy_pass http://172.18.0.1:8001/api/dl/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location ~ ^/([A-Za-z0-9_\\-]+)$ {
    proxy_pass http://172.18.0.1:8001/api/dl/$1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location / {
    default_type text/plain;
    return 404 "Zeepub Direct Downloads";
  }

  include /data/nginx/custom/server_proxy[.]conf;
}
"""

    stdin, stdout, stderr = ssh.exec_command('docker exec -i proxy sh -c "cat > /data/nginx/proxy_host/7.conf"')
    stdin.write(nginx_conf)
    stdin.channel.shutdown_write()
    print("Write exit status:", stdout.channel.recv_exit_status())

    stdin, stdout, stderr = ssh.exec_command('docker exec proxy nginx -t')
    print("nginx -t stdout:", stdout.read().decode())
    print("nginx -t stderr:", stderr.read().decode())

    stdin, stdout, stderr = ssh.exec_command('docker exec proxy nginx -s reload')
    print("nginx reload:", stdout.read().decode())
    
    ssh.close()

if __name__ == '__main__':
    update_proxy()
