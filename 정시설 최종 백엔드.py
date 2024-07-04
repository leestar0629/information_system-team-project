from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from typing import List
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
import pymysql
import logging
import asyncio

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="templates")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# 데이터베이스 연결 설정
try:
    conn = pymysql.connect(host="localhost", user="root", password="mangolim@20",
                           db='carrel2', charset="utf8", cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()
except Exception as e:
    logger.error(f"데이터베이스 연결 오류: {e}")
    raise HTTPException(status_code=500, detail="데이터베이스 연결에 실패했습니다.")

async def call_procedure():
    try:
        # 트랜잭션 시작
        conn.begin()

        # 저장 프로시저 호출
        cur.callproc('cancel_reservation')
        cur.callproc('update_reservation0')

        # 변경 사항 커밋
        conn.commit()

        logger.info("Stored procedure executed and committed successfully.")
    except pymysql.MySQLError as err:
        # 오류 발생 시 롤백
        if conn:
            conn.rollback()
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail=f"Error: {err}")

@app.get("/")
async def home(request: Request):
    await call_procedure()
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/insert/")
async def insert(request: Request):
    await call_procedure()
    return templates.TemplateResponse("insert.html", {"request": request})

@app.get("/delete/")
async def delete(request: Request):
    await call_procedure()
    return templates.TemplateResponse("delete.html", {"request": request})

@app.get("/search/")
async def search(request: Request):
    await call_procedure()
    return templates.TemplateResponse("search.html", {"request": request})

@app.get("/check/")
async def check(request: Request):
    await call_procedure()
    return templates.TemplateResponse("check.html", {"request": request})

@app.get("/user_search/")
async def user_search(request: Request):
    await call_procedure()
    return templates.TemplateResponse("user_search.html", {"request": request})

@app.get("/room_search/")
async def room_search(request: Request):
    await call_procedure()
    return templates.TemplateResponse("room_search.html", {"request": request})

