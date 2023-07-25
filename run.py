from app import app
'''
MAIN FUNCTION
    The main function to run the User Interface. Just run 'python run.py'.
'''

# Set the port here and on config.js
if __name__ == "__main__":
    app.run(port=5001, debug=True)
