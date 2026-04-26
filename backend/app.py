from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.secret_key = 'supersecretkey_ayurtech_flask'
DATABASE = 'ayurtech.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db_connection()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                doctor_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                height REAL,
                weight REAL,
                bmi REAL,
                allergies TEXT,
                medical_conditions TEXT,
                prakriti TEXT,
                dosha_imbalance TEXT,
                lifestyle_notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (doctor_id) REFERENCES users (id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS diet_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                plan_json TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        db.commit()
        db.close()

init_db()

# ---- AUTH ROUTES ----
@app.route('/', methods=['GET'])
def index():
    if 'user_id' in session:
        if session.get('role') == 'doctor':
            return redirect('/doctor_dashboard')
        else:
            return redirect('/patient_dashboard')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                         (name, email, password, role))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Email already exists.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']
            return redirect('/')
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---- DOCTOR ROUTES ----
@app.route('/doctor_dashboard')
def doctor_dashboard():
    if session.get('role') != 'doctor':
        return redirect('/')
    
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients WHERE doctor_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('doctor_dashboard.html', patients=patients)

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if session.get('role') != 'doctor':
        return redirect('/')
        
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        bmi = round(weight / ((height/100) ** 2), 2) if height > 0 else 0
        prakriti = request.form['prakriti']
        dosha_imbalance = request.form['dosha_imbalance']
        allergies = request.form['allergies']
        medical_conditions = request.form['medical_conditions']
        lifestyle_notes = request.form['lifestyle_notes']
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO patients (doctor_id, name, age, gender, height, weight, bmi, prakriti, dosha_imbalance, allergies, medical_conditions, lifestyle_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], name, age, gender, height, weight, bmi, prakriti, dosha_imbalance, allergies, medical_conditions, lifestyle_notes))
        conn.commit()
        conn.close()
        flash('Patient added successfully', 'success')
        return redirect('/doctor_dashboard')
    return render_template('add_patient.html')

@app.route('/diet_plan/<int:patient_id>')
def view_diet_plan(patient_id):
    if 'user_id' not in session:
        return redirect('/')
        
    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    diet_plan_row = conn.execute('SELECT * FROM diet_plans WHERE patient_id = ?', (patient_id,)).fetchone()
    conn.close()
    
    diet_plan = json.loads(diet_plan_row['plan_json']) if diet_plan_row else None
    return render_template('diet_plan.html', patient=patient, diet_plan=diet_plan)

@app.route('/generate_diet_plan/<int:patient_id>', methods=['POST'])
def generate_diet_plan(patient_id):
    if session.get('role') != 'doctor':
        return redirect('/')
        
    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    imbalance = patient['dosha_imbalance'] if patient and patient['dosha_imbalance'] else 'Vata'
    
    recommendations = {
        "Vata": {
            "avoid": "Cold, dry, and light foods.",
            "prefer": "Warm, moist, and grounding foods.",
            "breakfast": "Warm oatmeal with ghee and almonds",
            "lunch": "Basmati rice, moong dal, and cooked sweet potatoes",
            "dinner": "Warm soup with cooked root vegetables",
            "reason": "Vata is balanced by warm, heavy, and moist qualities."
        },
        "Pitta": {
            "avoid": "Spicy, sour, and hot foods.",
            "prefer": "Cooling, sweet, and bitter foods.",
            "breakfast": "Cooling coconut milk smoothie with sweet berries",
            "lunch": "Quinoa salad with cucumber and fresh coriander",
            "dinner": "Steamed green vegetables with simple rice",
            "reason": "Pitta is hot; cooling and mild foods soothe it."
        },
        "Kapha": {
            "avoid": "Heavy, oily, and sweet foods.",
            "prefer": "Light, warm, and spicy foods.",
            "breakfast": "Warm spiced apples with ginger and cinnamon",
            "lunch": "Spiced lentil soup (dal) with steamed greens",
            "dinner": "Light quinoa with roasted vegetables",
            "reason": "Kapha is heavy and cold; light, warm foods stimulate it."
        }
    }
    rec = recommendations.get(imbalance, recommendations["Vata"])
    
    plan_json = json.dumps({
        "imbalance": imbalance,
        "principles": {"avoid": rec["avoid"], "prefer": rec["prefer"]},
        "meals": {
            "Breakfast": {"food": rec["breakfast"], "explanation": rec["reason"]},
            "Lunch": {"food": rec["lunch"], "explanation": rec["reason"]},
            "Dinner": {"food": rec["dinner"], "explanation": rec["reason"]}
        }
    })
    
    existing = conn.execute('SELECT id FROM diet_plans WHERE patient_id = ?', (patient_id,)).fetchone()
    if existing:
        conn.execute('UPDATE diet_plans SET plan_json = ? WHERE patient_id = ?', (plan_json, patient_id))
    else:
        conn.execute('INSERT INTO diet_plans (patient_id, plan_json) VALUES (?, ?)', (patient_id, plan_json))
        
    conn.commit()
    conn.close()
    flash('AI Diet Plan Generated!', 'success')
    return redirect(f'/diet_plan/{patient_id}')

