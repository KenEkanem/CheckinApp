
Setting the FLASK_APP environment variable is essential for Flask to locate and run your application
Setting the Variable:


- Linux/Mac
```export FLASK_APP=app.py```

- Windows (cmd)
```set FLASK_APP=app.py```


#### - Install pm2 globally
```npm install pm2 -g``` (node must be installed)
or

#### Install Requirements
```pip install requirements.txt``` (requirements using ```pip freeeze```)


#### Start the app
```pm2 start app.py```
