### Windows

Not supported

### Fedora Linux

`sudo dnf groupinstall "Development Tools" -y`

`sudo dnf install curl curl-devel gcc-c++ cmake make -y`

`sudo dnf install postgresql postgresql-devel libpq-devel -y`

`sudo dnf install boost boost-devel websocketpp-devel -y`

### CentOS 7

`sudo yum groupinstall "Development Tools" -y`

`sudo yum install curl curl-devel gcc-c++ cmake make -y`

`sudo yum install postgresql postgresql-devel libpq-devel -y`

`sudo yum install boost boost-devel websocketpp-devel -y`

## Set up PostgreSQL

### Fedora Linux

`sudo dnf install postgresql-server postgresql-contrib`

`sudo postgresql-setup --initdb`

`sudo systemctl start postgresql`

`sudo systemctl enable postgresql`

`sudo -i -u postgres psql`

`CREATE DATABASE judge_brains;`

`CREATE USER judge WITH ENCRYPTED PASSWORD 'your_secure_password';`

`GRANT ALL PRIVILEGES ON DATABASE judge_brains TO judge;`

`\q`

## Your newly created .env file

Your new file named as '.env' must look like this: 

DATABASE_URL=postgres://judge:your_secure_password@localhost/judge_brains 

TELEGRAM_TOKEN=telegram_token_here 

DISCORD_TOKEN=discord_token_here
