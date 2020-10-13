from flask import Flask, flash, render_template, redirect, url_for, jsonify, session, request
from itsdangerous import URLSafeTimedSerializer, BadData, SignatureExpired
from PIL import Image
import requests, random, timeit, io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissecret'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

sToken = URLSafeTimedSerializer('thisissecret')

# Custom Function
def islogin():
    if "islogin" in session:
        return True

def isadmin():
    if islogin():
        if 'admin' in session:
            return True

def isnormal():
    if islogin():
        if 'regular' in session:
            return True

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API URL
url_menu = "http://127.0.0.1:5000/api/menu/"
url_tenant = "http://127.0.0.1:5000/api/tenant/"
url_location = "http://127.0.0.1:5000/api/locations/"
url_auth = "http://127.0.0.1:5000/api/auth/"
url_user = "http://127.0.0.1:5000/api/users/"
url_level_user = "http://127.0.0.1:5000/api/level_user/"



@app.route('/')
def index():
    data_menu = []

    # request menu
    req_menu = requests.get(url_menu)
    req_menu = req_menu.json()['data']

    # Shuffle data
    req_menu = random.sample(req_menu,len(req_menu))

    for i in req_menu:
        data = {}
        data['id'] = sToken.dumps(i['id'], salt="id_menu")
        data['nama_menu'] = i['nama_menu']
        data['harga_menu'] = i['harga_menu']
        data['foto_menu'] = i['foto_menu']

        # get tenant
        tenant = {}
        tenant['id'] = sToken.dumps(i["tenant"]['id'], salt="id_tenant")
        tenant['nama_toko'] = i["tenant"]['nama_toko']
        tenant['no_hp'] = i["tenant"]['no_hp']

        # get location
        location = {}
        location['id'] = sToken.dumps(i["tenant"]["location"]['id'], salt="id_location")
        location['nama_location'] = i["tenant"]["location"]['nama_location']

        tenant['location'] = location
        data['tenant'] = tenant

        data_menu.append(data)
    # return jsonify(data_menu)
    return render_template("index.html", data_menu=data_menu)


@app.route('/area/<place>')
def area(place):
    try:
        tempat = sToken.loads(place, salt="id_location", max_age=3600)
        data_menu = []

        # request menu
        req_menu = requests.get(url_menu, params={"id_location":tempat})
        req_menu = req_menu.json()['data']

        # Shuffle data
        req_menu = random.sample(req_menu,len(req_menu))
        for i in req_menu:
            data = {}
            data['id'] = sToken.dumps(i['id'], salt="id_menu")
            data['nama_menu'] = i['nama_menu']
            data['harga_menu'] = i['harga_menu']
            data['foto_menu'] = i['foto_menu']

            # get tenant
            tenant = {}
            tenant['id'] = sToken.dumps(i["tenant"]['id'], salt="id_tenant")
            tenant['nama_toko'] = i["tenant"]['nama_toko']
            tenant['no_hp'] = i["tenant"]['no_hp']

            # get location
            location = {}
            location['id'] = sToken.dumps(i["tenant"]["location"]['id'], salt="id_location")
            location['nama_location'] = i["tenant"]["location"]['nama_location']

            # set place
            place = i["tenant"]["location"]['nama_location']

            tenant['location'] = location
            data['tenant'] = tenant

            data_menu.append(data)
        return render_template("area.html", data_menu=data_menu, place=place)
    except BadData:
        return redirect(url_for('index'))
    except SignatureExpired:
        return redirect(url_for('index'))

