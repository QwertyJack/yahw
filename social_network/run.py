#!/usr/bin/env python
# encoding:utf-8

# from social_network import app as app1
# from social_network2 import app as app2
# from werkzeug.wsgi import DispatcherMiddleware
# import os
# app = DispatcherMiddleware(app2, {
#     '/app2':     app1
# })

# app.secret_key = os.urandom(24)
# from werkzeug.serving import run_simple
# run_simple('localhost', 5000, app,
#             use_debugger=True)


from social_network import app
import os
app.secret_key = os.urandom(24)
port = int(os.environ.get('PORT', 5000))
files = [
    './social_network/__init__.py',
    './social_network/models.py',
    './social_network/views.py',
    './social_network/static/css/style1.css'
]

if __name__=='__main__':
    app.run(host = '0.0.0.0', port = port, debug = True, threaded = True, extra_files = files)
