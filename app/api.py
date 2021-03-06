from flask import request
from app import app

import time, base64
from mongodb import *
from re import findall, match
from hashlib import md5
from json import dumps
from random import randint
from os import listdir, remove

generate = lambda length=32: ''.join([chr(randint(48, 123)) for i in range(length)])

def max_image(url):
	x = listdir(url)
	k = 0
	for i in x:
		j = findall(r'\d+', i)
		if len(j) and int(j[0]) > k:
			k = int(j[0])
	return k+1

def load_image(url, data, adr=None, format='jpg', type='base64'):
	if type == 'base64':
		data = base64.b64decode(data)

	if adr:
		id = adr

		for i in listdir(url):
			if str(adr) + '.' in i:
				remove(url + '/' + i)
	else:
		id = max_image(url)

	with open('%s/%d.%s' % (url, id, format), 'wb') as file:
		file.write(data)

	return id

def errors(x, filters):
	for i in filters:
		if i[0] in x:
			#Неправильный тип данных
			if type(x[i[0]]) != i[2] or (type(x[i[0]]) == list and any(type(j) != i[3] for j in x[i[0]])):
				mes = 'Invalid data type: %s (required %s' % (i[0], str(i[2]))
				if i[2] == list:
					mes += ' - %s' % str(i[3])
				mes += ')'
				return dumps({'error': 4, 'message': mes})

		#Не все поля заполнены
		elif i[1]:
			return dumps({'error': 3, 'message': 'Not all required fields are filled in: %s' % i[0]})

def del_id(x):
	y = []
	for i in x:
		del i['_id']
		y.append(i)
	return y


type_transactions = (
	'Unknown transaction',
	'Send tokens',
	'Tokens for registration',
)


@app.route('/', methods=['POST'])
def process():
	x = request.json
	#print(x)

	if 'method' not in x:
		return dumps({'error': 2, 'message': 'Wrong method'})

	#Убираем лишние отступы
	for i in x:
		if type(x[i]) == str:
			x[i] = x[i].strip()

	#Определение пользователя
	if 'token' in x:
		user = db['tokens'].find_one({'token': x['token']})['id']
	else:
		user = 0

	try:
#Регистрация
		if x['method'] == 'profile.reg':
			#Не все поля заполнены
			mes = errors(x, (
				('login', True, str),
				('pass', True, str),
				('mail', True, str),
				('name', False, str),
				('surname', False, str),
			))
			if mes: return mes

			x['login'] = x['login'].lower()

			#Логин уже зарегистрирован
			if len(list(db['users'].find({'login': x['login']}))):
				return dumps({'error': 5, 'message': 'This login already exists'})

			#Недопустимый логин
			if not 3 <= len(x['login']) <= 10 or len(findall('[^a-z0-9]', x['login'])) or not len(findall('[a-z]', x['login'])):
				return dumps({'error': 6, 'message': 'Wrong login: length must be more than 3 and less than 10 characters, consist only of digits and at least a few latin letters'})

			#Почта уже зарегистрирована
			if len(list(db['users'].find({'mail': x['mail']}))):
				return dumps({'error': 7, 'message': 'This mail already exsists'})

			#Недопустимый пароль
			if not 6 <= len(x['pass']) <= 40 or len(findall('[^a-zA-z0-9!@#$%^&*()-_+=;:,./?\|`~\[\]{}]', x['pass'])) or not len(findall('[a-zA-Z]', x['pass'])) or not len(findall('[0-9]', x['pass'])):
				return dumps({'error': 8, 'message': 'Invalid password: the length must be from 6 to 40 characters, consist of mandatory digits, characters:! @, #, $, %, ^, &, *, (, ), -, _, +, =, ;, :, ,, ., /, ?, |, `, ~, [, ], {, } and necessarily Latin letters'})

			#Недопустимая почта
			if match('.+@.+\..+', x['mail']) == None:
				return dumps({'error': 9, 'message': 'Invalid mail'})

			#Недопустимое имя
			if 'name' in x and not x['name'].isalpha():
				return dumps({'error': 10, 'message': 'Invalid name'})

			#Недопустимая фамилия
			if 'surname' in x and not x['surname'].isalpha():
				return dumps({'error': 11, 'message': 'Invalid surname'})

			try:
				id = db['users'].find().sort('id', -1)[0]['id'] + 1
			except:
				id = 1

			db['users'].insert({
				'id': id,
				'login': x['login'],
				'password': md5(bytes(x['pass'], 'utf-8')).hexdigest(),
				'mail': x['mail'],
				'name': x['name'].title() if 'name' in x else None,
				'surname': x['surname'].title() if 'surname' in x else None,
				'description': '',
				'rating': 0,
				'tokens': 500,
				'admin': 3,
				'transactions': [{
					'type': 2,
					'count': 500,
					'user': 0,
					'out': 0,
					'time': time.time(),
				}],
				'ladders': [],
			})

			token = generate()
			db['tokens'].insert({
				'token': token,
				'id': id,
				'time': time.time(),
			})

			return dumps({'error': 0, 'id': id, 'token': token})