@app.route('/mitra/<id_tenant>')
def mitra(id_tenant):
    try:
        id_tenant = sToken.loads(id_tenant, salt="id_tenant", max_age=3600)

        data_menu = []

        # get menu
        req_menu = requests.get(url_menu, params={'id_tenant': id_tenant})
        req_menu = req_menu.json()
        if req_menu['status'] == "error":
            return redirect(url_for('index'))
        else:
            req_menu = req_menu['data']
            tenant = {
                "id":sToken.dumps(req_menu['id'],salt="id_tenant"),
                "nama_toko":req_menu['nama_toko'],
                "no_hp": req_menu['no_hp'],
                "location":{
                    "id":sToken.dumps(req_menu['location']['id'], salt='id_location'),
                    "nama_location":req_menu['location']['nama_location']
                }
            }
            for j in req_menu['menu']:
                data = {}
                data['tenant'] = tenant
                data['id'] = sToken.dumps(j['id'], salt="id_menu")
                data['nama_menu'] = j['nama_menu']
                data['harga_menu'] = j['harga_menu']
                data['foto_menu'] = j['foto_menu']
                data_menu.append(data)
            return render_template("mitra.html", data_menu=data_menu, mitra=req_menu['nama_toko'])
    except BadData:
        return redirect(url_for('index'))
    except SignatureExpired:
        return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if islogin():
        return redirect(url_for('index'))
    else:
        if request.method == 'GET':
            return render_template('login.html')
        else:
            email = request.form['email']
            password = request.form['password']

            json = {
                "email":email,
                "password":password
            }

            req = requests.post(url_auth, json=json)

            if req.status_code == 200:
                res = req.json()
                if res['status'] == 'success':
                    session['islogin'] = True,
                    session['id_user'] = res['data']['id'],
                    session['nama_user'] = res['data']['nama'].capitalize()

                    id_level = res['data']['id_level']

                    req_level_user = requests.get(url_level_user,params={"id_level":id_level})
                    nama_level = req_level_user.json()['data']['nama_level']

                    if nama_level == 'Admin':
                        session['admin'] = True
                        req_tenant = requests.get(url_tenant,params={"id_user":res['data']['id']})
                        res_tenant = req_tenant.json()
                        session['id_tenant']=res_tenant['data']['id']
                        return redirect(url_for('dashboard'))
                    if nama_level == 'Regular':
                        session['regular'] = True
                        return redirect(url_for('index'))

                return redirect(url_user("login"))
            return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if islogin():
        return redirect(url_for('index'))
    else:
        if request.method == "GET":
            return render_template("register.html")
        else:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']

            json = {
                'id_level':"5f48d40db863173baa5be801",
                'nama': name,
                'email': email,
                "password": password
            }

            req = requests.post(url_user, json=json)
            if req.status_code == 200:
                res = req.json()
                if res['status'] == 'success':
                    return redirect(url_for('login'))
                else:
                    return redirect(url_for('register'))
            else:
                return redirect(url_for('register'))

@app.route('/join-partner', methods=['GET', 'POST'])
def joinparter():
    if islogin():
        return redirect(url_for('index'))
    else:
        if request.method == "GET":
            return render_template("registerpartner.html")
        else:
            name = request.form['namepartner']
            email = request.form['emailpartner']
            password = request.form['passwordpartner']

            json = {
                'id_level':"5f48b92ca69c2f203b82b533",
                'nama': name,
                'email': email,
                "password": password
            }

            req = requests.post(url_user, json=json)
            if req.status_code == 200:
                res = req.json()
                if res['status'] == 'success':
                    return redirect(url_for('login'))
                else:
                    return redirect(url_for('joinparter'))
            else:
                return redirect(url_for('joinparter'))


@app.route('/dashboard')
def dashboard():
    if isadmin():
        return render_template("dashboard.html")
    else:
        return redirect(url_for('index'))

@app.route('/dashboard/menu')
def dashboard_menu():
    if isadmin():

        data_menu = []

        # get menu
        req_menu = requests.get(url_menu,{"id_tenant":session['id_tenant']})
        req_menu = req_menu.json()
        if req_menu['status'] == "error":
            return redirect(url_for('index'))
        else:
            req_menu = req_menu['data']
            tenant = {
                "id":sToken.dumps(req_menu['id'],salt="id_tenant"),
                "nama_toko":req_menu['nama_toko'],
                "no_hp": req_menu['no_hp'],
                "location":{
                    "id":sToken.dumps(req_menu['location']['id'], salt='id_location'),
                    "nama_location":req_menu['location']['nama_location']
                }
            }
            for j in req_menu['menu']:
                data = {}
                data['tenant'] = tenant
                data['id'] = sToken.dumps(j['id'], salt="id_menu")
                data['nama_menu'] = j['nama_menu']
                data['harga_menu'] = j['harga_menu']
                data['foto_menu'] = j['foto_menu']
                data_menu.append(data)
            return render_template('menu.html',data_menu=data_menu)
    else:
        return redirect(url_for('index'))

