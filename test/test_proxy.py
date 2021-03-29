    


class B:
    pass


class A:
    __instance = None

    tttt = 1
                
    def __init__(self):
        self.a = 1 
            
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(A,cls).__new__(cls)
            for k, v in cls.__instance.__dict__:
                B.__setattr__(B(), k,v)

    
            
a = A()
