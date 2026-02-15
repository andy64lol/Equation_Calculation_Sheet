import ecs

# ----------------------------
# Load ECS / ECSP sheets
# ----------------------------
ecs.add_sheet("constants")   # loads constants.ecs
ecs.add_sheet("physics")     # loads physics.ecsp
ecs.add_sheet("main")        # loads main.ecs

# ----------------------------
# Access basic ECS variables
# ----------------------------
print("x =", ecs.get("x"))           # 48
print("x2 =", ecs.get("x2"))         # solved quadratic
print("r1 =", ecs.get("r1"))         # 2
print("x3 =", ecs.get("x3"))         # 4
print("a =", ecs.get("a"))           # 2
print("b =", ecs.get("b"))           # 2304
print("c1 =", ecs.get("c1"))         # 1.23e10
print("d =", ecs.get("d"))           # -4
print("e =", ecs.get("e"))           # 8
print("f =", ecs.get("f"))           # ≈0.33

# ----------------------------
# Access ECSP block variables
# ----------------------------
print("spring F =", ecs.get("spring.F"))                 # 20
print("spring K =", ecs.get("spring.K"))                 # 4
print("spring extension =", ecs.get("spring.L_final") - ecs.get("spring.L_init"))  # 5
print("gas v2 =", ecs.get("gas.v2"))                     # solved value

# ----------------------------
# Access imported ECS constants
# ----------------------------
print("gravity =", ecs.get("gravity"))   # 9.8
print("pi =", ecs.get("pi"))             # 3.14159

# ----------------------------
# Dynamically defining a variable
# ----------------------------
predefined_variable = 7
ecs.define_var(predefined_variable)     # internally defines X = 8
print("X =", ecs.get("X"))              # 8

# Using it in another calculation
ecs.define_var(ecs.get("X") + 2)       # X = 10
print("Updated X =", ecs.get("X"))      # 10
