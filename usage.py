class A:
    x = 5

    @classmethod
    def set(cls, x):
        cls.x = x


A.set(65)
print(A.x)
