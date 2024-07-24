import os

if os.path.exists('.env'):
    with open('.env', 'r') as fin:
        while True:
            line = fin.readline()
            if line == "":
                break

            sline = line.strip()
            if not sline:

                continue

            k,v = sline.split('=', maxsplit=1)

            if v[0] == v[-1] and v[0] in ("'", '"'):
                v = v[1:-2]

            os.environ.update({k: v})
