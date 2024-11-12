from app.models import RDaily


def register(app):
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