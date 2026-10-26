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