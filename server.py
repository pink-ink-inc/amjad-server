import flask
import redis
import datetime
import json

redis = redis.StrictRedis(host = 'redis-amjad-01')
app = flask.Flask(__name__)

@app.route('/api/test')
def test():
    return 'test'

@app.route('/api/repr/<key>')
def repr_route(key):
    return json.dumps(repr(key), indent=2)

@app.route('/api/render/<key>')
def render_route(key):
    return render(key)

def render(key):
    key_type = redis.type(key)
    strategies = {
              'string': 'repr_string'
            , 'list': 'render_list'
            , 'set': 'repr_set'
            , 'zset': 'repr_zset'
            , 'hash': 'repr_hash'
            , 'none': 'repr_none'
            }
    return strategy ( strategies, key_type, key )

def repr(key):
    key_type = redis.type(key)
    strategies = {
              'string': 'repr_string'
            , 'list': 'repr_list'
            , 'set': 'repr_set'
            , 'zset': 'repr_zset'
            , 'hash': 'repr_hash'
            , 'none': 'repr_none'
            }
    return strategy ( strategies, key_type, key )

def strategy (strategies, key, value):
    for each in strategies:
        if key == each:
            try:
                return globals()[strategies[each]] (value)
            except AttributeError:  # That is, the function name is not present in the namespace.
                pass 
    return False

def definite_strategy (strategies, key, value, default_strategy):
    for each in strategies:
        if key == each:
            try:
                return strategies[each] (value)
            except NameError:  # That is, the function name is not present in the namespace.
                pass
    return strategies[default_strategy] (value)

def repr_string(key):
    return redis.get(key)

def repr_list(key):
    strategies = {
              '::': repr
              , ':-': lambda x: [ repr(each) for each in redis.keys(x + ':*') ]
              , '': str
            }
    return [ definite_strategy (strategies, key[0:2], key, '')
            for key in redis.lrange ( key, 0, -1 ) ]

def repr_hash(key):
    return [ ]

def repr_none(key):
    return 'none here'

def render_list(key):
    strategies = {
              '::': render
              , ':-': lambda x: '\n'.join([ render(each) for each in redis.keys(x + ':*') ])
              , '': str
            }
    return '\n'.join ([ definite_strategy (strategies, key[0:2], key, '')
            for key in redis.lrange ( key, 0, -1 ) ])


if __name__ == '__main__':
    app.run(host = '0.0.0.0')
