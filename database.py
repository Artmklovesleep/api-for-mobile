from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import asyncio
from datetime import datetime, timedelta

DATABASE_URL = "mysql+aiomysql://root:@localhost/mobile_bd"


class workwithbd:
    def __init__(self) -> None:
        self.engine = create_async_engine(DATABASE_URL, echo=True, future=True)

        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        self.Base = declarative_base()

    async def get_reviews(self):
        async with self.async_session() as session:
            stmt = text("SELECT * FROM reviews;")
            result = await session.execute(stmt, {"age_threshold": 30})
            rows = result.all()
            await session.commit()
            return rows

    async def create_user(self, email: str, login: str, password: str):
        try:
            async with self.async_session() as session:
                stmt = text(
                    "INSERT INTO user (email, login, password) VALUES (:email, :login, :password);"
                )
                params = {
                    "email": email,
                    "login": login,
                    "password": password,  # In a real case, password should be hashed
                }
                result = await session.execute(stmt, params)
                await session.commit()

                user_id_stmt = text("SELECT LAST_INSERT_ID();")
                result = await session.execute(user_id_stmt)
                user_id = result.scalar()
                return user_id
        except SQLAlchemyError as e:
            print(f"Error while creating user: {e}")
            return -1
        
    async def authenticate_user(self, login: str, password: str) -> int:
        try:
            async with self.async_session() as session:
                stmt = text(
                    "SELECT id FROM user WHERE login = :login AND password = :password;"
                )
                params = {
                    "login": login,
                    "password": password,
                }
                result = await session.execute(stmt, params)
                user = result.fetchone()

                if user:
                    return user[0]
                else:
                    return -1 
        except SQLAlchemyError as e:
            print(f"Error while authenticating user: {e}")
            return -1 

    async def record_calculation(self, user_id: int, tax_type: int, operation: int, amount: float, new: int, total: float):
        try:
            async with self.async_session() as session:
                stmt = text("""
                    INSERT INTO raschet (user_id, tax_type, date, operation, amount, new, total)
                    VALUES (:user_id, :tax_type, CURRENT_DATE, :operation, :amount, :new, :total);
                """)
                params = {
                    "user_id": user_id,
                    "tax_type": tax_type,
                    "operation": operation,
                    "amount": amount,
                    "new": new,
                    "total": total
                }
                await session.execute(stmt, params)
                await session.commit()
        except SQLAlchemyError as e:
            print(f"Error while inserting record into raschet: {e}")


    async def get_calculations_by_user(self, user_id: int):
        try:
            async with self.async_session() as session:
                stmt = text("SELECT * FROM raschet WHERE user_id = :user_id ORDER BY date DESC;")
                result = await session.execute(stmt, {"user_id": user_id})
                rows = result.fetchall()

                formatted_results = []

                for row in rows:
                    calc_id = str(row.id)
                    tax_type = row.tax_type
                    operation = row.operation
                    amount = row.amount
                    new = row.new
                    total = row.total
                    date = row.date


                    formatted_results.append({
                        'id': calc_id,
                        'tax_type': tax_type,
                        'date': date,
                        'operation': operation,
                        'amount': amount,
                        'new': new,
                        'total': total
                    })

                return formatted_results

        except SQLAlchemyError as e:
            print(f"Error while fetching calculations: {e}")
            return []


