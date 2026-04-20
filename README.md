# Garden System
A prototype for managing a **community garden**.

## Features
- Plot renting  
- Tool sharing  
- Seed bank  
- Volunteer shifts  
- Simple marketplace  

## Usage
```python
garden = Garden(150, 80).build()
member = garden.join_member("Me")
member.add_credits(200)