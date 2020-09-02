from flask import Flask, render_template
import requests

app = Flask(__name__)


@app.route('/')
def index():
	# request menu
	url_menu = "http://127.0.0.1:5000/api/menu/"
	req_menu = requests.get(url_menu)
	req_menu = req_menu.json()
	data_menu = []
	for i in req_menu['data']:
		data = {}
		data['id'] = i['id'],
		data['nama_menu'] = i['nama_menu']
		data['harga_menu'] = i['harga_menu']
		data['foto_menu'] = "http://127.0.0.1:5000/api/files/?filename={}".format(i['foto_menu'])
		
		# get tenant
		url_tenant = "http://127.0.0.1:5000/api/tenant/"
		req_tenant = requests.get(url_tenant,params={'id_tenant':i['id_tenant']})
		req_tenant = req_tenant.json()['data']

		tenant = {}	

		tenant['nama_toko'] = req_tenant['nama_toko']
		tenant['no_hp'] = req_tenant['no_hp']

		# get location
		url_location = "http://127.0.0.1:5000/api/locations/"
		req_location = requests.get(url_location,params={'id_location':req_tenant['id_location']})
		req_location = req_location.json()['data']

		location = {}
		location['id'] = req_location['id']
		location['nama_location'] = req_location['nama_location']

		tenant['location'] = location
		data['tenant'] = tenant

		data_menu.append(data)

	return render_template("index.html", data_menu=data_menu)

@app.route('/area/<location>')
def area(location):
	return "oke"


if __name__ == "__main__":
	app.run(debug=True, port=5001)