# Garcil-AI
Garcil-AI: An agentic RAG system that calculates skill gaps and dynamically generates stateful, interactive career roadmaps.

						Local Setup & Installation Instructions


Prerequisites:

    -Python 3.10 or higher installed on your system.
    -Git installed.


	
Step 1: Clone the Repository

Open your terminal (or command prompt) and run:

	-git clone [https://github.com/sam-2804/Garcil-AI.git](https://github.com/sam-2804/Garcil-AI.git)
	-cd Garcil-AI


	
Step 2: Create and Activate a Virtual Environment

It is recommended to isolate your project dependencies using a virtual environment:

Windows:

	-python -m venv .venv
    -.venv\Scripts\activate

macOS / Linux:

    -python3 -m venv .venv
    -source .venv/bin/activate



Step 3: Install Dependencies

Install all required libraries using the provided requirements.txt file:

	-pip install -r requirements.txt



Step 4: Configure Environment Variables

Create a .env file in the root directory of the project and add your API keys:

	-GEMINI_API_KEY=your_google_gemini_api_key_here
	-HF_TOKEN=your_huggingface_token_here



Step 5: Run the Streamlit Application

Launch the app locally:

	-streamlit run app.py