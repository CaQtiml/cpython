from regions import Region, is_local
from immutable import freeze, unfreezable, freezable, isfrozen
import sys


@freezable
class Foo:
    @freezable
    def bar(self):
        pass


def baz():
    return {"foo": "bar"}


freeze(baz()) # Create an instance of baz and freeze it
print(f"Is baz() frozen? {isfrozen(baz())}") # Create ANOTHER instance of baz and check if it's frozen (should be False)

f = Foo()
freeze(Foo.bar)
print(f"Is Foo frozen? {isfrozen(Foo)}")
print(f"Is Foo.bar frozen? {isfrozen(Foo.bar)}")
print("-------------------------")
f = Foo()
freeze(f.bar)
print(f"Is f.bar frozen? {isfrozen(f.bar)}")
print(f"Is f frozen? {isfrozen(f)}")
print(f"Is Foo frozen? {isfrozen(Foo)}")