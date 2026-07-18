from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/test")
def test():
    return {"msg": "Hello from Vercel Python"}
