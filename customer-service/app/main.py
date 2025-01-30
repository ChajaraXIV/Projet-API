import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date
from .message_broker import AMQPBroker

# Initialize FastAPI
app = FastAPI()

# Database Configuration
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# RabbitMQ Configuration
RABBITMQ_DEFAULT_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_DEFAULT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")

# Initialize the broker
broker = AMQPBroker(host=RABBITMQ_HOST, user=RABBITMQ_DEFAULT_USER, password=RABBITMQ_DEFAULT_PASS)
broker.connect()

# Connect to PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=5432,
        cursor_factory=RealDictCursor
    )

# Customer Model
class Customer(BaseModel):
    username: str
    user_id: int
    firstname: str
    lastname: str
    birth_date: date



# Routes
@app.get("/")
def read_root():
    return {"message": "Welcome to Customer Service"}

# Add a New Customer
@app.post("/customers/add")
def add_customer(customer: Customer):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """
            INSERT INTO customers (username, user_id, firstname, lastname, birth_date)
            VALUES (%s, %s, %s, %s, %s) RETURNING username
            """,
            (customer.username, customer.user_id, customer.firstname, customer.lastname, customer.birth_date)
        )
        conn.commit()

        return {"message": "Customer added successfully", "username": customer.username}

    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username already exists.")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        cur.close()
        conn.close()

# Get All Customers
@app.get("/customers/all")
def get_all_customers():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM customers ORDER BY created_at DESC")
        customers = cur.fetchall()
        
        if not customers:
            raise HTTPException(status_code=404, detail="No customers found")
        
        return {"customers": customers}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        cur.close()
        conn.close()

# Get a Single Customer by username
@app.get("/customers/{username}")
def get_customer(username: str):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM customers WHERE username = %s", (username,))
        customer = cur.fetchone()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return customer

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()

# Update a Customer by username
@app.put("/customers/update/{username}")
def update_customer(username: str, customer: Customer):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if customer exists before updating
        cur.execute("SELECT username FROM customers WHERE username = %s", (username,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")

        cur.execute(
            """
            UPDATE customers 
            SET firstname = %s, lastname = %s, birth_date = %s, updated_at = CURRENT_TIMESTAMP
            WHERE username = %s
            """,
            (customer.firstname, customer.lastname, customer.birth_date, username)
        )
        conn.commit()

        return {"message": "Customer updated successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()

# Delete a Customer by username
@app.delete("/customers/delete/{username}")
def delete_customer(username: str):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if customer exists before deleting
        cur.execute("SELECT username FROM customers WHERE username = %s", (username,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")

        cur.execute("DELETE FROM customers WHERE username = %s", (username,))
        conn.commit()
        
        return {"message": "Customer deleted successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()