@app.route('/create_menu', methods=['POST'])
def create_menu():
    if isadmin():
        menu_name = request.form['menu_name']
        menu_price = request.form['menu_price']
        if 'menu_photo' not in request.files:
            return "nope"
        file = request.files['menu_photo']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return "nope"
        if file and allowed_file(file.filename):
            image = file
            image.name = image.filename
            image = io.BufferedReader(image)
            data = {"id_tenant":session['id_tenant'],"nama_menu":menu_name,"harga_menu":menu_price}
            req = requests.post(url_menu,data=data,files={"FotoMenu":image})
            if req.status_code == 200:
                res = req.json()
                if res['status'] == 'success':
                    flash("Created",'success')
                    return redirect(url_for('dashboard_menu'))
                else:
                    flash("Opps Something Wrong!","error")
                    return redirect(url_for('dashboard_menu'))
            else:
                flash("Opps Server Error!","error")
                return redirect(url_for('dashboard_menu'))
        else:
            flash("File Not Allowed!","error")
            return redirect(url_for('dashboard_menu'))
    else:
        return redirect(url_for('index'))

@app.route('/edit_menu/<id_menu>', methods=['POST'])
def edit_menu(id_menu):
    if isadmin():
        id_menu = sToken.loads(id_menu,salt='id_menu',max_age=3600)
        # get menu
        req_menu = requests.get(url_menu,params={'id_menu':id_menu})
        if req_menu.status_code == 200:
            res = req_menu.json()
            if res['status'] == 'success' and res['data']['id_tenant'] == session['id_tenant']:
                # get data form
                menu_name = request.form['menu_name']
                menu_price = request.form['menu_price']
                # pack data into dictionary fo requests
                data = {"id_menu":id_menu,"nama_menu":menu_name,"harga_menu":menu_price}
                # get form image data
                file = request.files['menu_photo']
                if file.filename == '':
                    update_menu =  requests.put(url_menu,data=data)
                    if update_menu.status_code == 200:
                        res = update_menu.json()
                        if res['status'] == 'success':
                            flash("Updated","success")
                            return redirect(url_for('dashboard_menu'))
                        else:
                            flash("Opps Something Wrong!","error")
                            return redirect(url_for('dashboard_menu'))
                    else:
                        flash("Opps Server Error!","error")
                        return "server error"
                if file and allowed_file(file.filename):
                    image = file
                    image.name = image.filename
                    image = io.BufferedReader(image)
                    req = requests.put(url_menu,data=data,files={"FotoMenu":image})
                    if req.status_code == 200:
                        res = req.json()
                        if res['status'] == 'success':
                            flash("Updated","success")
                            return redirect(url_for('dashboard_menu'))
                        else:
                            flash("Opps Something Wrong!","error")
                            return redirect(url_for('dashboard_menu'))
                    else:
                        flash("Opps Server Error!","error")
                        return redirect(url_for('dashboard_menu'))
                else:
                    flash("File Not Allowed!","error")
                    return redirect(url_for('dashboard_menu'))
            else:
                flash("User Not Allowed!","error")
                return redirect(url_for('dashboard_menu'))
        else:
            flash("Opps Server Error!","error")
            return redirect(url_for('dashboard_menu'))
    else:
        return redirect(url_for('index'))

@app.route('/remove_menu/<id_menu>')
def remove_menu(id_menu):
    if isadmin():
        id_menu = sToken.loads(id_menu,salt='id_menu',max_age=3600)
        # get menu
        req_menu = requests.get(url_menu,params={'id_menu':id_menu})
        if req_menu.status_code == 200:
            res = req_menu.json()
            if res['status'] == 'success' and res['data']['id_tenant'] == session['id_tenant']:
                req = requests.delete(url_menu,params={"id_menu":id_menu})
                if req.status_code == 200:
                    res = req.json()
                    if res['status'] == 'success':
                        flash("Deleted","success")
                        return redirect(url_for('dashboard_menu'))
                    else:
                        flash("Opps Something Wrong!","error")
                        return redirect(url_for('dashboard_menu'))
                else:
                    flash("Opps Server Error!","error")
                    return redirect(url_for('dashboard_menu'))
            else:
                flash("User Not Allowed!")
                return redirect(url_for('dashboard_menu'))
        else:
            flash("Opps Server Error","error")
            return redirect(url_for('dashboard_menu'))
    else:
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
