# AyurTech - AI-powered Ayurvedic Diet Planning System (Flask Edition)

## Prerequisites
- Python 3.9+

## Setup & Run Project
1. Open a terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Flask Server:
   ```bash
   python app.py
   ```
   *Note: The SQLite database (`ayurtech.db`) and tables will automatically initialize when the script is run for the first time.*

5. Open your browser and navigate to `http://127.0.0.1:5000`

## Usage Instructions
1. **Register** as a "Doctor" or "Patient".
2. **Doctor Login:**
   - Add new patients with their Ayurvedic Prakriti and Dosha details.
   - Click "View Diet Plan" and then **Generate AI Diet Plan** to automatically generate a custom meal plan using Ayurvedic logic.
   - Use the **Recipe Analyzer** to evaluate the Dosha effect, Rasa, Virya, Vipaka, and Guna of text-based recipes.
3. **Patient Login:**
   - Note: Patients are linked by matching their exact name to the name the doctor provided in the Add Patient form.
   - View the generated diet plan from the doctor and check daily Ayurvedic principles.
