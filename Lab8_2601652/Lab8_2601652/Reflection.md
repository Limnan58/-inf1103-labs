# INF1103 Lab 6 – Reflection Questions

**1. What is the difference between a class and an object?**
A class is a blueprint that defines what data (attributes) and behaviour (methods) something will have. An object is a specific instance created from that blueprint with its own values. `Product` is the class; `Product("P001", "Laptop", 1200.00, 15)` is an object.

**2. Why is Product a suitable class for this system?**
Product is a clear "noun" in the system. Every product has the same kind of data (ID, name, price, stock) and the same operations (update stock, display itself), so grouping them into one class removes repeated dictionary handling and keeps related data and behaviour together.

**3. What data belongs inside a Product object?**
Its product ID, name, price and stock quantity – stored as the private attributes `__product_id`, `__name`, `__price` and `__stock`.

**4. Why should the Product class manage its own stock rather than the main program directly changing it?**
So the rules for valid stock live in one place. `update_stock()` rejects negative or non-whole-number values, so no other part of the program can put the product into an invalid state. If the rules change later, only the Product class needs editing.

**5. What does encapsulation mean in your program?**
Product and Inventory keep their data private (`__stock`, `__products`, etc.). Outside code reads values through read-only properties (`product.stock`) and changes them only through public methods (`update_stock()`, `add_product()`). `Inventory.get_products()` returns a copy of the list, so the internal list cannot be replaced from outside.

**6. What is the responsibility of the Product class?**
To represent and manage a single product: store its information and control how that information changes.

**7. What is the responsibility of the Inventory class?**
To manage a collection of Product objects: add products (rejecting duplicate IDs), search for products, update a product's stock through the product itself, and display all products.

**8. How does separating these responsibilities demonstrate the Single Responsibility Principle?**
Each part has one reason to change: Product changes if product rules change, Inventory changes if the way products are stored or searched changes, FileHandler changes if the file format changes, and the main program changes if the menu or user input changes. None of them does another's job – e.g. Product never reads files, and Inventory never asks the user for input.

**9. What information does the main program need to know about a Product?**
Only its public interface: how to create one (`Product(id, name, price, stock)`), how to read its ID, name, price and stock, and that it can `update_stock()` and `display_information()`.

**10. What information about the internal implementation of Product does the main program not need to know?**
How the attributes are stored (the private `__` names and name mangling), how validation is done inside `update_stock()` and `__init__`, or how the display string is formatted. The internals could change without the main program needing any changes.
