from flask import render_template, session
from app import app, LINK, get_preview

from requests import post
from json import loads

@app.route('/', methods=['GET'])
@app.route('/index')
def index():
	categories = loads(post(LINK, json={'method': 'categories.gets'}).text)
	user = loads(post(LINK, json={'method': 'users.get', 'id': session['id']}).text) if 'id' in session else {'id': 0, 'admin': 2}

	return render_template('index.html',
		title = 'Главная',
		description = '',
		tags = [],
		url = 'index',
		categories = categories,
		user = user,
		preview = get_preview,

		courses = loads(post(LINK, json={'method': 'courses.gets'}).text),
		questions = loads(post(LINK, json={'method': 'questions.gets'}).text),
		experts = loads(post(LINK, json={'method': 'users.gets'}).text),
		news = None,
	)