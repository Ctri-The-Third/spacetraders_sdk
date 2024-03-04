import straders_sdk.constants as st_c


manufactured_by = st_c.MANUFACTURED_BY
# takes the form {["str":["str","str",...]]}

manufactures = {}
for k, v in manufactured_by.items():
    # k = the thing being manufactured
    # v = a list of strings that manufacture it
    for item in v:
        if item in manufactures:
            manufactures[item].append(k)
        else:
            manufactures[item] = [k]

print("MANUFACTURES = {")
for k, v in manufactures.items():
    print(f'"{k}": {v},')
print("}")
