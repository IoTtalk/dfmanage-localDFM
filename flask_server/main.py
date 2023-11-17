import logging

from server import create_app

logging.basicConfig(level=logging.INFO)

app = create_app()
app.debug = True
# context = ('/etc/letsencrypt/live/dfmanage.iottalk.tw/fullchain.pem', '/etc/letsencrypt/live/dfmanage.iottalk.tw/privkey.pem')
app.run(host='0.0.0.0', port=8100)
