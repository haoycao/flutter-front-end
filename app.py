######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '1q2w3e4r'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	try:
		user.is_authenticated = request.form['password'] == pwd
	except:
		pass
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out', loggedin=False)

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		gender=request.form.get('gender')
		hometown=request.form.get('hometown')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		birthdate=request.form.get('birthdate')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password,gender,hometown,first_name,last_name,birth_date) VALUES ('{0}', '{1}','{2}','{3}','{4}','{5}','{6}')".format(email, password,gender,hometown,firstname,lastname,birthdate)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!', loggedin=True)
	else:
		return render_template('hello.html', message='Duplicate Email!', loggedin=False)
		# return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def getUserById(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT *  FROM Users WHERE user_id = '{0}'".format(uid))
    return cursor.fetchone()

def getFriendIds(uid):
	fids = []
	cursor = conn.cursor()
	cursor.execute('SELECT user_id2 FROM Friends WHERE user_id1=%s', (uid))
	for _ in cursor.fetchall():
		fids.append(_[0])
	cursor = conn.cursor()
	cursor.execute('SELECT user_id1 FROM Friends WHERE user_id2=%s', (uid))
	for _ in cursor.fetchall():
		fids.append(_[0])
	return fids

def getLikes(pid):
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM Likes WHERE photo_id=%s', (pid))
    num = 0
    users = []
    for _ in cursor.fetchall():
        uid = _[0]
        num += 1
        if uid > 1:
            cs = conn.cursor()
            cs.execute('SELECT first_name, last_name FROM Users WHERE user_id=%s', (uid))
            res = cs.fetchone()
            users.append(res[0] + ' ' + res[1])
    return num, users
   
    

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", loggedin=True)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        photo_data =imgfile.read()
        tags = request.form.get('tags')
        albumid = request.form.get('albumid')
        tags = tags.split(' ')
        tagids = []
        for tag in tags:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM Tags WHERE name=%s', (tag))
            if cursor.fetchall()[0][0] == 0:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO Tags (name) VALUES (%s)', (tag))
                conn.commit()
            cursor = conn.cursor()
            cursor.execute('SELECT tag_id FROM Tags WHERE name=%s', (tag))
            tagids.append(cursor.fetchone()[0])
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Photos (data, user_id, caption, albums_id) VALUES (%s, %s, %s, %s )''' ,(photo_data,uid, caption,albumid))
        conn.commit()
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(photo_id) FROM Photos')
        photo_id = cursor.fetchone()[0]
        for id in tagids:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO Tagged (photo_id, tag_id) VALUES (%s, %s)''' ,(photo_id,id))
            conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64, loggedin=True)
    else:
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM Albums WHERE user_id = %s''' ,(uid))
        albums = []
        for album in cursor.fetchall():
            albums.append([album[0], album[1]])
        return render_template('upload.html', albums=albums)
#end photo uploading code

#create album
@app.route('/createalbum', methods=['GET', 'POST'])
@flask_login.login_required
def createalbum():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		name = request.form.get('name')
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (name, user_id, date) VALUES (%s, %s, NOW() )''' , (name,uid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album created!', photos=getUsersPhotos(uid),base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('createalbum.html')

#add friend
@app.route('/addfriend',methods=['GET','POST'])
@flask_login.login_required
def addfriend():
    if flask.request.method == 'GET':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        friends = []
        fids = getFriendIds(uid)
        for _ in fids:
            friends.append(getUserById(_))
        recomids = []
        for _ in fids:
            recomids += getFriendIds(_)
        recomids = list(set(recomids))

        for _ in fids:
            recomids.remove(uid)

        recoms = []
        for _ in recomids:
            recoms.append(getUserById(_))
        return render_template('addfriend.html', friends=friends, recoms=recoms)
    else:   
        uid = getUserIdFromEmail(flask_login.current_user.id)
        email = request.form.get('email')
        try:
            fuid = getUserIdFromEmail(email)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM Friends WHERE user_id1=%s AND user_id2=%s', (uid, fuid))
            count1 = cursor.fetchone()[0]
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM Friends WHERE user_id2=%s AND user_id1=%s', (uid, fuid))
            count2 = cursor.fetchone()[0]
            print(count1, count2)
            if count1 == 0 and count2 == 0:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO Friends (user_id1, user_id2) VALUES (%s, %s)''' , (uid,fuid))
                conn.commit()
                return render_template('hello.html', name=flask_login.current_user.id, message='Added a friend!', photos=getUsersPhotos(uid),base64=base64, loggedin=True)
            else:
                return render_template('addfriend.html', message='Already is friend, Try another!')
        except:
            return render_template('addfriend.html', message='No such user, Try again!')

#user albums
@app.route('/albums',methods=['GET'])
@flask_login.login_required
def albums():
    cs1 = conn.cursor()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cs1.execute('SELECT *  FROM Albums WHERE user_id = %s', (uid))
    return render_template('albums.html', albums=cs1.fetchall())

#remove a photo
def removephoto(pid):
    cs2 = conn.cursor()
    cs2.execute('DELETE FROM Tagged WHERE photo_id=%s', (pid[0]))
    conn.commit()
    cs2.execute('DELETE FROM Photos WHERE photo_id=%s', (pid[0]))
    conn.commit()
    
#photo
@app.route('/photos/<pid>',methods=['GET'])
def photo(pid):
    cs1 = conn.cursor()
    cs1.execute('SELECT * FROM Photos WHERE photo_id = %s', (pid))
    cs2 = conn.cursor()
    cs2.execute('SELECT tag_id FROM Tagged WHERE photo_id=%s', (pid))
    tids = []
    for _ in cs2.fetchall():
        tids.append(_[0])
    tags = []
    for _ in tids:
        cs2 = conn.cursor()
        cs2.execute('SELECT name FROM Tags WHERE tag_id=%s', (_))
        tags.append(cs2.fetchone()[0])
    photo = cs1.fetchone()
    try:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        if uid == photo[4]:
            logged = True
        else:
            logged = False
    except:
        logged = False
    num, users = getLikes(pid)
    return render_template('photo.html', photo=photo, base64=base64, tags=tags, logged=logged, num=num, users=users)

#delete photo
@app.route('/deletephoto/<pid>',methods=['POST'])
@flask_login.login_required
def deletephoto(pid):
    removephoto(pid)
    return flask.redirect(flask.url_for('albums'))

#comment search
@app.route('/commentsearch',methods=['POST'])
def commentsearch():
    keyword = request.form.get('keyword')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, COUNT(*) AS ccount FROM Comments WHERE text Like "%'+keyword+'%" GROUP BY user_id ORDER BY ccount DESC')
    users = []
    for _ in cursor.fetchall():
        if _[0] > 1:
            cs = conn.cursor()
            cs.execute('SELECT first_name, last_name FROM Users WHERE user_id=%s', (_[0]))
            res = cs.fetchone()
            users.append([res[0] + ' ' + res[1], _[1]])
    return render_template('search.html', users=users)

#tag search
@app.route('/tagsearch',methods=['POST'])
def tagsearch():
    photos = []
    keyword = request.form.get('keyword')
    tags = keyword.split(' ')
    tids = []
    for tag in tags:
        cursor = conn.cursor()
        cursor.execute('SELECT tag_id FROM Tags WHERE name=%s', (tag))
        try:
            _ = cursor.fetchone()[0]
            tids.append(_)
        except:            
            return render_template('photos.html', photos=photos, base64=base64)
    tpids = []
    for tid in tids:
        cursor.execute('SELECT photo_id FROM Tagged WHERE tag_id=%s', (tid))
        tpids.append([_[0] for _ in cursor.fetchall()])
    pids = tpids[0]
    for i in range(len(tpids)):
        pids = list(set(pids).intersection(set(tpids[i])))
    for pid in pids:
        cursor.execute('SELECT * FROM Photos WHERE photo_id = %s', (pid))
        photos.append(cursor.fetchone())
    return render_template('photos.html', photos=photos, base64=base64)

#comment
@app.route('/comment/<pid>',methods=['POST'])
def comment(pid):
    comment = request.form.get('comment')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Photos WHERE photo_id = %s', (pid))
    photo = cursor.fetchone()
    try:
        _ = flask_login.current_user.id
        uid = getUserIdFromEmail(flask_login.current_user.id)
        loggedin = True
        if photo[4] == uid:
            return render_template('hello.html', name=flask_login.current_user.id, message='Cannot comment to your own photo', photos=getUsersPhotos(uid),base64=base64, loggedin=loggedin)
        else:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Comments (user_id, photo_id, text, date) VALUES (%s, %s, %s, NOW())', (uid, pid, comment))
            conn.commit()
            return render_template('hello.html', name=flask_login.current_user.id, message='Comment success', photos=getUsersPhotos(uid),base64=base64, loggedin=loggedin)
    except:
        loggedin = False
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Comments (user_id, photo_id, text, date) VALUES (1, %s, %s, NOW())', (pid, comment))
        conn.commit()
        return render_template('hello.html', message='Welecome to Photoshare', loggedin=loggedin)

#like
@app.route('/like/<pid>',methods=['POST'])
def like(pid):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Photos WHERE photo_id = %s', (pid))
    photo = cursor.fetchone()
    try:
        _ = flask_login.current_user.id
        uid = getUserIdFromEmail(flask_login.current_user.id)        
    except:
        uid = 1
    
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM Likes WHERE photo_id=%s AND user_id=%s', (pid, uid))
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO Likes (user_id, photo_id) VALUES (%s, %s)', (uid, pid))
        conn.commit()
    return flask.redirect('/photos/'+pid)

#tags
@app.route('/tags',methods=['GET'])
def tags():
    cs1 = conn.cursor()
    cs1.execute('SELECT * FROM Tags')
    tags = cs1.fetchall()
    try:
        _ = flask_login.current_user.id
        uid = getUserIdFromEmail(flask_login.current_user.id)
        loggedin = True
    except:
        loggedin = False
    tag_ids = [_[0] for _ in tags]
    tag_photos = []
    for tid in tag_ids:
        cs2 = conn.cursor()
        cs2.execute('SELECT COUNT(*) FROM Tagged WHERE tag_id=%s', (tid))
        tag_photos.append(cs2.fetchone()[0])
    populars = []
    try:    
        for i in range(5):
            maxidx = tag_photos.index(max(tag_photos))
            populars.append(tags[tag_ids[maxidx]-1])
            tag_ids.pop(maxidx)
            tag_photos.pop(maxidx)
        
    except:
        pass
    return render_template('tags.html', tags=tags, pop=populars, logged=loggedin)
#all tag photos
@app.route('/tags/<tid>',methods=['GET'])
def tagphotos(tid):
    cs1 = conn.cursor()
    cs1.execute('SELECT photo_id FROM Tagged WHERE tag_id=%s', (tid))
    photos = []
    for _ in cs1.fetchall():
        cs2 = conn.cursor()
        cs2.execute('SELECT * FROM Photos WHERE photo_id=%s', (_[0]))
        photos.append(cs2.fetchone())
    return render_template('photos.html', photos=photos, base64=base64)

#all tag photos of a user
@app.route('/usertags/<tid>',methods=['GET'])
@flask_login.login_required
def usertagphotos(tid):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cs1 = conn.cursor()
    cs1.execute('SELECT photo_id FROM Tagged WHERE tag_id=%s', (tid))
    photos = []
    for _ in cs1.fetchall():
        print(_[0])
        cs2 = conn.cursor()
        cs2.execute('SELECT * FROM Photos WHERE photo_id=%s', (_[0]))
        photo = cs2.fetchone()
        if photo[4] == uid:
            photos.append(photo)
    return render_template('photos.html', photos=photos, base64=base64)

#delete album
@app.route('/deletealbum/<aid>',methods=['POST'])
@flask_login.login_required
def deletealbum(aid):
    cs1 = conn.cursor()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cs1.execute('SELECT photo_id FROM Photos WHERE albums_id = %s', (aid))
    for pid in cs1.fetchall():
        removephoto(pid[0])
    cs2 = conn.cursor()
    cs2.execute('DELETE FROM Albums WHERE albums_id=%s', (aid))
    conn.commit()
    return flask.redirect(flask.url_for('albums'))

#user album photos
@app.route('/albums/<albumid>',methods=['GET'])
@flask_login.login_required
def albumphotos(albumid):
    cs1 = conn.cursor()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cs1.execute('SELECT *  FROM Photos WHERE user_id = %s AND albums_id = %s', (uid, albumid))
    return render_template('photos.html', photos=cs1.fetchall(), base64=base64)

#all albums
@app.route('/allalbums',methods=['GET'])
def allalbums():
    cs1 = conn.cursor()
    cs1.execute('SELECT *  FROM Albums')
    return render_template('allalbums.html', albums=cs1.fetchall())

#all album photos
@app.route('/allalbums/<albumid>',methods=['GET'])
def allalbumphotos(albumid):
    cs1 = conn.cursor()
    cs1.execute('SELECT *  FROM Photos WHERE albums_id = %s', (albumid))
    return render_template('photos.html', photos=cs1.fetchall(), base64=base64)

def takeSecond(ele):
    return ele[1]

@app.route('/top10contributed',methods=['GET'])
def top():
	cs1 = conn.cursor()
	cs1.execute("SELECT user_id,first_name,last_name  FROM Users WHERE user_id > 1")
	res = []
	temp = cs1.fetchall()
	uids = [_[0] for _ in temp]
	names = [_[1] + ' ' + _[2] for _ in temp]
	for i in range(len(uids)):
		num = 0
		cs1.execute('SELECT COUNT(*) FROM Photos WHERE user_id=%s', (uids[i]))
		num += cs1.fetchone()[0]
		cs1.execute('SELECT COUNT(*) FROM Comments WHERE user_id=%s', (uids[i]))
		num += cs1.fetchone()[0]
		res.append([names[i], num])
	if len(res) > 10:
		res = res[:10]
	res.sort(key=takeSecond, reverse=True)
	return render_template('search.html', users=res)

@app.route('/maylike',methods=['GET'])
@flask_login.login_required
def maylike():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cs1 = conn.cursor()
    cs1.execute("SELECT photo_id  FROM Photos WHERE user_id = %s", (uid))
    res = []
    pids = cs1.fetchall()
    tids = {}
    for pid in pids:
        cs1.execute('SELECT tag_id FROM Tagged WHERE photo_id=%s', (pid[0]))
        temp = cs1.fetchall()
        for _ in temp:
            if _[0] in tids:
                tids[_[0]] += 1
            else:
                tids[_[0]] = 1
    mosttids = []
    for _ in tids:
        mosttids.append([_, tids[_]])
    mosttids.sort(key=takeSecond, reverse=True)
    if len(mosttids) > 5:
        mosttids = mosttids[:5]
    mosttids = [_[0] for _ in mosttids]
    
    cs1.execute("SELECT photo_id  FROM Photos")
    temp = cs1.fetchall()
    allphotos = []
    for _ in temp:
        item = []
        cs1.execute('SELECT tag_id FROM Tagged WHERE photo_id=%s', (_[0]))
        for __ in cs1.fetchall():
            item.append(__[0])
        allphotos.append([_[0], item])
    # print(allphotos)
    photoranks = []
    for _ in allphotos:
        count = 0
        for tid in mosttids:
            if tid in _[1]:
                count += 1
        if count > 0:
            photoranks.append([_[0], count])
    # print(photoranks)
    photoranks.sort(key=takeSecond, reverse=True)
    photoranks = [_[0] for _ in photoranks]
    
    photos = []
    for pid in photoranks:
        cs1.execute('SELECT * FROM Photos WHERE photo_id=%s', (pid))
        photos.append(cs1.fetchone())
    return render_template('photos.html', photos=photos, base64=base64)


		


     
	
	

#default page
@app.route("/", methods=['GET'])
def hello():
	try:
		_ = flask_login.current_user.id
		uid = getUserIdFromEmail(flask_login.current_user.id)
		loggedin = True
		return render_template('hello.html', name=flask_login.current_user.id, message='Welecome to Photoshare', photos=getUsersPhotos(uid),base64=base64, loggedin=loggedin)
	except:
		loggedin = False
		return render_template('hello.html', message='Welecome to Photoshare', loggedin=loggedin)


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
