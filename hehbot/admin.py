class StaffPerson:
    def __init__(self, number: int, telegram: int = None, admin = False, credits = 100, max_credit = 100, discord: int = None) -> None:
        self.number = number
        self.telegram = telegram
        self.discord = discord
        self.admin = admin
        self.credits = credits
        self.max_credits = max_credit


import sqlite3
from abc import ABC, abstractmethod
from typing import List
from hehbot.env_service import env

class ITGStaffPersonRepository(ABC):
    @abstractmethod
    def add(self, staff: StaffPerson) -> None:
        pass

    @abstractmethod
    def get_by_number(self, number: int):
        pass

    @abstractmethod
    def get_all(self) -> List[StaffPerson]:
        pass

    @abstractmethod
    def update(self, staff) -> None:
        pass

    @abstractmethod
    def delete(self, id: int) -> None:
        pass


class TGStaffPersonRepository(ITGStaffPersonRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()
        #self.add(StaffPerson(788237639, True, -1))

    def _create_table(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                number INT PRIMARY KEY UNIQUE,
                telegram INT UNIQUE,
                admin BOOLEAN NOT NULL,
                credit_left INT,
                max_credit INT,
                discord INT UNIQUE
            )
        ''')
        conn.commit()
        conn.close()

    def add(self, staff: StaffPerson) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT telegram FROM staff WHERE telegram = ?', (staff.telegram,))
        if cursor.fetchone():
            print(f"Record with telegram {staff.telegram} already exists.")
            conn.close()
            self.update(staff)
            return
        cursor.execute('SELECT discord FROM staff WHERE discord = ?', (staff.discord,))
        if cursor.fetchone():
            print(f"Record with discord {staff.discord} already exists.")
            conn.close()
            self.update(staff)
            return

        cursor.execute('''
            INSERT INTO staff (number, telegram, admin, credit_left, max_credit, discord)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (staff.number, staff.telegram, staff.admin, staff.credits, staff.max_credits, staff.discord))
        conn.commit()
        conn.close()

    def get_by_number(self, number: int) -> StaffPerson:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM staff WHERE number = ?', (number,))
        row = cursor.fetchone()
        conn.close()
        return StaffPerson(*row) if row else None

    def get_all(self) -> List[StaffPerson]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM staff')
        rows = cursor.fetchall()
        conn.close()
        return [StaffPerson(*row) for row in rows]

    def update(self, staff: StaffPerson) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE staff
            SET admin = ?, credit_left = ?, max_credit = ?
            WHERE number = ?
        ''', (staff.admin, staff.credits, staff.max_credits, staff.number))
        conn.commit()
        conn.close()

    def delete(self, number: int) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM staff WHERE number = ?', (number,))
        conn.commit()
        conn.close()

repo_staff = TGStaffPersonRepository('{}/staff.db'.format(env.data_path))