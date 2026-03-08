# Option Pricer
#### Video Demo:  https://youtu.be/r5IZPFZ_JyM
#### Description:

Hi! Welcome to Option Pricer. This is my final project for CS50. I wanted to build something that combines coding with my interest in finance, so I created a full-stack web application that calculates the price of stock options. 

The idea is simple: You type in a stock ticker (like AAPL or TSLA), a strike price, and the days left until the option expires. The app then automatically fetches real, current market data from Yahoo Finance and uses two famous methods (the Black-Scholes formula and a Monte Carlo simulation) to tell you what the option should theoretically cost.

### What's under the hood? (Tech Stack)

I split this project into a backend and a frontend to keep things organized:

* **Backend (Python & FastAPI):** I used Python for the heavy lifting. Instead of Flask, I went with FastAPI because it's faster and handles data validation really well. If a user tries to break the app (like entering -5 days or a fake ticker symbol), the Python code catches it and sends a clean error message back before the server crashes.
* **Frontend (HTML, Tailwind CSS, JS):** The user interface is built with plain HTML and JavaScript. I used Tailwind CSS via CDN because it makes styling super easy and modern without having to write hundreds of lines in a separate CSS file. I also used the Chart.js library to draw a cool graph of the simulated future stock prices.
* **Database (SQLite):** I wanted users to be able to see their past calculations. Since SQLite is built right into Python, it was the perfect choice. Every time you calculate an option, it saves the results, which you can then view on the `/history` page.
* **Docker:** To make sure this app runs perfectly on any machine without dependency headaches, I containerized the entire project using Docker.

The App requires the user to input the stock symbol, the intended strike price and the remaining time in days. It will then fetch relevant data from yahoo finance using the yfinance library and plug it into the Black-Scholes equation. It will then run a Monte Carlo simulation 10000 times. This simulation is recorded in an array containing 10000 rows, each of which is made up one column tracking each day. 
The API then returns some values, as well as 50 rows of the Monte Carlo array, which Chart.js uses to draw the graph.

### Files in this Project

* `main.py`: This is the core of the app. It handles the web routes, talks to the Yahoo Finance API, does all the math, and saves stuff to the database.
* `templates/index.html`: The main calculator page with the form and the JavaScript that makes the "Calculate" button work without reloading the page.
* `templates/history.html`: The page that displays the SQLite database records in a nice HTML table using Jinja2.
* `requirements.txt`: A list of the Python packages needed to run this project.
* `Dockerfile` & `.dockerignore`: The blueprints to build and run the isolated container.

### How to Run It

There are two options to run this project:

**Option 1: The Docker Way (Recommended)**
1. Make sure Docker Desktop is installed and running on your machine.
2. Open your terminal in the project folder.
3. Build the image: `docker build -t option-pricer .`
4. Run the container: `docker run -d -p 8000:8000 --name my-pricer option-pricer`
5. Open your browser and go to `http://localhost:8000`.

**Option 2: The Standard Python Way**
1. Make sure you have Python installed.
2. Open your terminal in the project folder.
3. Run `pip install -r requirements.txt` to get all the needed packages.
4. Start the server by typing `uvicorn main:app --reload`.
5. Open your browser and go to `http://localhost:8000`.