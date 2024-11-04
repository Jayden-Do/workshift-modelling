# Modelling Shift Management System

The Shift Management System is a web application designed to streamline shift scheduling and tracking for small to medium-sized food and beverage businesses. It offers features for both employees and managers to efficiently manage shifts, view assignments, and track worked hours.

## MongoDB Data Modeling
This project focuses on MongoDB data modeling, which includes:

- Identifying Data Workloads: Analyzing and understanding the data usage patterns to optimize performance.
- Modeling Data Relationships: Structuring data in a way that accurately represents relationships between different entities.
- Applying Schema Design Patterns: Implementing best practices for schema design to enhance data integrity and query performance.


## Installation

To set up the project locally, follow these steps:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/YourUsername/shift-management-system.git
   cd shift-management-system
   ```
2. **Set Up a Virtual Environment**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`
   ```
3. **Install Required Libraries**
   
   *Make sure you have the requirements.txt file in your project directory, then run*:
   ```bash
   python -m pip install requirement.txt
   ```
5. **Create a .env File**
   
   *Create a .env file in the root directory and add your environment variables as needed.*
   ```bash
   MONGO_URI="your_mongodb_uri"
   SECRET_KEY="your_secret_key" # can be created using `openssl rand -hex 32`, used for generating JWT tokens
   ALGORITHM="HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```
7. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

   
# FASTAPI First Touch & Contributing
This project marks my first dive into FastAPI, created for study purposes. Your feedback and suggestions on my code would be greatly appreciated, as they will help me grow and improve. If you'd like to contribute, feel free to fork the repository and submit a pull request. Thank you for your support! 😁
