def run(*args):
    print(args)


run("hello", "this", "is")

"""
def do():
    try:
        nums = [1,2,3]
        print(nums[10])
    except Exception as error:
        print("do error")
        raise ValueError()
    finally:
        print("do finally block reached")

try:
    do()
    print("after do")
except Exception as error:
    print("MAIN EXCEPTION BLOCK HIT")
    
from pathlib import Path
PROJECT_DIR = Path.home() / "cua-learning"
print(PROJECT_DIR)
print(type(PROJECT_DIR))

# ----------
print("starting program")
# raise SystemExit(1)
# print("this won't execute")
from exceptions import ExecutorError
def doo():
    try:
        nums = [1,2,3]
        print(nums[20])
    except Exception as error:
        # raise ExecutorError(str(error), "path/here/ok") from error
        print('lol')
    return 10
    
try:
    res = doo()
    print(f"$$$$ {res}")
except ExecutorError as error:
    print(type(error))
    print(type(error).__name__)
    print(str(error))
    print(error.__context__)
"""