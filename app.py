from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import hashlib
from bson.objectid import ObjectId

import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask import Flask, send_from_directory
from flask import Flask, send_from_directory
app = Flask(__name__)
app.secret_key = "samplekey"
app.config['UPLOAD_FOLDER'] = './uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

client = MongoClient("mongodb://localhost:27017/")
db = client.pet_adoption
shelters_collection=db['shelters']
users_collection = db['users']
admin_collection = db['admin']
Shelter_collection = db['shelter']
pets_collection=db['pets']
adoptions_collection=db['applications']
@app.route('/')
def index():
    return render_template('register.html')

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method =="POST":
        # Access form data (validation should be added here)
        name = request.form.get("name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        password = request.form.get("password")
        confirm_password = request.form.get('confirm_password')
        print(password)
        print(confirm_password)
        if password != confirm_password:
                flash("Passwords do not match, please enter the same passwords","error")
                return redirect(url_for("register"))

        
        role = request.form.get("role")

        # Hash the password securely before storing it
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        # Prepare common user data
        user_data = {
            "name": name,
            "email": email,
            "mobile": mobile,
            "password": hashed_password,
            "role": role
        }

        if role == "shelter":
            # Access additional shelter-specific data
            address = request.form.get("address")
            city = request.form.get("city")
            state = request.form.get("state")
            zipcode = request.form.get("zipcode")

            # Prepare shelter-specific data
            shelter_data = {
                **user_data,
                "address": address,
                "city": city,
                "state": state,
                "zipcode": zipcode,
                'status':"created"
            }

            # Insert shelter data into shelter collection
            shelter_collection = db.shelter
            shelter_collection.insert_one(shelter_data)
        elif role == "member":
            # Access additional member-specific data
            city = request.form.get("city-member")
            state = request.form.get("state-member")
            zipcode = request.form.get("zipcode-member")
            dob = request.form.get("dob")
            ssn = request.form.get("ssn")
            print(city)
            print(state)
            print(zipcode)
            # Prepare member-specific data
            member_data = {
                **user_data,
                "city": city,
                "state": state,
                "zipcode": zipcode,
                "dob": dob,
                "ssn": ssn
            }
            users_collection = db.users
            users_collection.insert_one(member_data)

        return render_template('register.html')
    else : 
        return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        role = request.form['role']

        if role == 'admin':
            admin_user = admin_collection.find_one({'email': email, 'password': hashed_password})
            if admin_user and admin_user['role'] == 'admin':
                session['email'] = email
                session['role'] = 'admin'
                flash('Logged in successfully as admin!', 'success')
                return redirect(url_for('admin_dashboard'))
        
        elif role == 'shelter':
            shelter_user = Shelter_collection.find_one({'email': email, 'password': hashed_password})
            if shelter_user and shelter_user['role'] == 'shelter':
                print(shelter_user.get('status'))
                if shelter_user.get('status') == 'created':
                    flash('Shelter account is not activated yet. Please wait for activation.', 'warning')
                    return redirect(url_for('login'))
                else:
                    session['email'] = email
                    session['role'] = 'shelter'
                    flash('Logged in successfully as shelter!', 'success')
                    return redirect(url_for('shelter_dashboard'))
        
        elif role == 'member':
            user = users_collection.find_one({'email': email, 'password': hashed_password})
            if user and user['role'] == 'member':
                session['email'] = email
                session['role'] = 'member'
                flash('Logged in successfully as member!', 'success')
                return redirect(url_for('user_dashboard'))
        
        flash('Invalid email or password', 'error')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')


@app.route('/shelter_dashboard')
def shelter_dashboard():
    return render_template('shelter_dashbaord.html')

@app.route('/member_dashbaord')
def user_dashboard():
    if 'email' in session and session['role'] == 'member':
        return render_template('user_dashbaord.html')
    else:
        flash('Unauthorized access', 'error')


        return redirect(url_for('login'))
    
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/create-adoption', methods=['GET', 'POST'])
def create_adoption():
    if request.method == 'GET':
        # Get list of shelters from your data source (replace with your logic)
        shelters = users_collection.find({"role": "shelter"})
        return render_template('create_shelter.html', shelters=shelters)



@app.route('/view-status')
def view_status():
    # Fetch and display shelter status data
    return render_template('view_status.html')  # Replace with data fetching

 # Replace with data fetching

@app.route("/add_pet", methods=["GET", "POST"])
def add_pet():
    if request.method == "GET":
        # Get all shelters for the dropdown
        shelters = shelters_collection.find()
        return render_template("add_pet.html", shelters=shelters)
    elif request.method == "POST":
        # Access form data
        pet_name = request.form.get("pet_name")
        breed = request.form.get("breed")
        pet_type = request.form.get("type")
        age = request.form.get("age")
        description = request.form.get("description")


        file = request.files['cover_image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cover_image_url = url_for('uploaded_file', filename=filename)
        else:
            cover_image_url = ''


        # Get selected shelter ID
        shelter_id = request.form.get("shelter")

        # Prepare pet data for insertion
        pet_data = {
            "pet_name": pet_name,
            "breed": breed,
            "type": pet_type,
            "age": age,
            "description": description,
            'cover_image': cover_image_url,
            "shelter_id": shelter_id,
             'status':'avaliable'
        }

        pets_collection.insert_one(pet_data)
        flash('Conference created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    


@app.route("/foster_add_pet", methods=["GET", "POST"])
def foster_add_pet():
    session_email=session["email"]
    print(session_email)
    user = Shelter_collection.find_one({'email': session_email, 'role': 'shelter'})
    username=user["name"]
    print(username)
    if request.method == "GET":
        # Get all shelters for the dropdown
        shelters = shelters_collection.find()
        return render_template("foster_create_adoption.html", shelters=shelters)
    elif request.method == "POST":

        # Access form data
        pet_name = request.form.get("pet_name")
        breed = request.form.get("breed")
        pet_type = request.form.get("type")
        age_years = int(request.form.get("years", 0))  # Default to 0 if not provided
        age_months = int(request.form.get("months", 0)) 
        age_weeks =int(request.form.get("weeks", 0))
        description = request.form.get("description")


        file = request.files['cover_image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cover_image_url = url_for('uploaded_file', filename=filename)
        else:
            cover_image_url = ''


        # Get selected shelter ID
        shelter_id = request.form.get("shelter")

        # Prepare pet data for insertion
        pet_data = {
            "pet_name": pet_name,
            "breed": breed,
            "type": pet_type,
            "age": {
            "years": age_years,
            "months": age_months,
            "weeks" :age_weeks
        },
            "description": description,
            'cover_image': cover_image_url,
            "shelter_id": username,
            'status':'avaliable'
        }

        pets_collection.insert_one(pet_data)
        flash('Conference created successfully!', 'success')
        return redirect(url_for('shelter_dashboard'))
    

@app.route("/foster_update_pet/<petid>", methods=["GET", "POST"])
def foster_update_pet(petid):
    session_email = session["email"]
    user = Shelter_collection.find_one({'email': session_email, 'role': 'shelter'})
    shelter_id = user["name"]

    if request.method == "GET":
        # Fetch the existing pet details from the database
        pet = pets_collection.find_one({"_id": ObjectId(petid), "shelter_id": shelter_id})
        if not pet:
            flash('Pet not found!', 'error')
            return redirect(url_for('shelter_dashboard'))

        # Render the edit form with current pet details
        return render_template("foster_update_pet.html", pet=pet)

    elif request.method == "POST":
        # Update pet details based on form submission
        pet_name = request.form.get("pet_name")
        breed = request.form.get("breed")
        pet_type = request.form.get("type")
        age = request.form.get("age")
        description = request.form.get("description")

        # Prepare updated pet data
        updated_data = {
            "pet_name": pet_name,
            "breed": breed,
            "type": pet_type,
            "age": age,
            "description": description,
            "shelter_id": shelter_id,
            'status': 'available'  
        }

        # Perform the update operation in the database
        result = pets_collection.update_one({"_id": ObjectId(petid)}, {"$set": updated_data})

        if result.modified_count > 0:
            flash('Pet updated successfully!', 'success')
        else:
            flash('Failed to update pet. Please try again.', 'error')

        return redirect(url_for('shelter_dashboard'))

@app.route("/view_pets")
def view_pets():
    role=session['role']
    if role=='shelter':
        session_email=session["email"]
        user = Shelter_collection.find_one({'email': session_email, 'role': 'shelter'})
        username=user["name"]
        #uncomment below line 

        pets=pets_collection.find({ 'shelter_id': username})
        #pets = pets_collection.find({'shelter_id': username, 'status': {'$ne': 'Adopted'}})
    elif role=='member':
        pets = pets_collection.find({'shelter_id': username, 'status': {'$ne': 'Adopted'}})
    else:
        pets = pets_collection.find()

    return render_template("view_pets_admin.html",role=role, pets=pets)

@app.route("/user_view_pets")
def user_view_pets():

    # Retrieve all pets from the collection
    pets = pets_collection.find({'status': {'$ne': 'Adopted'}})
    return render_template("user_view_pets.html", pets=pets)


@app.route("/adopt", methods=["GET", "POST"])
def adopt_pet():
    pet_id = request.form.get("pet_id")
    print(pet_id)
    pet = pets_collection.find_one({"_id": ObjectId(pet_id)})
    return render_template("adoption_from.html", pet=pet)





@app.route("/adopt_submission", methods=["GET", "POST"])
def adopt_submission():
    session_email=session["email"]
    user = users_collection.find_one({'email': session_email, 'role': 'member'})
    username=user["name"]
    pet_id = request.form.get("pet_id")
    name = request.form.get("name")
    contact_number = request.form.get("contact_number")
    email = request.form.get("email")
    reason = request.form.get("reason")
    adoption_data = {
            "pet_id": pet_id,
            "adopter_name": name,
            "contact_number": contact_number,
            "email": email,
            'user':username,
            "reason":reason,
            "adoption_status": "Pending",  # Placeholder status
        }
    adoptions_collection.insert_one(adoption_data)
    return redirect(url_for("user_dashboard")) 


@app.route('/view_adoptions', methods=['GET'])
def view_adoptions():
    session_email=session["email"]
    role=session['role']
    user = Shelter_collection.find_one({'email': session_email, 'role': 'shelter'})
    sheltername=user["name"]
    pet_details = []
    adoptions=adoptions_collection.find()
    for adoption in adoptions:
        pet_id = adoption['pet_id']
        pet = pets_collection.find_one({'_id': ObjectId(pet_id), 'shelter_id': sheltername})
        if pet:
            pet_detail = {
                'pet_id': str(pet['_id']),
                'pet_name': pet['pet_name'],
                'breed': pet['breed'],
                'type': pet['type'],
                'age': pet['age'],
                'reason':adoption['reason'],
                'description': pet['description'],
                'cover_image': pet['cover_image'],
                'shelter_id': pet['shelter_id'],
                'adoption_id': adoption['_id'],
                'adopter_name': adoption['adopter_name'],
                'contact_number': adoption['contact_number'],
                'email': adoption['email'],
                'adoption_status': adoption['adoption_status']
            }
            pet_details.append(pet_detail)
    return render_template("view_adoptions.html", pet_details=pet_details,role=role)


@app.route('/user_view_adoptions', methods=['GET'])
def user_view_adoptions():
    session_email=session["email"]
    user = users_collection.find_one({'email': session_email, 'role': 'member'})
    username=user["name"]
    
    pet_details = []
    adoptions=adoptions_collection.find({ 'user': username})
    print(username)
    for adoption in adoptions:
        pet_id = adoption['pet_id']
        pet = pets_collection.find_one({'_id': ObjectId(pet_id)})
        if pet:
            pet_detail = {
                'pet_id': str(pet['_id']),
                'pet_name': pet['pet_name'],
                'breed': pet['breed'],
                'type': pet['type'],
                'age': pet['age'],
                'description': pet['description'],
                'cover_image': pet['cover_image'],
                'shelter_id': pet['shelter_id'],
                'adoption_id': adoption['_id'],
                'adopter_name': adoption['adopter_name'],
                'contact_number': adoption['contact_number'],
                'email': adoption['email'],
                'adoption_status': adoption['adoption_status']
            }
            pet_details.append(pet_detail)



    return render_template("user_adoptions.html", pet_details=pet_details)


@app.route('/admin_view_adoptions', methods=['GET'])
def admin_view_adoptions():
    role=session['role']

    
    pet_details = []
    adoptions=adoptions_collection.find()
    for adoption in adoptions:
        pet_id = adoption['pet_id']
        pet = pets_collection.find_one({'_id': ObjectId(pet_id)})
        if pet:
            pet_detail = {
                'pet_id': str(pet['_id']),
                'pet_name': pet['pet_name'],
                'breed': pet['breed'],
                'type': pet['type'],
                'age': pet['age'],
                'description': pet['description'],
                'cover_image': pet['cover_image'],
                'shelter_id': pet['shelter_id'],
                'adoption_id': adoption['_id'],
                'adopter_name': adoption['adopter_name'],
                'contact_number': adoption['contact_number'],
                'email': adoption['email'],
                'adoption_status': adoption['adoption_status']
            }
            pet_details.append(pet_detail)



    return render_template("view_adoptions.html", pet_details=pet_details,role=role)





@app.route('/update_status/<adoption_id>', methods=['POST'])
def update_status(adoption_id):
    role=session['role']
    new_status = request.form['status']
    print(adoption_id)
    print(new_status)
    adoptions_collection.update_one({'_id': ObjectId(adoption_id)}, {'$set': {'adoption_status': new_status}})
    adoption = adoptions_collection.find_one({'_id': ObjectId(adoption_id)})
    pet_id = adoption.get('pet_id')
    print(pet_id)
    pets_collection.update_one({'_id': ObjectId(pet_id)}, {'$set': {'status': new_status}})


    if role=='admin':
        return redirect(url_for('admin_view_adoptions'))

    return redirect(url_for('view_adoptions'))

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to the login page or another page after logout
    return redirect(url_for('login'))


@app.route('/delete_adoption/<adoption_id>', methods=['POST', 'DELETE'])
def delete_adoption(adoption_id):
    print(adoption_id)
    role=session['role']
    adoptions_collection.delete_one({'_id': ObjectId(adoption_id)})
    if role=='admin':
        return redirect(url_for('admin_view_adoptions'))

    return redirect(url_for('view_adoptions'))

@app.route('/view_shelters')
def view_shelters():
    shelters = list(Shelter_collection.find())
    return render_template('approve_shelters.html', shelters=shelters)
@app.route('/approve_shelter/<shelter_id>')
def approve_shelter(shelter_id):
    print(shelter_id)
    Shelter_collection.update_one({'_id': ObjectId(shelter_id)}, {'$set': {'status': 'approved'}})
    return redirect(url_for('view_shelters'))

@app.route('/disapprove_shelter/<shelter_id>')
def disapprove_shelter(shelter_id):
    print(shelter_id)
    Shelter_collection.update_one({'_id': ObjectId(shelter_id)}, {'$set': {'status': 'disapproved'}})
    return redirect(url_for('view_shelters'))



@app.route('/shelter_view_pets')
def shelter_view_pets():
    if 'email' in session:
        email = session['email']
        user = Shelter_collection.find_one({'email': email})
        if user and user['role'] == 'shelter':
            shelter_name = user['name']  # Assuming 'name' field holds shelter name
            pets = pets_collection.find({'shelter_id': shelter_name})
            return render_template('adoption_posts.html', pets=pets)
        else:
            flash('You are not authorized to view this page.', 'error')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))




@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if request.method == 'GET':
        post = pets_collection.find_one({'_id': ObjectId(post_id)})
        print(post)
        return render_template('edit_post.html', pet=post)
    elif request.method == 'POST':
        new_title = request.form.get('title')
        new_content = request.form.get('content')
        
        #posts[post_id]['title'] = new_title
        #posts[post_id]['content'] = new_content
        
        return f'Post {post_id} updated successfully'


@app.route('/delete_post/<post_id>', methods=['GET', 'POST'])
def delete_post(post_id):
    pets_collection.delete_one({"_id": ObjectId(post_id)})
    return redirect(url_for('shelter_view_pets'))


if __name__ == '__main__':
    app.run(debug=True)

#flask --app app.py --debug run