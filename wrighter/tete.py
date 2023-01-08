def tete(*args):
    print(args)
    print(type(args))


tete(1, 2)


def add_request(*urls: str, label: str | None = None):
    print(urls)
    print(label)


add_request("a", "b", "c", "d", label="test")
