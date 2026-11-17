from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('travel_planner.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT NOT NULL,
            title TEXT NOT NULL,
            target_budget INTEGER NOT NULL
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS budget_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER,
            section_title TEXT,
            name TEXT,
            price INTEGER,
            qty INTEGER,
            FOREIGN KEY (trip_id) REFERENCES trips (id)
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER,
            amount INTEGER NOT NULL,
            FOREIGN KEY (trip_id) REFERENCES trips (id)
        )
    ''')
    
    # Tabel baru untuk Catatan & Packing List
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER,
            content TEXT NOT NULL,
            FOREIGN KEY (trip_id) REFERENCES trips (id)
        )
    ''')
    
    trip_check = conn.execute('SELECT COUNT(*) FROM trips').fetchone()[0]
    if trip_check == 0:
        conn.execute('INSERT INTO trips (destination, title, target_budget) VALUES (?, ?, ?)', 
                     ('Bandung', 'Trip Lembang 3H2M (Difa & Iann)', 3939000))
        trip_id = 1
        
        initial_items = [
            (trip_id, 'Transportasi (Semarang - Jakarta & PP)', 'Bus Iann (Semarang - Jakarta)', 400000, 1),
            (trip_id, 'Transportasi (Semarang - Jakarta & PP)', 'Kereta (Jatinegara - Bandung PP)', 175000, 4),
            (trip_id, 'Transportasi (Semarang - Jakarta & PP)', 'Grab Kost - Stasiun', 27000, 2),
            (trip_id, 'Transportasi (Semarang - Jakarta & PP)', 'Angkot & Transport Lokal', 400000, 1),
            
            (trip_id, 'Orchid Forest Cikole (Sabtu Pagi)', 'Ticket Terusan', 105000, 2),
            (trip_id, 'Orchid Forest Cikole (Sabtu Pagi)', 'Tea Pitcher', 40000, 1),
            (trip_id, 'Orchid Forest Cikole (Sabtu Pagi)', 'Waffle Ice Cream', 45000, 1),
            (trip_id, 'Orchid Forest Cikole (Sabtu Pagi)', 'Double Cheese Burger + French Fries', 80000, 1),
            
            (trip_id, 'Farm House Lembang (Sabtu Siang)', 'Ticket Masuk', 40000, 2),
            (trip_id, 'Farm House Lembang (Sabtu Siang)', 'Spot Foto & Jajan', 200000, 1),
            
            (trip_id, 'Tangkuban Perahu (Minggu Pagi)', 'Ticket Masuk', 40000, 2),
            (trip_id, 'Tangkuban Perahu (Minggu Pagi)', 'Jajan & Kuliner', 150000, 1),
            
            (trip_id, 'Hotel & Makan Malam (2 Malam)', 'Hotel (2 Malam)', 300000, 2),
            (trip_id, 'Hotel & Makan Malam (2 Malam)', 'Makan Malam (1)', 150000, 1),
            (trip_id, 'Hotel & Makan Malam (2 Malam)', 'Makan Malam (2)', 150000, 1),
            
            (trip_id, 'Lain-lain & Oleh-oleh', 'Makan & Jajan Tambahan', 300000, 1),
            (trip_id, 'Lain-lain & Oleh-oleh', 'Oleh-oleh Cokelat', 300000, 1),
        ]
        conn.executemany('INSERT INTO budget_items (trip_id, section_title, name, price, qty) VALUES (?, ?, ?, ?, ?)', initial_items)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    trips = conn.execute('SELECT * FROM trips').fetchall()
    conn.close()
    return render_template('index.html', trips=trips)

