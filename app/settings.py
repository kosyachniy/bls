from flask import session, request, render_template
from app import app, LINK, get_url

from requests import post
import base64

@app.route('/settings', methods=['POST'])
def settings():
	x = request.form

	if 'token' not in session:
		return render_template('message.html', cont='3')

	req = {
		'method': 'profile.edit',
		'token': session['token']
	}

	for i in ('name', 'surname', 'description'): #mail #password
		if i in x:
			req[i] = x[i]

	if 'photo' in request.files:
		y = request.files['photo'].stream.read()
		y = str(base64.b64encode(y))[2:-1]
		req['photo'] = y
		req['file'] = request.files['photo'].filename

	req = post(LINK, json=req).text

	if req != '0' and len(req) < 3:
		return render_template('message.html', cont=req)

	return get_url(request.args.get('url'))