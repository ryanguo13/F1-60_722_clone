import adsk.core
def run(c):
    app = adsk.core.Application.get()
    n = 0
    for d in list(app.documents):
        try:
            d.close(False)
            n += 1
        except Exception as e:
            print("close fail", d.name, e)
            break
    print("closed", n, "remaining", app.documents.count)