@app.get("/search_get/")
async def get_reservations_by_student_id(student_id: int = Query(..., description="학생 ID를 입력하세요")):
    await call_procedure()
    try:
        logger.info(f"받은 student_id: {student_id}")  # 디버깅용 로그

        sql = """
        SELECT b.booking_id, b.date, b.period, b.num_person, b.bookingroom_id, b.representative
        FROM student s
        JOIN have h ON s.student_id = h.booking_student_id
        JOIN booking b ON h.have_booking_id = b.booking_id
        WHERE s.student_id = %s
        """
        cur.execute(sql, (student_id,))

        rows = cur.fetchall()

        logger.info(f"조회된 데이터: {rows}")  # 디버깅용 로그

        if not rows:
            data=[]
            return data


        # 응답 구조 생성 및 datetime 객체 변환
        response = []
        for row in rows:
            reservation = {
                "booking_id": row["booking_id"],
                "date": row["date"].strftime('%Y-%m-%d %H:%M:%S'),
                "period": row["period"],
                "num_person": row["num_person"],
                "bookingroom_id": row["bookingroom_id"],
                "representative": row["representative"]
            }
            response.append(reservation)

        return response

    except Exception as e:
        logger.error(f"오류: {e}")  # 디버깅용 로그
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user_search_get/")
async def get_user_info_by_student_id(student_id: int = Query(..., description="학생 ID를 입력하세요")):
    await call_procedure()
    try:
        logger.info(f"받은 student_id: {student_id}")  # 디버깅용 로그

        sql = """
        SELECT name, availability, phone_num, status
        FROM student
        WHERE student_id = %s
        """
        cur.execute(sql, (student_id,))

        row = cur.fetchone()

        logger.info(f"조회된 데이터: {row}")  # 디버깅용 로그

        if not row:
            raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")

        user_info = {
            "name": row["name"],
            "availability": row["availability"],
            "phone_num": row["phone_num"],
            "status": row["status"]
        }

        return user_info

    except Exception as e:
        logger.error(f"오류: {e}")  # 디버깅용 로그
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/delete_get/")
async def get_booking_info(booking_id: int = Query(..., description="예약 ID를 입력하세요")):
    await call_procedure()
    try:
        logger.info(f"받은 booking_id: {booking_id}")  # 디버깅용 로그

        sql = """
        SELECT s.student_id, s.name, s.phone_num, b.bookingroom_id, b.date, b.period
        FROM student s
        JOIN have h ON s.student_id = h.booking_student_id
        JOIN booking b ON h.have_booking_id = b.booking_id
        WHERE b.booking_id = %s
        """
        cur.execute(sql, (booking_id,))

        rows = cur.fetchall()

        logger.info(f"조회된 데이터: {rows}")  # 디버깅용 로그

        if not rows:
            data=[]
            return data

        # 응답 구조 생성
        response = []
        for row in rows:
            booking_info = {
                "student_id": row["student_id"],
                "name": row["name"],
                "phone_num": row["phone_num"],
                "room_id": row["bookingroom_id"],
                "date": row["date"].strftime('%Y-%m-%d %H:%M:%S'),
                "period": row["period"]
            }
            response.append(booking_info)

        return response

    except Exception as e:
        logger.error(f"오류: {e}")  # 디버깅용 로그
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete_booking/")
async def delete_booking(booking_id: int = Query(..., description="예약 ID를 입력하세요")):
    await call_procedure()
    try:
        logger.info(f"받은 booking_id: {booking_id}")  # 디버깅용 로그

        # 예약 존재 여부 확인
        check_sql = "SELECT * FROM booking WHERE booking_id = %s"
        cur.execute(check_sql, (booking_id,))
        booking = cur.fetchone()

        if not booking:
            raise HTTPException(status_code=404, detail="해당 예약 내역을 찾을 수 없습니다.")
        
        # 예약의 end 상태 확인
        if booking["end"] == 1:
            raise HTTPException(status_code=400, detail="이미 종료된 예약은 삭제할 수 없습니다.")

        # 예약 삭제
        delete_sql = "DELETE FROM booking WHERE booking_id = %s"
        cur.execute(delete_sql, (booking_id,))

        conn.commit()

        return {"detail": "예약이 성공적으로 삭제되었습니다."}

    except Exception as e:
        logger.error(f"오류: {e}")  # 디버깅용 로그
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/check_get/")
async def check_booking_info(booking_id: int = Query(..., description="예약 ID를 입력하세요")):
    await call_procedure()
    try:
        logger.info(f"받은 booking_id: {booking_id}")  # 디버깅용 로그

        sql = """
        SELECT s.student_id, s.name, s.phone_num, b.bookingroom_id, b.date, b.period, b.start, b.end
        FROM student s
        JOIN have h ON s.student_id = h.booking_student_id
        JOIN booking b ON h.have_booking_id = b.booking_id
        WHERE b.booking_id = %s
        """
        cur.execute(sql, (booking_id,))

        rows = cur.fetchall()

        logger.info(f"조회된 데이터: {rows}")  # 디버깅용 로그

        if not rows:
            raise HTTPException(status_code=404, detail="해당 예약 내역을 찾을 수 없습니다.")

        # 응답 구조 생성
        response = []
        for row in rows:
            booking_info = {
                "student_id": row["student_id"],
                "name": row["name"],
                "phone_num": row["phone_num"],
                "bookingroom_id": row["bookingroom_id"],
                "date": row["date"].strftime('%Y-%m-%d %H:%M:%S'),
                "period": row["period"],
                "start": row["start"],
                "end": row["end"]
            }
            response.append(booking_info)

        return response

    except Exception as e:
        logger.error(f"오류: {e}")  # 디버깅용 로그
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/check_in/")
async def check_in(booking_id: int = Query(..., description="예약 ID를 입력하세요")):
    await call_procedure()
    try:
        logger.info(f"입실 확인 받은 booking_id: {booking_id}")  # 디버깅용 로그

        # 예약 내역 조회
        sql = """
        SELECT date, period FROM booking
        WHERE booking_id = %s
        """
        cur.execute(sql, (booking_id,))

        booking = cur.fetchone()

        if not booking:
            raise HTTPException(status_code=404, detail="해당 예약 내역을 찾을 수 없습니다.")

        booking_date = booking["date"]
        booking_period = booking["period"]
        checkin_deadline = booking_date + timedelta(minutes=10)

        # 현재 시간 가져오기
        current_time = datetime.now()

        # 입실 시간이 예약 시간으로부터 10분 이내인지 검사
        if current_time > checkin_deadline:
            raise HTTPException(status_code=400, detail="입실 가능 시간이 지났습니다.")

        # 입실 처리 (start를 1로 업데이트)
        cur.execute("""
        UPDATE booking SET start = 1
        WHERE booking_id = %s
        """, (booking_id,))

        conn.commit()
        return {"detail": "입실이 성공적으로 처리되었습니다."}

    except Exception as e:
        logger.error(f"오류: {e}")  # 디버깅용 로그
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/check_out/")
async def check_out(booking_id: int = Query(..., description="예약 ID를 입력하세요")):
    await call_procedure()
    try:
        logger.info(f"퇴실 확인 받은 booking_id: {booking_id}")  # 디버깅용 로그

        # 예약 내역 조회
        sql = """
        SELECT date, period FROM booking
        WHERE booking_id = %s
        """
        cur.execute(sql, (booking_id,))

        booking = cur.fetchone()

        if not booking:
            raise HTTPException(status_code=404, detail="해당 예약 내역을 찾을 수 없습니다.")

        booking_date = booking["date"]
        booking_period = booking["period"]
        checkout_deadline = booking_date + timedelta(minutes=booking_period)

        # 현재 시간 가져오기
        current_time = datetime.now()

        # 퇴실 시간이 예약 종료 시간을 지났는지 검사
        if current_time > checkout_deadline:
            raise HTTPException(status_code=400, detail="퇴실 시간이 이미 지났습니다.")

        # 퇴실 처리 (end를 1로 업데이트)
        cur.execute("""
        UPDATE booking SET end = 1
        WHERE booking_id = %s
        """, (booking_id,))

        conn.commit()
        return {"detail": "퇴실이 성공적으로 처리되었습니다."}

    except Exception as e:
        logger.error(f"오류: {e}")  # 디버깅용 로그
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/carrel_search_get/")
async def carrel_search_get(room_type: int = Query(..., description="캐럴 종류를 입력하세요"), beam_able: bool = Query(..., description="빔 프로젝트 사용 여부를 입력하세요")):
    await call_procedure()
    try:
        logger.info(f"받은 room_type: {room_type}, beam_able: {beam_able}")  # 디버깅용 로그

        sql = """
        SELECT room_id FROM study_room
        WHERE room_type = %s AND beam_able = %s AND booking_able = 1
        """
        cur.execute(sql, (room_type, beam_able))

        rows = cur.fetchall()

        logger.info(f"조회된 데이터: {rows}")  # 디버깅용 로그

        if not rows:
            raise HTTPException(status_code=404, detail="해당 조건에 맞는 이용 가능한 캐럴이 없습니다.")

        # 응답 구조 생성
        response = {
            "room_type": room_type,
            "beam_able": beam_able,
            "available_carrels": [{"room_id": row["room_id"]} for row in rows]
        }

        return response

    except Exception as e:
        logger.error(f"오류: {e}")  # 디버깅용 로그
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insert_get/")
async def add_booking(
        representative: int,
        date_time: str,
        period: int,
        num_person: int,
        beam_able: bool,
        participant_ids: str = Query(..., description="참여자 학번 리스트를 쉼표로 구분하여 입력하세요. 예: 202010001,202010002")
):
    await call_procedure()
    try:
        logger.info(f"Received representative: {representative}, date_time: {date_time}, period: {period}, num_person: {num_person}, beam_able: {beam_able}, participant_ids: {participant_ids}")

        # Parse participant_ids from comma-separated string to a list of integers
        try:
            if num_person != 1:
                participant_ids_list = list(map(int, participant_ids.split(',')))
            else:
                participant_ids_list = []
            participant_ids_list.append(representative)  # 대표자 ID를 참가자 리스트에 추가
        except ValueError as ve:
            logger.error(f"Invalid participant_ids format: {participant_ids}")
            raise HTTPException(status_code=400, detail="참여자 학번 리스트 형식이 잘못되었습니다. 올바른 형식: 202010001,202010002")

        if len(participant_ids_list) != num_person:
            logger.error(f"Number of participants does not match: {participant_ids_list}")
            raise HTTPException(status_code=400, detail="참가자 수가 올바르지 않습니다.")

        # 트랜잭션 시작
        conn.begin()

        # 1. 모든 참가자들의 availability 검사
        participant_ids_tuple = tuple(participant_ids_list)
        query = "SELECT availability FROM student WHERE student_id IN %s" if len(participant_ids_tuple) > 1 else "SELECT availability FROM student WHERE student_id = %s"
        cur.execute(query, (participant_ids_tuple,))
        
        availabilities = cur.fetchall()

        if not all(a["availability"] for a in availabilities):
            conn.rollback()
            logger.error(f"Not all participants are available: {availabilities}")
            raise HTTPException(status_code=400, detail="모든 참가자들의 availability가 1이어야 합니다.")

        # 2. 적절한 방 타입 찾기
        if num_person == 1:
            room_type = 1
        elif 1 < num_person <= 4:
            room_type = 4
        elif 5 <= num_person <= 6:
            room_type = 6
        elif 6 < num_person <= 12:
            room_type = 12
        else:
            conn.rollback()
            logger.error(f"Invalid number of participants: {num_person}")
            raise HTTPException(status_code=400, detail="인원수가 너무 많습니다.")

        # 대표자의 신분 확인
        cur.execute("SELECT status FROM student WHERE student_id = %s", (representative,))
        rep_status = cur.fetchone()["status"]

        # 방 찾기 로직
        if rep_status == '대학원생':
            if room_type == 1:
                room_types_to_check = [1, 4]
            elif room_type == 4:
                room_types_to_check = [4, 6]
            elif room_type == 6:
                room_types_to_check = [6, 12]
            else:
                room_types_to_check = [12]

        else:
            room_types_to_check = [room_type]

        available_room_found = False

        for room_type_to_check in room_types_to_check:
            cur.execute("""
            SELECT room_id FROM study_room
            WHERE room_type = %s AND booking_able = 1 AND beam_able = %s
            """, (room_type_to_check, beam_able))
            available_rooms = cur.fetchall()

            for room in available_rooms:
                bookingroom_id = room["room_id"]
                
                # 선택된 방의 예약 내역 조회
                cur.execute("""
                SELECT date, period, end FROM booking
                WHERE bookingroom_id = %s
                """, (bookingroom_id,))
                existing_bookings = cur.fetchall()

                requested_start = datetime.strptime(date_time, '%Y-%m-%dT%H:%M')
                requested_end = requested_start + timedelta(hours=period)

                conflict_found = False

                for booking in existing_bookings:
                    if booking["end"] == 1:
                        continue  # 이미 종료된 예약은 고려하지 않음

                    booking_start = booking["date"]
                    booking_end = booking_start + timedelta(minutes=booking["period"] * 60)  # 시간을 분으로 변환

                    if not (requested_end <= booking_start or requested_start >= booking_end):
                        conflict_found = True
                        break

                if not conflict_found:
                    available_room_found = True
                    break
            
            if available_room_found:
                break

        if not available_room_found:
            conn.rollback()
            logger.error("No available rooms found")
            raise HTTPException(status_code=400, detail="예약 가능한 방이 없습니다.")

        # 5. 예약 추가하기 전에 representative의 period 제한 확인
        if rep_status == '학부생' and period > 3:
            conn.rollback()
            logger.error("Undergraduate representative booking period exceeds limit")
            raise HTTPException(status_code=400, detail="학부생은 최대 3시간까지만 예약할 수 있습니다.")

        # 예약 추가
        cur.execute("""
        INSERT INTO booking (date, period, num_person, bookingroom_id, representative)
        VALUES (%s, %s, %s, %s, %s)
        """, (date_time, period, num_person, bookingroom_id, representative))
        conn.commit()

        booking_id = cur.lastrowid

        # 'have' 테이블에 참가자 추가
        if num_person >= 2:
            participant_ids_list.pop()
            for participant_id in participant_ids_list:
                cur.execute("INSERT INTO have (booking_student_id, have_booking_id) VALUES (%s, %s)",
                            (participant_id, booking_id))

        conn.commit()

        # 트랜잭션 커밋
        conn.commit()

        return {"detail": "예약이 성공적으로 추가되었습니다."}

    except Exception as e:
        logger.error(f"오류: {e}")  # 디버깅용 로그
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
