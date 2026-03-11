import random
import os

def get_random_value(x):
    if not isinstance(x, list):
        return x
    else:
        if len(x) > 1:
            if isinstance(x[0], int):
                return random.randint(x[0], x[1])
            elif isinstance(x[0], float):
                return random.uniform(x[0], x[1])
            else:
                NotImplementedError("Type not suitable for random number generator!")
        else:
            return x[0]

def get_rgba_value(x):
    assert isinstance(x, list)
    assert 4 == len(x)

    return [get_random_value(i) for i in x]

def get_files_with_ext(self, path, ext=".json"):
    files = []
    for file in os.listdir(path):
        if file.endswith(ext):
            files.append(os.path.join(path, file))

    return files