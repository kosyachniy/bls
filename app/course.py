from flask import render_template, session, request, Markup
from app import app, LINK, get_preview

from requests import post
from json import loads
import markdown

@app.route('/courses/<int:id>')
def course(id):
	categories = loads(post(LINK, json={'method': 'categories.gets'}).text)
	user = loads(post(LINK, json={'method': 'users.get', 'id': session['id']}).text) if 'id' in session else {'id': 0, 'admin': 2}

	course = loads(post(LINK, json={'method': 'courses.get', 'id': id}).text)
	course2 = dict(course)
	course2['cont'] = Markup(markdown.markdown(course2['cont']))

	category = 0
	subcategory = 0
	for i in categories:
		if i['id'] == course['category']:
			if i['parent']:
				category = i['parent']
				subcategory = i['id']
			else:
				category = i['id']
			break

	edit = request.args.get('edit')

	return render_template('edit.html' if edit else 'course.html',
		title = course['name'],
		description = course['description'],
		tags = course['tags'],
		url = course['id'],
		categories = categories,
		user = user,
		category = category,
		subcategory = subcategory,
		preview = get_preview,

		course = course if edit else course2,
	)