
There is a simple rule to fetch the data.
========================================

Obviously everything schema could be kept in a keylist '{key}:*', where key is say an integer
counter.  Then, we have a 'fetch key start end' method... that takes this key and iterates over
the elements, assigning each to a hash... so far this is a mapping from redis to a python
structure.

Then, we apply a map of 'render template data' method that performs the obvious transformation.

Redis:
--------------------

key_name:
    - template: template
    - type: either terminal or non-terminal
    - either :list or something else.

list:
    - :data-hash

