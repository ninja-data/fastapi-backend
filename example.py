import json

# JSON string with escaped quotes
json_string = "{\"name\":\"name\",\"surname\":\"surname\",\"email\":\"mejej9@bk.ru\",\"phone\":\"+994708156159\",\"password\":\"123456789\"}"

# Parse the JSON string into a dictionary
parsed_data = json.loads(json_string)

# Print the dictionary
print(parsed_data)
