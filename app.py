import os
import certifi
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from pymongo import MongoClient, ReturnDocument
from bson import ObjectId
from bson.errors import InvalidId

app = Flask(__name__)
CORS(app)

# Connection string using Environment Variable for safety
URI = os.getenv("MONGO_URI", "mongodb+srv://syedebtisamali:SEAPASS@sea-db.2biflg3.mongodb.net/?appName=SEA-DB")

client = MongoClient(URI)
db = client.get_database("BookStore")
books_collection = db.Books

def serialize_doc(doc):
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Bookstore API is live!"}), 200

@app.route("/books", methods=["GET"])
def get_books():
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = max(1, int(request.args.get("limit", 10)))
        skip = (page - 1) * limit
        
        cursor = books_collection.find().skip(skip).limit(limit)
        books_list = [serialize_doc(doc) for doc in cursor]
        total_count = books_collection.count_documents({})
        
        return jsonify({
            "page": page,
            "limit": limit,
            "total_books": total_count,
            "total_pages": (total_count + limit - 1) // limit if limit > 0 else 0,
            "data": books_list
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/books/<book_id>", methods=["GET"])
def get_book_by_id(book_id):
    try:
        book = books_collection.find_one({"_id": ObjectId(book_id)})
        if not book:
            return jsonify({"error": "Book not found"}), 404
        return jsonify(serialize_doc(book)), 200
    except InvalidId:
        return jsonify({"error": "Invalid book ID format"}), 400

@app.route("/books", methods=["POST"])
def create_book():
    book_data = request.get_json()
    if not book_data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    result = books_collection.insert_one(book_data)
    new_book = books_collection.find_one({"_id": result.inserted_id})
    return jsonify(serialize_doc(new_book)), 201

@app.route("/books/<book_id>", methods=["PUT"])
def update_book(book_id):
    update_data = request.get_json()
    if not update_data:
        return jsonify({"error": "No update fields provided"}), 400
        
    try:
        updated_doc = books_collection.find_one_and_update(
            {"_id": ObjectId(book_id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        if not updated_doc:
            return jsonify({"error": "Book not found"}), 404
        return jsonify(serialize_doc(updated_doc)), 200
    except InvalidId:
        return jsonify({"error": "Invalid book ID format"}), 400

@app.route("/books/<book_id>", methods=["DELETE"])
def delete_book(book_id):
    try:
        result = books_collection.delete_one({"_id": ObjectId(book_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Book not found"}), 404
        return jsonify({"message": f"Book {book_id} deleted"}), 200
    except InvalidId:
        return jsonify({"error": "Invalid book ID format"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
