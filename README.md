# Springboard-Capstone-Project-1
For my first capstone project I decided to create a stock trading multiplayer game that uses real time stock data, 
and provides functionality for users to buy, sell, and see detailed information about stocks, in a competitive environment against other users.

Core Dependancies Used:
* Flask
* SQLAlchemy
* Jinja2
* Postgresql

## Schema
---
![schema](util/schema.PNG)

<em>Made using dbdesigner.net, a overall summary of the actual schema</em>
* A complete definition of the database is found in [models.py](/models.py) using SQLAlchemy models to represent the tables stored in Postgresql

## API:
---
Yahoo finance rapid-api: https://rapidapi.com/apidojo/api/yahoo-finance1
* This api is used for getting realtime stock information. Config variables stored in the database in the app_config table toggle when stocks are updated in view functions defined in [app.py](/app.py).





