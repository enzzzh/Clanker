# EnzzzClanker

## What is this 

A discord bot that can install youtube link, or even playlists

## How to install it 

#### It is a long and tedious process that even me writing this made me TIIIIIIIRED 

First, let's get the bot running 

navigate in [Discord admin page](https://discord.com/developers/applications) and create a new application 

Now when you enter the page of your bot you gonna navigate to the OAuth2 page and go donw to the URL generator 
 and in here you are going to check two tabs, the first one **bot** (duh) and the second one will be **speak** (to be able to speak ykyk ?)
then after the URL will be generate it paste it into your browser and allow the bots permissions 

EDITOR NOTE: it WONT make you a sandwich (found it out the hard way)

Anyways now that you done that go back to the bot tab and generate a Token in the **Token** setting


### NOW FOR THE TECHNICAL PART

```bash
git clone --depth 1 https://github.com/enzzzh/EnzzzClanker.git
cd EnzzzClanker
```

now that you are here let's make a .env file for the token

```bash
nvim .env
```

inside this .env you are going to type

```DISCORD_TOKEN="the discord token that you copied like 10s ago"```

and now for the docker part (the unfun part for the guy who built the dockerfile and the CI integrations (me) )

```bash
sudo docker compose build
```

then to run it 

```bash
sudo docker compose up
```

## How to use this 

On ***YOUR*** discord server (plz don't do it in public servers), type in chat /download followed by the link of the youtube video you wanna install


## PLZ READ THIS 

If there is **anything** wrong with the installation or the running part, **DO NOT HESITATE TO WRITE AN ISSUE** I would *really* appreciate it. And if you also have some ideas or some bugs with it, you can always text me on discord. my username is enzzz.h (obviously) 

Aight peace 
