import subprocess
import time


def manage_docker(action):
    if action == "start":
        print("Waking up Database")
        subprocess.run(["docker", "compose", "up", "-d"], check=True)
        time.sleep(2)
    elif action == "stop":
        print("Shutting down Database")
        subprocess.run(["docker", "compose", "stop"], check=True)


if __name__ == '__main__':
    api_process = None
    try:
        # 1. Wake up the DB
        manage_docker("start")

        print("Starting AI Engine")
        # 2. Launch FastAPI in the background
        api_process = subprocess.Popen(
            ["uvicorn", "main:app", "--port", "8000"])
        time.sleep(3)  # Give the API a moment to load the model into RAM

        print("Launching Dashboard")
        # 3. Launch Streamlit
        subprocess.run(["streamlit", "run", "app.py"])

    except KeyboardInterrupt:
        print("\nClosing application")
    finally:
        # 4. Cleanup when they close the app
        if api_process:
            print("Stopping AI Engine")
            api_process.terminate()
        manage_docker("stop")
        print("System safely shut down.")