#Авторизация
		elif x['method'] == 'profile.auth':
			mes = errors(x, (
				('login', True, str),
				('pass', True, str),
			))
			if mes: return mes

			x['login'] = x['login'].lower()

			#Неправильный логин
			if not len(list(db['users'].find({'login': x['login']}))):
				return dumps({'error': 5, 'message': 'Login does not exist'})

			i = db['users'].find_one({'login': x['login'], 'password': md5(bytes(x['pass'], 'utf-8')).hexdigest()})
			if i:
				id = i['id']

			#Неправильный пароль
			else:
				dumps({'error': 6, 'message': 'Invalid password'})

			token = generate()
			db['tokens'].insert({'token': token, 'id': id, 'time': time.time()})

			return dumps({'error': 0, 'id': id, 'token': token})

#Изменение личной информации
		elif x['method'] == 'profile.edit':
			mes = errors(x, (
				('token', True, str),
				('name', False, str),
				('surname', False, str),
				('description', False, str),
				('photo', False, str),
			))
			if mes: return mes

			if not user:
				return dumps({'error': 5, 'message': 'Invalid token'})

			i = db['users'].find_one({'id': user})

			if 'name' in x:
				#Недопустимое имя
				if not x['name'].isalpha():
					return dumps({'error': 6, 'message': 'Invalid name'})

				i['name'] = x['name'].title()

			if 'surname' in x:
				#Недопустимая фамилия
				if not x['surname'].isalpha():
					return dumps({'error': 7, 'message': 'Invalid surname'})

				i['surname'] = x['surname'].title()

			if 'description' in x:
				i['description'] = x['description']

			db['users'].save(i)

			if 'photo' in x:
				try:
					load_image('app/static/load/users', x['photo'], user)

				#Ошибка загрузки фотографии
				except:
					return dumps({'error': 8, 'message': 'Error uploading photo'})

			return dumps({'error': 0})

#Закрытие сессии
		elif x['method'] == 'profile.exit':
			mes = errors(x, (
				('token', True, str),
			))
			if mes: return mes

			i = db['tokens'].find_one({'token': x['token']})
			if i:
				db['tokens'].remove(i)
				return dumps({'error': 0})

			#Неправильный токен
			else:
				return dumps({'error': 5, 'message': 'Invalid token'})

#Получение категорий
# 		elif x['method'] == 'categories.gets':
# 			categories = []
# 			for i in db['categories'].find().sort('priority', -1): #{"$unwind": "$Applicants"}
# 				# print('!!!', i)
# 				# time.sleep(2)
# 				del i['_id']

# 				categories.append(i)
# 			return dumps(categories)

# db['categories'].insert({
# 	'id': 1,
# 	'parent': 0,
# 	'name': 'Раздел 1',
# 	'url': 'art',
# 	'priority': 50,
#	'plus': 'ladder',
# })

#Добавление курса
		elif x['method'] == 'ladders.add':
			mes = errors(x, (
				('token', True, str),
				('name', True, str),
				('description', True, str),
				('tags', True, list, str),
				#('category', True, int),
				('priority', False, int),
			))
			if mes: return mes

			try:
				id = db['ladders'].find().sort('id', -1)[0]['id'] + 1
			except:
				id = 1

			query = {
				'id': id,
				'user': user,
				'time': time.time(),
				'status': 1,
				'view': [user,],
				'like': [],
				'dislike': [],
				'comment': [],
				'priority': x['priority'] if 'priority' in x else 500,
				'steps': [{
					'name': 'You have read and agreed to Honor code?',
					'cont': '[Link to Honor code](/codex)',
					'options': ['Yes', 'No', 'Don\'t understand'],
					'answers': [1,],
					'theory': '[Link to Honor code](/codex)',
					'user': user,
				},],
			}

			for i in ('name', 'tags', 'description'): #, 'category'
				if i in x:
					query[i] = x[i]

			db['ladders'].insert(query)

			if 'preview' in x:
				try:
					load_image('app/static/load/ladders', x['preview'], id, x['file'].split('.')[-1] if 'file' in x else None)

				#Ошибка загрузки изображения
				except:
					return dumps({'error': 5, 'message': 'Error uploading image'})

			return dumps({'error': 0, 'id': id})

