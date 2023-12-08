from dataclasses import dataclass


# Define a base class named Vehicle
@dataclass
class Vehicle:
    model: str

    def display(self) -> None:
        print(f"Vehicle model: {self.model}")


# Define two subclasses for Vehicle: Car and Boat
class Car(Vehicle):
    def display(self) -> None:
        print(f"Car model: {self.model}")


class Boat(Vehicle):
    def display(self) -> None:
        print(f"Boat model: {self.model}")

class Plane(Vehicle):
    def display(self) -> None:
        print(f"Plane model: {self.model}")
        
class VehicleRegistry[V: Vehicle]:
    def __init__(self) -> None:
        self.vehicles: list[V] = []

    def add_vehicle(self, vehicle: V) -> None:
        self.vehicles.append(vehicle)

    def display_all(self) -> None:
        for vehicle in self.vehicles:
            vehicle.display()

# A non-generic type alias
type IntOrStr = int | str

# A generic type alias
type ListOrSet[T] = list[T] | set[T]

class Box[T]:
    def __init__(self, item: T):
        self.item = item

    def get_item(self) -> T:
        return self.item

    def set_item(self, new_item: T) -> None:
        self.item = new_item

# generic function example
def get_first_item[T](items: list[T]) -> T:
    return items[0]

def main() -> None:
    # For integers
    int_box = Box(123)
    int_item = int_box.get_item()
    print(int_item)  # Outputs: 123

    # For strings
    str_box = Box("Hello, Generics!")
    str_item = str_box.get_item()
    print(str_item)  # Outputs: Hello, Generics!

    # For lists
    list_box = Box([1, 2, 3])
    list_item = list_box.get_item()
    print(list_item)  # Outputs: [1, 2, 3]

    # Generic function
    first_item = get_first_item([1, 2, 3])
    print(first_item)  # Outputs: 1


if __name__ == "__main__":
    main()