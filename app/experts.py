from flask import render_template, session
from app import app, LINK, get_preview

from requests import post
from json import loads

@app.route('/experts')
def experts():
	categories = loads(post(LINK, json={'method': 'categories.gets'}).text)
	user = loads(post(LINK, json={'method': 'users.get', 'id': session['id']}).text) if 'id' in session else {'id': 0, 'admin': 2}

	users = []
	for i, category in enumerate(categories):
		if category['parent'] and category['plus'] == 'course':
			users.append({
				'url': category['url'],
				'name': category['name'],
				'users': loads(post(LINK, json={
					'method': 'users.gets',
					'sort': category['id'],
				}).text),
			})

	return render_template('experts.html',
		title = 'Эксперты',
		description = '',
		tags = [],
		url = 'experts',
		categories = categories,
		user = user,
		preview = get_preview,

		users = users,
	)