#Редактирование курса
		elif x['method'] == 'ladders.edit':
			mes = errors(x, (
				('token', True, str),
				('id', True, int),
				('name', False, str),
				('description', False, str),
				('tags', False, list, str),
				('priority', False, int),
			))
			if mes: return mes

			query = db['ladders'].find_one({'id': x['id']})

			#Отсутствует такой курс
			if not query:
				return dumps({'error': 5, 'message': 'Ladder does not exsist'})

			for i in ('name', 'description', 'tags', 'priority'): #'category'
				if i in x: query[i] = x[i]

			db['ladders'].save(query)

			if 'preview' in x:
				try:
					load_image('app/static/load/ladders', x['preview'], x['id'], x['file'].split('.')[-1] if 'file' in x else None)

				#Ошибка загрузки изображения
				except:
					return dumps({'error': 6, 'message': 'Error uploading image'})

			return dumps({'error': 0})

#Получение курсов #сделать выборку полей
		elif x['method'] == 'ladders.gets':
			mes = errors(x, (
				('count', False, int),
				('category', False, int)
			))
			if mes: return mes

			count = x['count'] if 'count' in x else None

			category = None
			if 'category' in x:
				category = [x['category'],]
				for i in db['categories'].find({'parent': x['category']}):
					category.append(i['id'])
				category = {'category': {'$in': category}}

			ladders = db['ladders'].find(category).sort('priority', -1)[0:count]

			return dumps({'error': 0, 'ladders': del_id(ladders)})

#Получение курса
		elif x['method'] == 'ladders.get':
			mes = errors(x, (
				('id', True, int),
			))
			if mes: return mes

			i = db['ladders'].find_one({'id': x['id']})

			if i:
				del i['_id']
				return dumps({'error': 0, 'ladder': i})

			#Несуществует такого курса
			else:
				return dumps({'error': 5, 'message': 'Ladder does not exsist'})

#Добавление шага #добавлять по id #менять местами
		elif x['method'] == 'step.add':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('name', True, str),
				('options', True, list, str),
				('answers', False, list, int),
				('cont', False, str),
				('theory', True, str),
			))
			if mes: return mes

			try:
				ladder = db['ladders'].find_one({'id': x['ladder']})
			except:
				return {'error': 5, 'message': 'Wrong id of ladder'}

			ladder['steps'].append({
				'name': x['name'],
				'cont': x['cont'] if 'cont' in x else '',
				'options': [i.strip() for i in x['options']],
				'answers': x['answers'] if 'answers' in x else [],
				'user': user,
				})

			db['ladders'].save(ladder)

			return dumps({'error': 0, 'id': len(ladder['steps'])-1})

#Изменение шага
		elif x['method'] == 'step.edit':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('step', True, int),
				('name', False, str),
				('options', False, list, str),
				('answers', False, list, int),
				('cont', False, str),
				('theory', False, str),
			))
			if mes: return mes

			try:
				ladder = db['ladders'].find_one({'id': x['ladder']})
			except:
				return dumps({'error': 5, 'message': 'Wrong invalid of ladder'})

			if len(ladder['steps']) > x['step']:
				for i in ('name', 'options', 'answers', 'cont', 'theory'):
					if i in x:
						if type(x[i]) == list and type(x[i][0]) == str:
							x[i] = [j.strip() for j in x[i]]
						ladder['steps'][x['step']][i] = x[i]
			else:
				return dumps({'error': 6, 'message': 'Wrong id of step'})

			db['ladders'].save(ladder)

			return dumps({'error': 0})

#Удаление шага
		elif x['method'] == 'step.delete':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('step', True, int),
			))
			if mes: return mes

			try:
				ladder = db['ladders'].find_one({'id': x['ladder']})
			except:
				return dumps({'error': 5, 'message': 'Wrong id of ladder'})

			if len(ladder['steps']) > x['step']:
				del ladder['steps'][x['step']]
			else:
				return dumps({'error': 6, 'message': 'Wrong id of step'})

			db['ladders'].save(ladder)

			return dumps({'error': 0})

