import flask
import redis
import datetime
import json

redis = redis.StrictRedis(host = 'redis-amjad-01')
app = flask.Flask(__name__)

@app.route('/api/test')
def test():
    return 'test'

@app.route('/api/echo', methods = ['GET', 'POST'])
def echo():
    return json.dumps ( definite_strategy (
                {
                      'GET': lambda x: flask.request.args
                    , 'POST': lambda x: flask.request.data
                }
                , flask.request.method
                , None
                )
            )

@app.route('/api/echo-json', methods = ['POST'])
def echo_json():
    print type(flask.request.json)
    return json.dumps ( flask.request.json, indent = 2 )

@app.route('/api/repr/<key>')
def repr_route(key):
    return json.dumps(repr(key), indent=2)

@app.route('/api/show/<key>')
def show_key(key):
    return json.dumps ( definite_strategy (
        {
              'string': lambda x: redis.get(x)
            , 'hash': lambda x: redis.hgetall(x)
            , 'list': lambda x: redis.lrange(x,0,-1)
        }
        , redis.type(key)
        , key
        ) )

@app.route('/api/render/<key>')
def render_route(key):
    return render(key)

@app.route('/api/keys/<key>')
def list_keys(key):
    return json.dumps (redis.keys(key), indent=2)

@app.route('/api/add/<key>', methods = ['POST'])
def add_key(key): return add_key_f(key)

def add_key_f(key):
    try:
        strategies = {
              'string': lambda (key, value): redis.set ( key, value )
            , 'hash': lambda (key, value): redis.hmset (key, value)
            , 'list': lambda (key, value): [redis.rpush (key, x) for x in value] 
            }

        print (strategies)
        print flask.request.json

        return json.dumps(definite_strategy (strategies, flask.request.json['kind'], (key, flask.request.json['value']) ), indent = 2)
    except Exception as e:
        return str(e)

@app.route('/api/del/<key>', methods = ['POST'])
def del_key(key): return del_key_f(key)

def del_key_f(key):
    return json.dumps ( redis.delete(key), indent = 2 )

@app.route('/api/rewrite/<key>', methods = ['POST'])
def rewrite(key):
    if redis.type(key) == 'list':
        del_key_f(key)
    return add_key_f(key)


@app.route('/api/flatten/<key>')
def flatten(key):
    def f(key):
        return ( definite_strategy (
            { 'list': lambda x: reduce(lambda x,y: x+y, [ f(a) if a[0:2] == '::' or a[0:2] == ':#' else [a] for a in redis.lrange(x, 0, -1) ])
                  , 'hash': lambda x: [redis.hgetall(x)]
                  , 'none': lambda x: []
                  , 'string': lambda x: [ f(a) if a[0:2] == '::' else a for a in [redis.get(x)] ]
                  }
                  , redis.type(key)
                  , key
                  , default_strategy = 'hash'
                  )
                )

    return json.dumps (f(key)
            , indent = 2
            )


def render(key):
    # print 'rendering ' + key
    key_type = redis.type(key)
    strategies = {
              'string': 'repr_string'
            , 'list': 'render_list'
            , 'set': 'repr_set'
            , 'zset': 'repr_zset'
            , 'hash': 'render_hash'
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
    return {
              'key': key
            , 'repr': strategy ( strategies, key_type, key )
            , 'type': redis.type(key)
        }

def strategy (strategies, key, value):
    for each in strategies:
        if key == each:
            # print 'chosen strategy ' + strategies[each]
            try:
                return globals()[strategies[each]] (value)
            except AttributeError:  # That is, the function name is not present in the namespace.
                pass 
    return False

def definite_strategy (strategies, key, value, default_strategy=''):
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
              , ':#': repr
              , ':!': repr
              , ':-': lambda x: [ repr(each) for each in redis.keys(x + ':*') ]
              , '': str
            }
    return [ definite_strategy (strategies, key[0:2], key, '')
            for key in redis.lrange ( key, 0, -1 ) ]

def repr_hash(key):
    hash_ = redis.hgetall(key)
    if 'template' in hash_.keys():
        return dict ( [ (key, repr(hash_[key])) for key in hash_.keys() ] )
    else:
        return hash_

def repr_none(key):
    return ''

def render_list(key):
    strategies = {
                '::': render
              , ':#': render
              , ':-': lambda x: '\n'.join([ render(each) for each in redis.keys(x + ':*') ])
              , '': str
            }
    return '\n'.join ([ definite_strategy (strategies, key[0:2], key, '')
            for key in redis.lrange ( key, 0, -1 ) ])

def render_hash(key):

    def intermix (template, values):
        for value in values:
            for template_string in template:
                if template_string[0:2] == ':!':
                    s = redis.hget ( value, template_string )
                    if s[0:2] == '::':
                        yield render (s)
                    else:
                        yield s
                else:
                    yield template_string
        # That would be all.

    def render_hash_template(key):
        return '\n'.join ( intermix (
                  redis.lrange ( redis.hget ( key, 'template' ), 0, -1 )
                , redis.lrange ( redis.hget ( key, 'values' ), 0, -1 )
                ) )

    def render_hash_values(key):
        return redis.hgetall(key)

    return definite_strategy (
                { ':#': render_hash_template
                , ':@': render_hash_values
                , '': str
                }
                , key[0:2], key)


if __name__ == '__main__':
    app.run(host = '0.0.0.0')
