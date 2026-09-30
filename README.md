# RetinaStage Showcase

A separate presentation site for the **fresh final Colab coursework notebook**. The saved P2 EfficientNetB0 model provides the five grade estimates. The site adds exploratory review signals, Grad-CAM attention, a fixed blur check, and a deterministic RetinaGuide explanation panel. It does not use the older RetinaStage repository's model or policy.

## Start locally

1. Export the **same** `selected_fine_model.keras` and `temperature_calibration.json` generated in the final notebook. Place them at `models/selected_fine_model.keras` and `models/temperature_calibration.json`. The API verifies the checkpoint SHA-256 against the calibration record and checks that the recorded preprocessing is P2. These files are excluded from Git.
2. Use Python 3.11 or 3.12, then run from the repository root:

   ```bash
   python3 -m venv server/.venv
   server/.venv/bin/pip install -r server/requirements.txt
   server/.venv/bin/uvicorn app:app --app-dir server --host 127.0.0.1 --port 8000
   ```

3. In another terminal:

   ```bash
   cd web
   npm install
   npm run dev
   ```

4. Open `http://localhost:5173`. The status banner explains missing model files. Analyze one fundus photograph, inspect the output, and ask RetinaGuide a question. Run `npm run build` to check the frontend and `python3 -m unittest discover -s server/tests -v` for the pure response logic.

The notebook remains the source of the training, split, calibration, evaluation, and Criterion 9 validation evidence. This website is a companion prototype for demonstration and the required video recording. Do not present the site's one-image blur check or Grad-CAM overlay as clinical validation. The review threshold is an illustrative rule from the notebook's exploratory RetinaReview section, **not** a safety guarantee. The API holds only result summaries for 30 minutes in memory to answer questions; it does not save image files.

## Create a new GitHub repository

Unzip the source in a new folder. Run `git init -b main`, `git add .`, and `git commit -m "Build RetinaStage showcase"`. Create an **empty** GitHub repository named `RetinaStage-Showcase`, then set its URL with `git remote add origin https://github.com/YOUR_USERNAME/RetinaStage-Showcase.git` and run `git push -u origin main`. Check `git status --short` first. Never add `models/`, retinal images, your Kaggle token, or exported patient data.

## Prototype video sequence

Show the final Colab notebook's model/evaluation evidence, then the website's live analysis, five probabilities, review message, Grad-CAM, blur check, and chatbot limits. State that the example is research only and that the held-out test results come from the notebook, not from the website demo.
