from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to Customer Service"}

@app.post("/customers")
def create_customer(customer: dict):
    return {"message": f"Customer {customer.get('name')} created successfully"}
