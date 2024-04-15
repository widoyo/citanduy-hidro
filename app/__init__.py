from flask import Flask
import click
import requests

from app.models import FetchLog, Pos

SDATELEMETRY = 'https://sdatelemetry.com/API_ap_telemetry/datatelemetry2.php?idbbws=8'
TELEMET = 'https://elektronikapolban.duckdns.org:8081/telemet/telemet/tabel10?p=0'


def create_app():
    app = Flask(__name__)
    
    @app.cli.command('fetch-sda')
    def fetch_sdatelemetry():
        '''Membaca data pada server SDATELEMETRY'''
        x = requests.get(SDATELEMETRY)
        fl = FetchLog.create(url=x.url, response=x.status_code, body=x.text)
            
    @app.cli.command('fetch-telemet')
    def fetch_telemet():
        '''Membaca data pada server Omtronik'''
        x = requests.get(TELEMET)
        fl = FetchLog.create(url=x.url, response=x.status_code, body=x.text)

    return app

