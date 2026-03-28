from werkzeug.datastructures import ImmutableMultiDict
from urllib.parse import urlencode
data = ImmutableMultiDict([
    ('level[]', 'ELEMENTARY'), 
    ('name_of_school[]', 'Test School'), 
    ('period_from[]', '2010'), 
    ('period_to[]', '2014')
])

d2 = {}
d2.update(data.to_dict(flat=False))

print("school:", d2.get('name_of_school[]'))
print("level:", d2.get('level[]'))
