from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Union
import asyncio

# from database import *
from database import *
import uvicorn

app = FastAPI()



class RegisterRequest(BaseModel):
    email: str
    login: str
    password: str

class LoginRequest(BaseModel):
    login: str
    password: str

class AuthResponse(BaseModel):
    user_id: int

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8081",
    "http://127.0.0.1:5500",
    "http://45.153.189.82:3001",
    "exp://109.194.206.48:8081"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных для расчетов
class TaxCalculationRequest(BaseModel):
    tax_type: int 
    operation: int 
    amount: float
    custom_rate: float
    new: int

class TaxCalculationResponse(BaseModel):
    id: int
    tax_type: int
    operation: int
    amount: float
    calculated_tax: float
    custom_rate_used: float


def calculate_ndfl(request: TaxCalculationRequest):
    if request.new == 1:

        tax = 0.0
        remaining_income = request.amount

        if remaining_income > 0:
            taxable_income = min(2400000, remaining_income)
            tax += round(taxable_income * 0.13)
            remaining_income -= taxable_income

        if remaining_income > 0:
            taxable_income = min(2600000, remaining_income)
            tax += round(taxable_income * 0.15)
            remaining_income -= taxable_income

        if remaining_income > 0:
            taxable_income = min(15000000, remaining_income)
            tax += round(taxable_income * 0.18)
            remaining_income -= taxable_income

        if remaining_income > 0:
            taxable_income = min(30000000, remaining_income)
            tax += round(taxable_income * 0.20) 
            remaining_income -= taxable_income

        if remaining_income > 0:
            tax += round(remaining_income * 0.22)  

        return tax

    else: 
        tax = 0.0
        remaining_income = request.amount

        if remaining_income > 0:
            taxable_income = min(5000000, remaining_income)
            tax += round(taxable_income * 0.13) 
            remaining_income -= taxable_income

        if remaining_income > 0:
            tax += round(remaining_income * 0.15) 

        return tax



def calculate_income_from_property(request: TaxCalculationRequest):
    if request.new == 0: 
        return round(request.amount * 0.13) 

    tax_first_part = min(request.amount, 2400000) * 0.13
    remaining_amount = max(0, request.amount - 2400000) 

    tax_second_part = remaining_amount * 0.15


    total_tax = tax_first_part + tax_second_part

    return round(total_tax)

def calculate_dividends(request: TaxCalculationRequest):
    if request.new == 0: 
        return round(request.amount * 0.13) 

    tax_first_part = min(request.amount, 2400000) * 0.13
    remaining_amount = max(0, request.amount - 2400000) 

    tax_second_part = remaining_amount * 0.15


    total_tax = tax_first_part + tax_second_part

    return round(total_tax)


def calculate_ndfl_for_non_residents(request: TaxCalculationRequest):
    if request.operation == 1:
        original_amount = request.amount / (1 - 0.30)
        return round(original_amount * 0.30)

    else:
        return round(request.amount * 0.30)

def calculate_winnings(request: TaxCalculationRequest):
    if request.operation == 1:
        amount_before_tax = request.amount / (1 - 0.35)
        return round(amount_before_tax * 0.35)

    return request.amount * 0.35

def calculate_custom_rate(request: TaxCalculationRequest):
    if request.operation == 1:
        if request.custom_rate is None:
            raise HTTPException(status_code=400, detail="Не указана ставка налога.")

        amount_before_tax = request.amount / (1 - (request.custom_rate / 100))
        return round(amount_before_tax * (request.custom_rate / 100)) 

    if request.custom_rate is None:
        raise HTTPException(status_code=400, detail="Не указана ставка налога.")
    return request.amount * (request.custom_rate / 100)


@app.post("/raschet/{id}")
async def calculate_tax(id: int, request: TaxCalculationRequest):
    print(request)
    match request.tax_type:
        case 1:
            calculated_tax = calculate_ndfl(request)
        case 2:
            calculated_tax = calculate_dividends(request)
        case 3:
            calculated_tax = calculate_ndfl_for_non_residents(request)
        case 4:
            calculated_tax = calculate_winnings(request)            
        case 5:
            calculated_tax = calculate_custom_rate(request)
        case 6:
            calculated_tax = calculate_income_from_property(request)

    await db.record_calculation(
        user_id=id,
        tax_type=request.tax_type,
        operation=request.operation,
        amount=request.amount,
        new=request.new,
        total=calculated_tax
    )
            
            

    return TaxCalculationResponse(
        id=id,
        tax_type=request.tax_type,
        operation=request.operation,
        amount=request.amount,
        calculated_tax=calculated_tax,
        custom_rate_used=request.custom_rate
    )

@app.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):

    user = await db.create_user(request.email, request.login, request.password)
    return AuthResponse(user_id=user)

@app.post("/auth", response_model=AuthResponse)
async def auth(request: LoginRequest):
    user = await db.authenticate_user(request.login, request.password)
    if user == -1:
        raise HTTPException(status_code=400, detail="Invalid login or password")
    return AuthResponse(user_id=user)

@app.get("/calculations/{user_id}")
async def get_calculations(user_id: int):
    calculations = await db.get_calculations_by_user(user_id)
    if not calculations:
        raise HTTPException(status_code=404, detail="No calculations found for this user")
    return calculations


if __name__ == "__main__":
    db = workwithbd()
    uvicorn.run(app, host="127.0.0.1", port=9011)