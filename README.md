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

### Windows (Visual Studio Setup)

For Windows, you need to manually set up the dependencies in Visual Studio. Here's a step-by-step guide:
1. Install Visual Studio

Download and install the latest version of Visual Studio from [Visual Studio Downloads](https://visualstudio.microsoft.com/downloads/). 
Choose the "Desktop development with C++" workload during installation.

2. Install PostgreSQL

    Download the latest version of [PostgreSQL](https://www.postgresql.org/download/windows/).
    Run the installer and follow the instructions to install PostgreSQL.
    During the installation, make sure to select the "Development Libraries" for PostgreSQL to get `libpq`.

3. Install Boost

Download Boost from the [official site](https://www.boost.org/users/download/).

    Extract the Boost archive to a directory (e.g., `C:\boost_1_87_0`).
    Run `bootstrap.bat` (located in the Boost folder) to build Boost libraries.

Alternatively, you can install Boost via vcpkg if you prefer:

[Install vcpkg](https://github.com/microsoft/vcpkg/) and follow its instructions.

Run:

`vcpkg install boost-asio boost-system boost-filesystem`

4. Configure Project in Visual Studio

    Open Visual Studio and create a new C++ console application project.

    Link PostgreSQL:
        Find the location of `libpq.lib` and `libpq.dll` (usually in the PostgreSQL installation folder under `lib\`).
        Right-click on the project in Solution Explorer → Properties → Configuration Properties → VC++ Directories.
        Add the path to `lib` folder in the Library Directories and the path to `include` folder in the Include Directories.
        Under Linker → Input, add `libpq.lib` to Additional Dependencies.

    Link Boost:
        If you installed Boost manually, add the Boost directory to VC++ Directories → Include Directories and Library Directories.
        If using vcpkg, you should have it integrated automatically with Visual Studio.

    Add WebSocket++:
        Download WebSocket++ from [WebSocket++ GitHub](https://github.com/zaphoyd/websocketpp).
        Follow the instructions to add the `include` folder and `lib` folder to your project settings as you did for PostgreSQL.

### Notes

- Ensure PostgreSQL is running locally or remotely for your bot to connect.

- Use Boost.Asio for asynchronous networking operations (both for HTTP/HTTPS and WebSocket connections).

- For PostgreSQL queries, using `libpq` in asynchronous mode is supported but requires integration with `Boost.Asio` or multi-threading to handle database interactions efficiently.


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
