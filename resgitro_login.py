from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

app = FastAPI()
SECRET = "clave_secreta"

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    # si el usuario y contraseña son correctos
    if form.username == "cliente" and form.password == "123":
        token = jwt.encode({"sub": form.username}, SECRET, algorithm="HS256")
        return {"access_token": token}
    return {"error": "Credenciales inválidas"}