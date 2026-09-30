from app import create_app
from app.db import query_all, query_one, get_db_connection

app = create_app()

def test_full_flow():
    # Fetch valid seat for Show 1
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.callproc("sp_get_show_seats", (1,))
        seats = cur.fetchall()
    conn.close()

    assert len(seats) > 0, "No seats found for show 1"
    target_seat = seats[0]
    target_seat_id = str(target_seat["seat_id"])
    print(f"[*] Testing with real Seat: {target_seat['seat_number']} (ID: {target_seat_id})")

    with app.test_client() as client:
        # 1. Login as Customer
        login_res = client.post('/login', data={'email': 'john@example.com', 'password': 'User@123'}, follow_redirects=True)
        print('[+] Login Customer Status:', login_res.status_code)

        # 2. View Seats for Show 1
        seats_res = client.get('/shows/1/seats')
        print('[+] View Seats Status:', seats_res.status_code)

        # 3. Book the real Seat
        book_res = client.post('/shows/1/book', data={'seat_ids': [target_seat_id], 'payment_method': 'UPI'}, follow_redirects=True)
        print('[+] Booking POST Status:', book_res.status_code)
        
        # Check booking record in DB
        booking = query_one('SELECT * FROM bookings WHERE user_id = 2 ORDER BY booking_id DESC LIMIT 1')
        assert booking is not None, "Booking record was not created!"
        print(f"[+] Created Booking Ref: {booking['booking_reference']} | Total: ${booking['total_amount']} | Status: {booking['status']}")

        # Check Trigger 1 in audit_logs
        audit_insert = query_one("SELECT * FROM audit_logs WHERE action_type = 'BOOKING_CREATED' ORDER BY log_id DESC LIMIT 1")
        assert audit_insert is not None, "Audit log for insert not found!"
        print(f"[+] Trigger 1 (Insert) Fired! Audit Log: {audit_insert['details']}")

        # 4. View Digital Ticket Pass
        ticket_res = client.get(f"/ticket/{booking['booking_reference']}")
        print(f"[+] View Ticket Status: {ticket_res.status_code}")

        # 5. Cancel Booking
        bid = booking['booking_id']
        cancel_res = client.post(f'/bookings/{bid}/cancel', follow_redirects=True)
        print(f"[+] Cancel Booking Status: {cancel_res.status_code}")

        # Check updated booking & payment status
        updated_booking = query_one('SELECT status FROM bookings WHERE booking_id = %s', (bid,))
        updated_payment = query_one('SELECT status FROM payments WHERE booking_id = %s', (bid,))
        print(f"[+] Booking Status after cancel: {updated_booking['status']}")
        print(f"[+] Payment Status after trigger: {updated_payment['status']}")
        assert updated_booking['status'] == 'CANCELLED'
        assert updated_payment['status'] == 'REFUNDED'

        # Check Trigger 2 in audit_logs
        audit_update = query_one("SELECT * FROM audit_logs WHERE action_type = 'BOOKING_CANCELLED' ORDER BY log_id DESC LIMIT 1")
        assert audit_update is not None, "Audit log for cancel not found!"
        print(f"[+] Trigger 2 (Update) Fired! Audit Log: {audit_update['details']}")

        print("\n[SUCCESS] ALL TESTS PASSED! FULL END-TO-END FLOW VERIFIED SUCCESSFULLY!")

if __name__ == '__main__':
    test_full_flow()