@app.route('/recipe_analyzer', methods=['GET', 'POST'])
def recipe_analyzer():
    result = None
    if request.method == 'POST':
        recipe_text = request.form.get('recipe_text', '').lower()
        
        ingredients = []
        calories, protein, carbs, fat = 0, 0, 0, 0
        rasa_set = set()
        virya, vipaka, guna = "Neutral", "Sweet", "Light"
        
        if "chicken" in recipe_text or "meat" in recipe_text:
            ingredients.append("Meat"); calories += 250; protein += 25; fat += 15; rasa_set.add("Sweet"); virya = "Heating"
        if "rice" in recipe_text:
            ingredients.append("Rice"); calories += 130; carbs += 28; protein += 2; rasa_set.add("Sweet"); vipaka = "Sweet"
        if "spice" in recipe_text or "chili" in recipe_text:
            ingredients.append("Spices"); calories += 10; rasa_set.add("Pungent"); virya = "Heating"; vipaka = "Pungent"
        if "milk" in recipe_text or "ghee" in recipe_text:
            ingredients.append("Dairy"); calories += 100; fat += 10; rasa_set.add("Sweet"); virya = "Cooling"
            
        if not ingredients:
            ingredients.append("Generic Mix"); calories=200; carbs=25; rasa_set.add("Mixed")
            
        if "fried" in recipe_text or "cheese" in recipe_text:
            guna = "Heavy"
            
        result = {
            "ingredients": ingredients,
            "nutrition": {"calories": calories, "protein": protein, "carbs": carbs, "fat": fat},
            "ayurveda": {"rasa": ", ".join(list(rasa_set)), "virya": virya, "vipaka": vipaka, "guna": guna}
        }
    return render_template('recipe_analyzer.html', result=result)

# ---- PATIENT ROUTES ----
@app.route('/patient_dashboard')
def patient_dashboard():
    if session.get('role') != 'patient':
        return redirect('/')
    
    # We map the patient by matching the patient's name with user's name for simplicity,
    # or ideal scenario we should link user_id. Here we assume doctor added patient and patient registered with same name/email.
    # To keep it simple, we check if patient.name matches session.name
    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE name = ?', (session['name'],)).fetchone()
    
    diet_plan = None
    if patient:
        diet_plan_row = conn.execute('SELECT * FROM diet_plans WHERE patient_id = ?', (patient['id'],)).fetchone()
        if diet_plan_row:
            diet_plan = json.loads(diet_plan_row['plan_json'])
            
    conn.close()
    return render_template('patient_dashboard.html', patient=patient, diet_plan=diet_plan)

if __name__ == '__main__':
    app.run(debug=True)
