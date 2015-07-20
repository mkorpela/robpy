from judas import kw, test

@kw
def kw1():
    print 'keyword'

@kw
def kw2():
    print 'keyword2'
    kw1()

@kw
def failing():
    print 'this fails'
    1/0

@test
def t1():
    kw1()
    kw2()
    failing()

@test
def t2():
    kw2()