@app.route('/add_trip', methods=['POST'])
def add_trip():
    destination = request.form['destination']
    title = request.form['title']
    target_budget = int(request.form['target_budget'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO trips (destination, title, target_budget) VALUES (?, ?, ?)', 
                   (destination, title, target_budget))
    trip_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/trip/<int:trip_id>/edit', methods=['GET', 'POST'])
def edit_trip(trip_id):
    conn = get_db_connection()
    trip = conn.execute('SELECT * FROM trips WHERE id = ?', (trip_id,)).fetchone()
    
    if request.method == 'POST':
        destination = request.form['destination']
        title = request.form['title']
        target_budget = int(request.form['target_budget'])
        
        conn.execute('UPDATE trips SET destination = ?, title = ?, target_budget = ? WHERE id = ?',
                     (destination, title, target_budget, trip_id))
        conn.commit()
        conn.close()
        return redirect(url_for('trip_detail', trip_id=trip_id))
        
    conn.close()
    return render_template('edit_trip.html', trip=trip)

@app.route('/trip/<int:trip_id>/delete')
def delete_trip(trip_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM budget_items WHERE trip_id = ?', (trip_id,))
    conn.execute('DELETE FROM savings WHERE trip_id = ?', (trip_id,))
    conn.execute('DELETE FROM notes WHERE trip_id = ?', (trip_id,))
    conn.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/trip/<int:trip_id>')
def trip_detail(trip_id):
    conn = get_db_connection()
    trip = conn.execute('SELECT * FROM trips WHERE id = ?', (trip_id,)).fetchone()
    if not trip:
        conn.close()
        return redirect(url_for('index'))
        
    budget_items = conn.execute('SELECT * FROM budget_items WHERE trip_id = ?', (trip_id,)).fetchall()
    
    calculated_total = 0
    sections = {}
    for item in budget_items:
        calculated_total += (item['price'] * item['qty'])
        sec = item['section_title']
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(item)
        
    savings_list = conn.execute('SELECT * FROM savings WHERE trip_id = ? ORDER BY id DESC', (trip_id,)).fetchall()
    total_saved = conn.execute('SELECT SUM(amount) FROM savings WHERE trip_id = ?', (trip_id,)).fetchone()[0]
    total_saved = total_saved if total_saved else 0
    
    # Ambil daftar catatan perjalanan
    notes_list = conn.execute('SELECT * FROM notes WHERE trip_id = ? ORDER BY id DESC', (trip_id,)).fetchall()
    
    conn.close()
    
    target = calculated_total
    remaining = target - total_saved
    progress = int((total_saved / target) * 100) if target > 0 else 0
    if progress > 100: progress = 100

    return render_template('trip_detail.html', 
                           trip=trip,
                           sections=sections,
                           savings_list=savings_list,
                           notes_list=notes_list,
                           total_saved=total_saved,
                           remaining=remaining,
                           progress=progress,
                           calculated_total=calculated_total)

@app.route('/trip/<int:trip_id>/add_saving', methods=['POST'])
def add_saving(trip_id):
    amount = int(request.form['amount'])
    conn = get_db_connection()
    conn.execute('INSERT INTO savings (trip_id, amount) VALUES (?, ?)', (trip_id, amount))
    conn.commit()
    conn.close()
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/trip/<int:trip_id>/add_item', methods=['POST'])
def add_item(trip_id):
    section_title = request.form['section_title']
    name = request.form['name']
    price = int(request.form['price'])
    qty = int(request.form['qty'])
    
    conn = get_db_connection()
    conn.execute('INSERT INTO budget_items (trip_id, section_title, name, price, qty) VALUES (?, ?, ?, ?, ?)', 
                 (trip_id, section_title, name, price, qty))
    conn.commit()
    conn.close()
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/item/<int:item_id>/delete/<int:trip_id>')
def delete_item(item_id, trip_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM budget_items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM budget_items WHERE id = ?', (item_id,)).fetchone()
    
    if request.method == 'POST':
        section_title = request.form['section_title']
        name = request.form['name']
        price = int(request.form['price'])
        qty = int(request.form['qty'])
        
        conn.execute('UPDATE budget_items SET section_title = ?, name = ?, price = ?, qty = ? WHERE id = ?',
                     (section_title, name, price, qty, item_id))
        conn.commit()
        conn.close()
        return redirect(url_for('trip_detail', trip_id=item['trip_id']))
        
    conn.close()
    return render_template('edit_item.html', item=item)

# Rute untuk Tambah & Hapus Catatan
@app.route('/trip/<int:trip_id>/add_note', methods=['POST'])
def add_note(trip_id):
    content = request.form['content']
    conn = get_db_connection()
    conn.execute('INSERT INTO notes (trip_id, content) VALUES (?, ?)', (trip_id, content))
    conn.commit()
    conn.close()
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/note/<int:note_id>/delete/<int:trip_id>')
def delete_note(note_id, trip_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('trip_detail', trip_id=trip_id))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)