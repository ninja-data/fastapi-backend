import phonenumbers
from phonenumbers import geocoder

x = phonenumbers.parse("+994553753758")

region = geocoder.description_for_number(x, 'en')
print(region)

