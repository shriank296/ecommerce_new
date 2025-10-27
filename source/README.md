example curl post command:

curl -X POST http://0.0.0.0:8081/users -H "Content-Type:application/json" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtaW50aUBleGFtcGxlLmNvbSIsInJvbGUiOiJBRE1JTiIsImV4cCI6MTc2MTUwMTA1NH0.Sh04MXDGppcqecxmiTGDM8m_xmXNakqFscM9xVGI-AM" -d '{"first_name":"Ankur", "last_name":"Shrivastava", "email":"cusatankur296@gmail.com", "phone":"9015", "address":{"street":"postal park"}, "role":"ADMIN", "created_by": "Ankur", "updated_by":"Ankur", "_password":"shrivastava@123"}'
