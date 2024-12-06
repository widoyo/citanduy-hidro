from app.models import RDaily
import click
import datetime
import json

def register(app):
    @app.cli.command('ews-rain')
    def ews_rain(now=datetime.datetime.now()):
        rd = RDaily.select().where(RDaily.sampling==now.date())
        rain_list = []
        for r in rd:
            raw = json.loads(r.raw)
            if 'rain' not in raw[0]:
                continue
            pos = r.nama
            pos_id = None
            if r.pos != None:
                pos = r.pos.nama
                pos_id = r.pos.id
            if 'PDA' in pos:
                continue
            minute_start = datetime.datetime.fromisoformat(raw[-1]['sampling'])
            durasi = datetime.timedelta()
            hujan = 0
            if r.source in ('SA', 'SB'):
                for ra in reversed(raw):
                    sampling = datetime.datetime.fromisoformat(ra['sampling'])
                    if sampling < now - datetime.timedelta(minutes=60):
                        continue
                    if float(ra['rain']) > 0.0:
                        durasi += minute_start - sampling
                        minute_start = sampling
                    hujan += float(ra['rain'])
            else:
                l = raw[-1]['rain']
                for ra in reversed(raw):
                    sampling = datetime.datetime.fromisoformat(ra['sampling'])
                    if sampling < now - datetime.timedelta(minutes=60):
                        continue
                    rain_now = l - ra['rain']
                    if rain_now > 0.0:
                        durasi += minute_start - sampling
                        minute_start = sampling
                    hujan += rain_now
                    l = ra['rain']
                    #click.echo('{} {}'.format(sampling.strftime('%H:%M'), ra['rain']))
            if hujan > 0.0:
                rain_list.append({'pos': pos, 'pos_id': pos_id, 'rain': hujan, 'duration': durasi.total_seconds()})
                try:
                    click.echo('Pos: {} {}'.format(r.pos.nama, len(raw)))
                except:
                    click.echo('{} {}'.format(r.nama, len(raw)))
                click.echo('Hujan: {} Durasi: {}'.format(hujan, durasi))
        click.echo(rain_list)

                
    @app.cli.command('hello')
    def hello():
        panjalu_11nop = RDaily.get(15813)
        panjalu_12nop = RDaily.get(15888)
        data = [(k, v) for k, v in panjalu_11nop._24jam().items() if k > 6]
        data2 = [(k, v) for k, v in panjalu_12nop._24jam().items() if k < 7]

        data += data2
        rain_before = 0
        rain_jum = 0
        for k, v in data:
            rain_jam = v.get('rain') - rain_before
            print(k, 'rain_jumlah:', v.get('rain'), 'rain_jam:', rain_jam, ' ', v.get('num'))
            rain_before = v.get('rain')
            rain_jum += rain_jam
        print('Rain Hari:', rain_jum)        