Run the following command using the git bash terminal

```source venv/Scripts/activate```

After activating the virtual enviroment, run the main.py file with the following command:

```uvicorn main:app --reload```

Run ```docker build -t calculadora-fast-api .``` to build the docker container

Run ```docker run -d -p 8060:8000 calculadora-fast-api``` to actually run the app on Docker with the port 8000 fowarded to the 8060.