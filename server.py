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

def repr_string(key):
    return redis.get(key)

def repr_list(key):
    return [ repr(key) if key[0:2] == '::' else key for key in redis.lrange ( key, 0, -1 ) ]

def repr_hash(key):
    return [ ]

def repr_none(key):
    return 'none here'


# @app.route('/redis//<id_>/counters')
# def counters(id_):
#     now = datetime.datetime.now()
#     key_day  = 'nginx-access:{}:{:04d}{:02d}{:02d}'       .format(id_, now.year, now.month, now.day)
#     key_hour = 'nginx-access:{}:{:04d}{:02d}{:02d}{:02d}' .format(id_, now.year, now.month, now.day, now.hour)
#     # return "meow"
# 
#     return '{} / {} / {}'.format (
#               redis.llen (key_hour)
#             , redis.llen (key_day)
#             , sum ( [ redis.llen (key) for key in redis.keys ('nginx-access:{}:????????' .format(id_)) ] )
#             )


if __name__ == '__main__':
    app.run(host = '0.0.0.0')
