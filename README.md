# viberMongoBot
simple viber bot built with viber python api + mongo-flask-gunicorn-nginx

(assuming Ubuntu 18.04 Env)

- install mongoDb: 

```
 wget -qO - https://www.mongodb.org/static/pgp/server-4.2.asc | sudo apt-key add -
 echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/4.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.2.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo service mongod start
sudo systemctl enable mongod.service

```

- install ngninx:

```
sudo apt update
sudo apt install nginx

```

- install python3 components:

```
sudo apt update
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools

```

- set up a virtual environment in order to isolate our Flask application from the other Python files on the system:

```
sudo apt install python3-venv
mkdir ~/netviber
cd ~/netviber
python3.6 -m venv netviberenv
source netviberenv/bin/activate
pip install wheel
pip install gunicorn flask
pip install pymongo
pip install viberbot

```

- then we create our flaskapp(flaskTest.py)

- allow firewall at port 5000:

```
sudo ufw allow 5000
```

- create wsgi file:

```

nano ~/netviber/wsgi.py

```

- file content:

```
from netviber import app

if __name__ == "__main__":
    app.run()
```    

- Bind gunicorn on port 5000:

```
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

- terminate virtual env

```
deactivate
```

- Let’s create the systemd service unit file:

```
sudo nano /etc/systemd/system/netviber.service
```

- file content:

```
[Unit]
Description=Gunicorn instance to serve netviber
After=network.target

[Service]
User=user1
Group=www-data
WorkingDirectory=/home/user1/netviber
Environment="PATH=/home/user1/netviber/netviberenv/bin"
ExecStart=/home/user1/netviber/netviberenv/bin/gunicorn --workers 3 --bind unix:netviber.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

- start and enable service

```
sudo systemctl start netviber
sudo systemctl enable netviber
```

- NGINX:

```
sudo nano /etc/nginx/sites-available/netviber
```

- Nginx sites-available content:

```
server {
    listen 80;
    server_name your.server.name

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/user1/netviber/netviber.sock;
    }
}

```

```
sudo ln -s /etc/nginx/sites-available/netviber /etc/nginx/sites-enabled
```

- check NGINX conf:

```
sudo nginx -t
```

- Restart nginx:

```
sudo systemctl restart nginx
```

- We no longer need access through port 5000, so we can remove that rule

```
sudo ufw delete allow 5000
```

- Allow full access to the Nginx server:

```
sudo ufw allow 'Nginx Full'
```

- Let's add SSL:

```
sudo add-apt-repository ppa:certbot/certbot
sudo apt install python-certbot-nginx
sudo certbot --nginx -d your_domain -d www.your_domain
```

- We no longer need the redundant HTTP NGINX profile allowance

```
sudo ufw delete allow 'Nginx HTTP'
```
- Visit https://your_domain
