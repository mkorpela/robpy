from robpy import kw, test

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

@test(tags=['foo', 'bar'])
def test_combined():
    kw1()
    kw2()
    failing()

@test
def test_failing_from_keyword():
    failing()

@test
def test_failing_from_test():
    print 'i am failing'
    1/0

@test
def test_keyword_call():
    kw2()


@test
def test_print_without_keywords():
    print 'hello test'