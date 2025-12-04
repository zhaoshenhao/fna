This tool will retrieve the latest financial news, analyze the impact to stocks.

# INSTALL

## DB
`
CREATE USER fna WITH PASSWORD '<DB_PASSWORD>';
CREATE DATABASE fna;
GRANT ALL PRIVILEGES ON DATABASE fna TO fna;
`

## APP
`
git clone https://github.com/zhaoshenhao/fna.git
cd fna
mkdir .env
#-----
GEMINI_API_KEY=<Gemini-api-key>
GROQ_API_KEY=<Groq-api-key>
DB_USER=<db-user>
DB_NAME=<db-name>
DB_PASSWORD=<db-password>
SECRET_KEY=<django-secret-key>
#-----
vi fna/setting.py
#- Update your file
#- Python env
conda create -n fna python=3.13
conda activate fna
pip install -r requirements.txt
playwright install
#-Install palywright dependency
#- Ubuntu
sudo playwright install-deps 
#- Or
sudo apt-get install libatk-bridge2.0-0 libatspi2.0-0 libgbm1 libasound2
#- Redhat/CentOS
yum install -y libatk-1.0.so.0 libatk-bridge-2.0.so.0 libcups.so.2 libdrm.so.2 libatspi.so.0 libXcomposite.so.1 libXdamage.so.1 libXfixes.so.3 libXrandr.so.2 libgbm.so.1 libpango-1.0.so.0 libasound.so.2 atk at-spi2-atk cups-libs libxkbcommon libXcomposite libXdamage libXrandr mesa-libgbm gtk3 libxshmfence alsa-lib
`


