from regions import Region, is_local
from immutable import freeze
from enum import Enum

class A: pass
# freeze(A())

def disable_optimization(region, obj):
    region.re1 = next(obj)
    next(obj)

# r = Region()
# input("Press Enter to create objects...")
# print(f"Region r: {r}")
# r.a = A()
# r.b = A()
# r.c = A()
# r.d = A()
# r.e = A()


#------------------Problem with LRC should not be increases------------------
# print(f"Region r: {r}")
# r.arr = [r.a, r.b]
# print(f"Region r after creating arr: {r}")
# # input("Press Enter to create enum...")
# r.it_arr = iter(r.arr)
# print(f"Region r after creating iterator: {r}")
# # input("Press Enter to create enum...")
# obj = enumerate(r.it_arr) # LRC +1 since obj points to r.it_arr
# print(f"Region r after creating enum: {r}")
# input("Press Enter to create enum...")
# x = next(obj)
# print(f"Region r after getting next from enum: {r}")
# input("Press Enter to move enum...")
# r.re2 = x
# print(f"Region r after getting next from enum: {r}")
# r.y = next(obj)
# print(f"Region r after getting next from enum: {r}")
# x = None
# print(f"Region r after deleting re1: {r}")
# r.y = None
# print(f"Region r after deleting re2: {r}")
# obj = None
# print(f"Region r after deleting obj: {r}")

#------------------Problem with LRC not being decreased------------------
# print(f"Region r: {r}")
# r.arr = [r.a, r.b, r.c, r.d]
# print(f"Region r after creating arr: {r}")
# # input("Press Enter to create enum...")
# r.it_arr = iter(r.arr)
# print(f"Region r after creating iterator: {r}")
# # input("Press Enter to create enum...")
# obj = enumerate(r.it_arr) # LRC +1 since obj points to r.it_arr
# print(f"Region r after creating enum: {r}")
# # input("Press Enter to create enum...")
# r.re1 = next(obj)
# print(f"{is_local(obj)}")
# print(f"Region r after getting next from enum: {r}")
# # input("Press Enter to create enum...")
# re2 = next(obj)
# print(f"Region r after getting next from enum: {r}")
# r.re3 = next(obj)
# print(f"Region r after getting next from enum: {r}")
# re4 = next(obj)
# print(f"Region r after getting next from enum: {r}")
# r.re1 = None 
# print(f"Region r after deleting re1: {r}")
# re2 = None
# print(f"Region r after deleting re2: {r}")
# r.re3 = None
# print(f"Region r after deleting re3: {r}")
# re4 = None
# print(f"Region r after deleting re4: {r}")
# obj = None
# print(f"Region r after deleting obj: {r}")

#------------------Problem with GC------------------
# print(f"Region r: {r}")
# r.arr = [r.a, r.b]
# print(f"Region r after creating arr: {r}")
# # input("Press Enter to create enum...")
# r.it_arr = iter(r.arr)
# print(f"Region r after creating iterator: {r}")
# input("Press Enter to create enum...")
# r.obj = enumerate(r.it_arr) # LRC +1 since obj points to r.it_arr
# print(f"Region r after creating enum: {r}")
# input("Press Enter to create enum...")
# re1 = next(r.obj)
# print(f"{is_local(r.obj)}")
# print(f"Region r after getting next from enum: {r}")
# input("Press Enter to create enum...")
# r.re2 = next(r.obj)
# print(f"Region r after getting next from enum: {r}")


# print(f"Region r: {r}")
# r.arr = [r.a, r.b, r.c, r.d, r.e]
# print(f"Region r after creating arr: {r}")
# # input("Press Enter to create enum...")
# r.it_arr = iter(r.arr)
# print(f"Region r after creating iterator: {r}")
# # input("Press Enter to create enum...")
# obj = enumerate(r.it_arr) # LRC +1 since obj points to r.it_arr
# print(f"Region r after creating enum: {r}")
# input("Press Enter to create enum...")
# re = next(obj)
# print(f"Region r after getting next from enum: {r}")
# r.re2 = next(obj)
# print(f"Region r after getting next from enum: {r}")
# re3 = next(obj)
# print(f"Region r after getting next from enum: {r}")
# r.re4 = next(obj)
# print(f"Region r after getting next from enum: {r}")

r1 = Region()
r2 = Region()
print(f"Region r1: {r1}")
print(f"Region r2: {r2}")
r1.a = A()
r1.b = A()
r1.arr = [r1.a, r1.b]
print(f"{r1.arr}")
r1.it = iter(r1.arr)
print(f"Region r1 after creating arr and iterator: {r1}")
print(f"Region r2 after creating arr and iterator in r1: {r2}")
obj = enumerate(r1.it)
print(f"Region r1 after creating enum: {r1}")
print(f"Region r2 after creating enum in r1: {r2}")
input("Press Enter to move enum result into r2...")
# next_obj = next(obj)
# r2.obj = next_obj
# r2.obj = next(obj)
try:
    # r2.obj = next_obj
    r2.obj = next(obj)
except Exception as e:
    print(f"Error: {e}")

print(f"Region r1 after trying to move enum result into r2: {r1}")
print(f"Region r2 after trying to move enum result into r2: {r2}")
re1 = next(obj)
print(f"{re1}")
print(f"Region r1 after trying to move enum result into r2: {r1}")
print(f"Region r2 after trying to move enum result into r2: {r2}")

# # next_obj = None
# obj = None
# print(f"Region r1 after deleting obj and next_obj: {r1}")
# print(f"Region r2 after deleting obj and next_obj: {r2}")