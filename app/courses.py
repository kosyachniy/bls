from flask import render_template, session
from app import app, LINK, get_preview

from requests import post
from json import loads

@app.route('/courses')
@app.route('/courses/<sub>')
def courses(sub=''):
	categories = loads(post(LINK, json={'method': 'categories.gets'}).text)
	user = loads(post(LINK, json={'method': 'users.get', 'id': session['id']}).text) if 'id' in session else {'id': 0, 'admin': 2}

	tags = ['Курсы',]
	category = 0
	subcategory = 0
	title = 'Курсы'
	for x in categories:
		if x['url'] == 'courses':
			title = x['name'] # Если подкатегория была удалена - останется основная
			tags.append(x['name'])
			category = x['id']

			if sub:
				for i in categories:
					if i['parent'] == x['id'] and i['url'] == sub:
						title = i['name']
						tags.append(i['name'])
						subcategory = i['id']

			break

	courses = loads(post(LINK, json={'method': 'courses.gets', 'category': subcategory if subcategory else category}).text)

	return render_template('courses.html',
		title = title,
		description = '',
		tags = tags,
		url = 'courses/' + sub,
		categories = categories,
		user = user,
		category = category,
		subcategory = subcategory,
		preview = get_preview,

		courses = courses,
	)