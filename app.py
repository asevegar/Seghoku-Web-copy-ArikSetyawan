from flask import Flask, render_template, redirect, url_for, jsonify
from itsdangerous import URLSafeTimedSerializer, BadData, SignatureExpired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissecret'

sToken = URLSafeTimedSerializer('thisissecret')


@app.route('/')
def index():
    data_menu = []

    # request menu
    url_menu = "http://127.0.0.1:5000/api/menu/"
    req_menu = requests.get(url_menu)
    req_menu = req_menu.json()['data']

    for i in req_menu:
        data = {}
        data['id'] = sToken.dumps(i['id'], salt="id_menu"),
        data['nama_menu'] = i['nama_menu']
        data['harga_menu'] = i['harga_menu']
        data['foto_menu'] = "http://127.0.0.1:5000/api/files/?filename={}".format(
            i['foto_menu'])

        # get tenant
        url_tenant = "http://127.0.0.1:5000/api/tenant/"
        req_tenant = requests.get(
            url_tenant, params={'id_tenant': i['id_tenant']})
        req_tenant = req_tenant.json()['data']

        tenant = {}
        tenant['id'] = sToken.dumps(req_tenant['id'], salt="id_tenant")
        tenant['nama_toko'] = req_tenant['nama_toko']
        tenant['no_hp'] = req_tenant['no_hp']

        # get location
        url_location = "http://127.0.0.1:5000/api/locations/"
        req_location = requests.get(
            url_location, params={'id_location': req_tenant['id_location']})
        req_location = req_location.json()['data']

        location = {}
        location['id'] = sToken.dumps(req_location['id'], salt="id_location")
        location['nama_location'] = req_location['nama_location']

        tenant['location'] = location
        data['tenant'] = tenant

        data_menu.append(data)
    # return jsonify(data_menu)
    return render_template("index.html", data_menu=data_menu)


@app.route('/area/<place>')
def area(place):
    try:
        place = sToken.loads(place, salt="id_location", max_age=3600)
        data_menu = []
        # Get location
        url_location = "http://127.0.0.1:5000/api/locations/"
        req_location = requests.get(
            url_location, params={'id_location': place})
        req_location = req_location.json()
        if req_location['status'] == 'error':
            return redirect(url_for('index'))
        else:

            # data_location
            req_location = req_location['data']
            location = {
                "id": sToken.dumps(req_location['id'], salt="id_location") ,
                "nama_location": req_location["nama_location"]
            }

            # get tenant by location
            url_tenant = "http://127.0.0.1:5000/api/tenant/"
            req_tenant = requests.get(
                url_tenant, params={'id_location': req_location['id']})
            req_tenant = req_tenant.json()['data']
            for i in req_tenant:
                tenant = {
                    'id': sToken.dumps(i['id'], salt='id_tenant'),
                    "nama_toko": i['nama_toko'],
                    "no_hp": i['no_hp'],
                    "location": location
                }
                # get menu by tenant
                url_menu = "http://127.0.0.1:5000/api/menu/"
                req_menu = requests.get(
                    url_menu, params={"id_tenant": i['id']})
                req_menu = req_menu.json()['data']
                for j in req_menu:
                    data = {}
                    data['tenant'] = tenant
                    data['id'] = sToken.dumps(j['id'],salt='id_menu'),
                    data['nama_menu'] = j['nama_menu']
                    data['harga_menu'] = j['harga_menu']
                    data['foto_menu'] = "http://127.0.0.1:5000/api/files/?filename={}".format(
                        j['foto_menu'])
                    data_menu.append(data)
            # return jsonify(data_menu)
            return render_template("area.html", data_menu=data_menu, place=req_location['nama_location'])
    except BadData:
        return redirect(url_for('index'))
    except SignatureExpired:
        return redirect(url_for('index'))


@app.route('/mitra/<id_tenant>')
def mitra(id_tenant):
    try:
        id_tenant = sToken.loads(id_tenant, salt="id_tenant", max_age=3600)
        data_menu = []

        # get tenant
        url_tenant = "http://127.0.0.1:5000/api/tenant/"
        req_tenant = requests.get(url_tenant, params={'id_tenant': id_tenant})
        req_tenant = req_tenant.json()
        if req_tenant['status'] == "error":
            return redirect(url_for('index'))
        else:
            req_tenant = req_tenant['data']
            tenant = {
                'id': sToken.dumps(req_tenant['id'], salt='id_tenant') ,
                "nama_toko": req_tenant['nama_toko'],
                "no_hp": req_tenant['no_hp']
            }

            # get location
            url_location = "http://127.0.0.1:5000/api/locations/"
            req_location = requests.get(
                url_location, params={'id_location': req_tenant['id_location']})
            req_location = req_location.json()['data']

            location = {}
            location['id'] = sToken.dumps(req_location['id'], salt='id_location')
            location['nama_location'] = req_location['nama_location']

            tenant['location'] = location

            # get menu by tenant
            url_menu = "http://127.0.0.1:5000/api/menu/"
            req_menu = requests.get(
                url_menu, params={"id_tenant": req_tenant['id']})
            req_menu = req_menu.json()['data']
            for j in req_menu:
                data = {}
                data['tenant'] = tenant
                data['id'] = sToken.dumps(j['id'],salt="id_menu"),
                data['nama_menu'] = j['nama_menu']
                data['harga_menu'] = j['harga_menu']
                data['foto_menu'] = "http://127.0.0.1:5000/api/files/?filename={}".format(
                    j['foto_menu'])
                data_menu.append(data)

            # return jsonify(data_menu)
            return render_template("mitra.html", data_menu=data_menu, mitra=req_tenant['nama_toko'])
    except BadData:
        return redirect(url_for('index'))
    except SignatureExpired:
        return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
