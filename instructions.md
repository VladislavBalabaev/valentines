# 1. How to launch bot

## 1.1. You should create .env file in main directory and supply it with

```txt
TG_BOT_TOKEN = "_token_"  
MONGODB_USERNAME = "..."  
MONGODB_PASSWORD = "..."  
EMAIL1_PASSWORD = "..."  
EMAIL2_PASSWORD = "..."  
```

## 1.2. Run docker compose

First, start docker:

```sh
sudo systemctl start docker
```

Docker compose images and network between them:

```sh
docker compose build #--no-cache  
docker compose up --detach
```

## 1.3. Start the bot

Be sure that you are in directory of valentines.  

Enter new window:

```sh
tmux new -s valentines  
```

Enter running container of bot in interactive mode:

```sh
docker exec -it tg_bot bash  
python bot/start_bot.py
```

If the bot takes forever to launch:

1) check if your proxies are correct

```sh
env | grep -i proxy
```

2) check if you have access to telegram's API:

```sh
curl -I https://api.telegram.org  
ping api.telegram.org  
```

## 1.3.1 Screen commands

To detach from the screen session (without stopping the bot), press the following key combination:

```txt
Ctrl+A, then D  
```

Reattach to the running screen session:

```sh
tmux a -t valentines  
```

## 1.4. Finish work

To exit the container:

```sh
exit  
```

Then:

```sh
docker compose stop  
docker compose down  
```

## If you use VPN

In compose.yaml comment out network settings and bring back **network_mode: 'host'**.
