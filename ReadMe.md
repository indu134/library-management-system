-first install requirement using below command

pip install -r requirements.txt


-then install redis  (refer https://redis.io/docs/install/install-redis/install-redis-on-linux/)

start redis server

-then install MailHog using below commands(if linux)

sudo apt install golang-go -y

go install github.com/mailhog/MailHog@latest

satrt it  using below command(if linux)

~/go/bin/MailHog


-then run application by below command

python3 app.py