#Получение ступени
		elif x['method'] == 'step.get':
			mes = errors(x, (
				('ladder', True, int),
				('step', True, int),
			))
			if mes: return mes

			i = db['ladders'].find_one({'id': x['ladder']})

			if i:
				if len(i['steps']) > x['step']:
					#del i['steps'][x['step']]['answers'] #для изменения

					req = db['users'].find_one({'id': i['steps'][x['step']]['user']})
					i['steps'][x['step']]['user'] = {
						'id': req['id'],
						'login': req['login'],
						'name': req['name'],
						'surname': req['surname'],
					}

					return dumps({'error': 0, 'step': i['steps'][x['step']], 'name': i['name'], 'tags': i['tags']})

				else:
					return dumps({'error': 6, 'message': 'Step does not exsist'})

			#Несуществует такого курса
			else:
				return dumps({'error': 5, 'message': 'Ladder does not exsist'})

#Проверка ответов
		elif x['method'] == 'step.check':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('step', True, int),
				('answers', True, list, int),
			))
			if mes: return mes

			i = db['ladders'].find_one({'id': x['ladder']})

			if i:
				if len(i['steps']) > x['step']:
					return dumps({'error': 0, 'correct': set(x['answers']) == set(i['steps'][x['step']]['answers'])})

				else:
					return dumps({'error': 6, 'message': 'Step does not exsist'})

			#Несуществует такого курса
			else:
				return dumps({'error': 5, 'message': 'Ladder does not exsist'})

#Проверка ответов
		elif x['method'] == 'step.study':
			mes = errors(x, (
				('token', True, str),
				('ladder', True, int),
				('step', True, int),
			))
			if mes: return mes

			i = db['ladders'].find_one({'id': x['ladder']})

			if i:
				if len(i['steps']) > x['step']:
					return dumps({
						'error': 0,
						'bot': {
							'price': 10,
						},
						'teachers': [],
						'users': [],
					})

				else:
					return dumps({'error': 6, 'message': 'Step does not exsist'})

			#Несуществует такого курса
			else:
				return dumps({'error': 5, 'message': 'Ladder does not exsist'})

#Получение пользователя
		elif x['method'] == 'users.get':
			mes = errors(x, (
				('id', True, int),
				#('login', False, str),
			))
			if mes: return mes

			i = db['users'].find_one({'id': x['id']} if 'id' in x else {'login': x['login']})

			if i:
				del i['_id']
				return dumps({'error': 0, 'user': i})

			#Несуществует такого человека
			else:
				return dumps({'error': 5, 'message': 'User does not exsist'})

#Получение экспертов
		elif x['method'] == 'experts.gets':
			mes = errors(x, (
				('sort', False, int),
			))
			if mes: return mes

			if 'sort' in x:
				users = db['users'].find().sort('rating.' + str(x['sort']), -1)
			else:
				users = db['users'].find()
			
			return dumps({'error': 0, 'users': del_id(users)})

#Отправить токены
		elif x['method'] == 'tokens.send':
			mes = errors(x, (
				('token', True, str),
				('count', True, int),
				('user', True, int),
			))
			if mes: return mes

			if x['count'] <= 0:
				return dumps({'error': 5, 'message': 'Invalid count of tokens'})

			now_time = time.time()

			i = db['users'].find_one({'id': user})

			if x['count'] > i['tokens']:
				return dumps({'error': 6, 'message': 'Not enough tokens!'})

			i['tokens'] -= x['count']
			i['transactions'].append({
				'type': 1,
				'count': x['count'],
				'user': x['user'],
				'out': 1,
				'time': now_time,
			})
			db['users'].save(i)

			i = db['users'].find_one({'id': x['user']})
			if i:
				i['tokens'] += x['count']
				i['transactions'].append({
					'type': 1,
					'count': x['count'],
					'user': user,
					'out': 0,
					'time': now_time,
				})
				db['users'].save(i)
			else:
				return dumps({'error': 6, 'message': 'Invalid id of user'})

			return dumps({'error': 0})

#Получение истории транзакций
		elif x['method'] == 'tokens.history':
			mes = errors(x, (
				('token', True, str),
			))
			if mes: return mes

			history = db['users'].find_one({'id': user})['transactions']

			for i, el in enumerate(history):
				history[i]['message'] = type_transactions[el['type']]
				if el['user'] > 0:
					history[i]['login'] = db['users'].find_one({'id': el['user']})['login']
				else:
					del history[i]['user']

			return dumps({'error': 0, 'history': history})

#Поиск
		elif x['method'] == 'search':
			pass

		else:
			return dumps({'error': 2, 'message': 'Wrong method'})

	#Серверная ошибка
	except:
		return dumps({'error': 1, 'message': 'Server error'})