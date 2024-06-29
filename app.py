from pyngrok import conf, ngrok
import subprocess
import time

# Authenticate ngrok
conf.get_default().auth_token = "....................................................."

# Run the Streamlit app in the background
process = subprocess.Popen(['streamlit', 'run', 'app.py'])

# Give the Streamlit app a few seconds to start
time.sleep(5)

# Expose the Streamlit app to the web using ngrok
public_url = ngrok.connect(addr="8501")
print(f"Public URL: {public_url}")

# Keep the Colab cell running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping Streamlit app...")
    process.terminate()
    ngrok.disconnect(public_url)
    ngrok.kill()
