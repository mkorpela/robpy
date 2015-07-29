from judas import kw, test

@test
def foo():
    bar()

@kw
def bar():
    print 'bar'